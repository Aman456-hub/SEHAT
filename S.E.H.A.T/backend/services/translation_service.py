import os
import logging
import asyncio
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

import google.generativeai as genai

logger = logging.getLogger("translation_service")

# Configure Gemini if key is provided
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key, transport="rest")
    logger.info("Gemini Generative AI client configured successfully for translation.")
else:
    logger.warning("GEMINI_API_KEY not found in environment at startup. Translation service running in Mock Mode.")

async def explain_in_hindi(medicine_list: list) -> str:
    """
    Generate patient-friendly conversational Hindi explanations for a list of medicines.
    Every service function must have a docstring.
    All Gemini API calls must have try/except with a graceful fallback.
    """
    current_key = os.getenv("GEMINI_API_KEY") or api_key
    if not current_key:
        logger.info("Mock Mode: Simulating prescription Hindi translation.")
        return get_mock_hindi_explanation(medicine_list)

    try:
        genai.configure(api_key=current_key, transport="rest")
        prompt = f"""
You are explaining medicines to a patient in simple Hindi.
The patient has low health literacy. Use conversational language only.
No English medical terms. No jargon.

For each medicine explain:
- यह दवाई किसलिए है
- कब लेनी है (खाने से पहले / बाद / खाली पेट)
- दिन में कितनी बार
- कितने दिन तक
- एक जरूरी बात (if any)

Medicine list: {medicine_list}

Return plain text only. No JSON. No markdown.
Use → for each point. Keep each medicine under 5 lines.
"""
        model = genai.GenerativeModel("gemini-3.6-flash")
        
        # Execute model content generation in threadpool to prevent async event-loop blocking
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )
        
        return response.text.strip()

    except Exception as e:
        logger.error(f"Gemini Hindi explanation failed with exception: {str(e)}. Triggering mock fallback.")
        return get_mock_hindi_explanation(medicine_list)

def get_mock_hindi_explanation(medicine_list: list) -> str:
    """
    Produce mock conversational Hindi instructions for standard medications.
    """
    explanations = []
    for med in medicine_list:
        name = med.get("name", "Medicine")
        dosage = med.get("dosage", "")
        freq = med.get("frequency", "")
        dur = med.get("duration", "")
        
        # Format simple, rule-based Hindi translations based on standard medicine names
        if "paracetamol" in name.lower() or "crocin" in name.lower() or "dolo" in name.lower():
            explanations.append(
                f"💊 *Paracetamol 500mg*:\n"
                f"→ यह दवाई बुखार और बदन दर्द को कम करने के लिए है।\n"
                f"→ इसे खाना खाने के बाद ही लेना चाहिए।\n"
                f"→ दिन में 3 बार (सुबह, दोपहर, रात) लें।\n"
                f"→ सिर्फ 3 दिन तक ही लें।\n"
                f"→ जरूरी बात: खाली पेट लेने से पेट में जलन हो सकती है।"
            )
        elif "cetirizine" in name.lower() or "alerid" in name.lower():
            explanations.append(
                f"💊 *Cetirizine 10mg*:\n"
                f"→ यह दवाई सर्दी, जुकाम और एलर्जी (खुजली) को ठीक करने के लिए है।\n"
                f"→ इसे रात को सोने से पहले लें।\n"
                f"→ दिन में केवल 1 बार (रात को) लें।\n"
                f"→ 5 दिन तक लें।\n"
                f"→ जरूरी बात: यह दवाई लेने के बाद गाड़ी न चलाएं क्योंकि इससे नींद आती है।"
            )
        else:
            explanations.append(
                f"💊 *{name}*:\n"
                f"→ यह दवाई डॉक्टर की सलाह के अनुसार बीमारी को ठीक करने के लिए है।\n"
                f"→ इसे खाना खाने के बाद पानी के साथ लें।\n"
                f"→ दिन में {freq or '2 बार'} लें।\n"
                f"→ {dur or '5 दिन'} तक लें।\n"
                f"→ जरूरी बात: कोई भी खुराक छोड़ें नहीं।"
            )
            
    return "\n\n".join(explanations)
