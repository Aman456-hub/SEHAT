# SEHAT Platform — Chatbot Output Samples

This document contains actual output message templates sent by the SEHAT WhatsApp chatbot to patients in semi-urban India.

---

## 🩺 FLOW 1: Doctor Booking

### 1. Available Doctors List (English)
*Sent when a patient drops their location pin or sends `DOCTOR` near Vasundhara, Ghaziabad:*
```text
🩺 Available Doctors Near You:

1. *Dr. Sharma* - General Physician
   Clinic: Sharma Health Clinic (0.4 km away)
   Status: AVAILABLE (Wait List: 3 patients)
   Estimated Wait: 36 mins
   To Book: Reply with 'BOOK 1'

2. *Dr. Verma* - Pediatrician
   Clinic: Verma Care Clinic (2.1 km away)
   Status: AVAILABLE (Wait List: 0 patients)
   Estimated Wait: 0 mins
   To Book: Reply with 'BOOK 2'
```

### 2. Available Doctors List (Hindi)
*Sent if the patient replies in Hindi or uses Devanagari script:*
```text
🩺 आपके पास उपलब्ध डॉक्टर:

1. *Dr. Sharma* - सामान्य चिकित्सक
   क्लिनिक: Sharma Health Clinic (0.4 किमी दूर)
   स्थिति: उपलब्ध (प्रतीक्षा सूची: 3 मरीज)
   अनुमानित समय: ३६ मिनट
   बुक करने के लिए: 'BOOK 1' लिखकर भेजें
```

### 3. Token Booking Confirmation
*Sent immediately after patient replies `BOOK 1`:*
```text
✅ Booking Confirmed!

Token Number: #SH-12
Patient Name: Mohan Singh
Doctor: Dr. Sharma (Sharma Health Clinic)
Estimated Wait: ~36 mins

⚠️ Please arrive at the clinic within 30 minutes of being called, or your token will be auto-cancelled.
```

---

## 💊 FLOW 2: Prescription Scanning & Hindi Explanations

### 1. Stock Matched at Single Chemist (English)
*Sent after patient uploads a prescription photo and all items exist at Mohan Chemists:*
```text
💊 All prescribed medicines are available at a nearby pharmacy!

📍 *Mohan Chemists* - Shop No. 4, Vasundhara, Ghaziabad (0.5 km away)
   Status: OPEN  |  Contact: +918888888888
   
Matched Items:
- Paracetamol 500mg
- Metformin 500mg

📝 Reply with 'EXPLAIN' to get instructions for these medicines in plain Hindi.
```

### 2. Split Stock Matched (Combination of 2 Chemists)
*Sent if no single pharmacy carries all items, but a combination of two nearby shops covers the list:*
```text
💊 Some medicines are out of stock in individual shops. We found a nearby combination to complete your prescription:

1. *Mohan Chemists* - Shop No. 4, Vasundhara (0.5 km)
   - Paracetamol 500mg (Available)
   - Metformin 500mg (Available)

2. *Gupta Pharmacy* - Sector 12, Vasundhara (1.2 km)
   - Amoxicillin 250mg (Available)

📝 Reply with 'EXPLAIN' to get instructions for these medicines in plain Hindi.
```

### 3. Inventory Unverified Flag (Rule 3)
*Sent if a chemist has not updated their stock list within the last 24 hours:*
```text
💊 Matched Pharmacy:

📍 *Mohan Chemists* - Shop No. 4, Vasundhara, Ghaziabad (0.5 km away)
   ⚠️ Inventory Unverified (Last updated 28 hours ago)
   We recommend calling before visiting: +918888888888
```

### 4. Hindi Conversational Explanation (`EXPLAIN`)
*Sent after patient replies `EXPLAIN` to understand their prescription instructions:*
```text
📋 आपकी दवाइयों की जानकारी (Hindi Explanation):

1. *Paracetamol 500mg* (बुखार और दर्द के लिए)
   - *कैसे लें:* 1 गोली दिन में दो बार, खाना खाने के बाद।
   - *जरूरी सलाह:* खाली पेट न लें। यदि आराम न मिले तो डॉक्टर से संपर्क करें।

2. *Metformin 500mg* (शुगर नियंत्रित करने के लिए)
   - *कैसे लें:* 1 गोली रोज सुबह नाश्ते के साथ या तुरंत बाद।
   - *जरूरी सलाह:* डॉक्टर की सलाह के बिना बंद न करें।
```

---

## 🩸 FLOW 3: Blood Group Queries

### 1. Blood Stock Search Output (English)
*Sent when a patient queries `BLOOD B+` or `b positive`:*
```text
🩸 B+ Blood Available Near You:

1. *City Blood Bank* - 10, Indirapuram, Ghaziabad (0.0 km away)
   Units: 12  |  Contact: +917777777777
   Open: 24 hours
```

### 2. Blood Stock Search Output (Hindi)
*Sent when a patient queries `KHOON B+`:*
```text
🩸 आपके पास उपलब्ध B+ रक्त:

1. *City Blood Bank* - 10, Indirapuram, Ghaziabad (0.0 किमी दूर)
   मात्रा: 12 यूनिट  |  संपर्क: +917777777777
   समय: २४ घंटे खुला
```

### 3. Stock Staleness Warning (Rule 4)
*Sent if a blood bank has not updated units count in over 12 hours:*
```text
🩸 B+ Blood Available Near You:

1. *City Blood Bank* - 10, Indirapuram (0.0 km away)
   Units: 12 (⚠️ Unverified - Last updated 15 hours ago)
   Contact: +917777777777
```

---

## 🛡️ Message Rate Limiting (Rule 13)

### 1. English Limit Alert
*Sent if a caller exceeds 10 messages within any rolling 1-hour window:*
```text
⚠️ Rate limit exceeded. You can send a maximum of 10 messages per hour. Please try again later.
```

### 2. Hindi Limit Alert
```text
⚠️ आप एक घंटे में अधिकतम १० संदेश ही भेज सकते हैं। कृपया बाद में प्रयास करें।
```
