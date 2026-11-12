-- ==========================================
-- SEHAT Platform Schema & Seed SQL File
-- Compatible with PostgreSQL 12+
-- ==========================================

-- ------------------------------------------
-- 1. DROP TABLES IF EXISTS (Clean Slate)
-- ------------------------------------------
DROP TABLE IF EXISTS whatsapp_message_logs CASCADE;
DROP TABLE IF EXISTS blood_stocks CASCADE;
DROP TABLE IF EXISTS blood_banks CASCADE;
DROP TABLE IF EXISTS prescription_logs CASCADE;
DROP TABLE IF EXISTS queue_tokens CASCADE;
DROP TABLE IF EXISTS chemist_stock CASCADE;
DROP TABLE IF EXISTS medicines CASCADE;
DROP TABLE IF EXISTS chemists CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS admins CASCADE;

-- ------------------------------------------
-- 2. CREATE TABLE SCHEMAS
-- ------------------------------------------

-- Admins Table
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Patients Table
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    language_preference VARCHAR(5) DEFAULT 'en' NOT NULL,
    last_search_doctor_ids JSONB DEFAULT '[]'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Doctors Table
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    clinic_name VARCHAR(150) NOT NULL,
    address VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    is_available BOOLEAN DEFAULT TRUE NOT NULL,
    avg_consultation_minutes INTEGER DEFAULT 15 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Chemists Table
CREATE TABLE chemists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    shop_name VARCHAR(150) NOT NULL,
    address VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    is_open BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Medicines Table
CREATE TABLE medicines (
    id SERIAL PRIMARY KEY,
    generic_name VARCHAR(150) UNIQUE NOT NULL,
    brand_names JSONB DEFAULT '[]'::jsonb NOT NULL,
    category VARCHAR(100) NOT NULL,
    schedule VARCHAR(20) DEFAULT 'H' NOT NULL,
    standard_dosages JSONB DEFAULT '[]'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Chemist Stock Table
CREATE TABLE chemist_stock (
    id SERIAL PRIMARY KEY,
    chemist_id INTEGER REFERENCES chemists(id) ON DELETE CASCADE NOT NULL,
    medicine_id INTEGER REFERENCES medicines(id) ON DELETE CASCADE NOT NULL,
    is_available BOOLEAN DEFAULT TRUE NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_chemist_medicine_stock UNIQUE (chemist_id, medicine_id)
);

-- Queue Tokens Table
CREATE TABLE queue_tokens (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER REFERENCES doctors(id) ON DELETE CASCADE NOT NULL,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
    token_number INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting' NOT NULL, -- waiting, called, seen, cancelled
    booked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    called_at TIMESTAMP WITH TIME ZONE,
    seen_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE
);

-- Prescription Logs Table
CREATE TABLE prescription_logs (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
    ocr_confidence DOUBLE PRECISION NOT NULL,
    extracted_medicines JSONB NOT NULL,
    hindi_explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Blood Banks Table
CREATE TABLE blood_banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    is_open_24hrs BOOLEAN DEFAULT TRUE NOT NULL,
    opening_time VARCHAR(20),
    closing_time VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Blood Stocks Table
CREATE TABLE blood_stocks (
    id SERIAL PRIMARY KEY,
    blood_bank_id INTEGER REFERENCES blood_banks(id) ON DELETE CASCADE NOT NULL,
    blood_group VARCHAR(3) NOT NULL, -- A+, B+, O-, etc.
    units_available INTEGER DEFAULT 0 NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_bank_group UNIQUE (blood_bank_id, blood_group)
);

-- WhatsApp Message Logs Table (For Rate Limiting)
CREATE TABLE whatsapp_message_logs (
    id SERIAL PRIMARY KEY,
    patient_phone VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);


-- ------------------------------------------
-- 3. SEED BASELINE DATA
-- ------------------------------------------

-- 3.1 Seed Admin
-- Credentials -> admin@sehat.in / sehat2026
INSERT INTO admins (email, password_hash, name)
VALUES (
    'admin@sehat.in', 
    '$2b$12$QuD2PLdXJwskBgiecN6qE.q4ioUyHeDQCne18VWmnukiSbd3MPl02', 
    'System Admin'
);

-- 3.2 Seed 5 Patients
INSERT INTO patients (phone, name, language_preference)
VALUES 
('+919999999901', 'Mohan Singh', 'en'),
('+919999999902', 'Rajesh Kumar', 'en'),
('+919999999903', 'Priya Sharma', 'en'),
('+919999999904', 'Amit Patel', 'en'),
('+919999999905', 'Sunita Rani', 'en');

-- 3.3 Seed 5 Doctors
-- All password hashes decrypt to 'sehat123'
INSERT INTO doctors (name, specialization, phone, password_hash, clinic_name, address, latitude, longitude, is_available, avg_consultation_minutes)
VALUES 
('Sharma', 'General Physician', '+919999999999', '$2b$12$mC5BGaCqs2B5PBlBSbaCtOpOUxB2YG4U3.NIJWSQ0Gb4gVfd./qhe', 'Sharma Health Clinic', 'Sector 14, Vasundhara, Ghaziabad', 28.6612, 77.3584, TRUE, 15),
('Verma', 'Pediatrician', '+919999999991', '$2b$12$mC5BGaCqs2B5PBlBSbaCtOpOUxB2YG4U3.NIJWSQ0Gb4gVfd./qhe', 'Verma Care Clinic', 'Sector 12, Vasundhara, Ghaziabad', 28.6620, 77.3590, TRUE, 15),
('Gupta', 'Gynecologist', '+919999999992', '$2b$12$mC5BGaCqs2B5PBlBSbaCtOpOUxB2YG4U3.NIJWSQ0Gb4gVfd./qhe', 'Gupta Women Clinic', 'Sector 10, Vasundhara, Ghaziabad', 28.6640, 77.3610, TRUE, 15),
('Patel', 'Cardiologist', '+919999999993', '$2b$12$mC5BGaCqs2B5PBlBSbaCtOpOUxB2YG4U3.NIJWSQ0Gb4gVfd./qhe', 'Patel Heart Center', 'Indirapuram, Ghaziabad', 28.6680, 77.3630, TRUE, 15),
('Singh', 'Dermatologist', '+919999999994', '$2b$12$mC5BGaCqs2B5PBlBSbaCtOpOUxB2YG4U3.NIJWSQ0Gb4gVfd./qhe', 'Singh Skin Clinic', 'Vasundhara, Ghaziabad', 28.6590, 77.3560, TRUE, 15);

-- 3.4 Seed 5 Chemists
-- All password hashes decrypt to 'sehat123'
INSERT INTO chemists (name, phone, password_hash, shop_name, address, latitude, longitude, is_open)
VALUES 
('Mohan Kumar', '+918888888888', '$2b$12$Bb1hKx4tFBz0uPIq/J072euGhYXRy3cOaI7bVSDKDSF4/QHzTM18S', 'Mohan Chemists', 'Shop 4, Vasundhara, Ghaziabad', 28.6625, 77.3595, TRUE),
('Gupta Owner', '+918888888881', '$2b$12$Bb1hKx4tFBz0uPIq/J072euGhYXRy3cOaI7bVSDKDSF4/QHzTM18S', 'Gupta Pharmacy', 'Sector 12, Vasundhara, Ghaziabad', 28.6635, 77.3605, TRUE),
('City Owner', '+918888888882', '$2b$12$Bb1hKx4tFBz0uPIq/J072euGhYXRy3cOaI7bVSDKDSF4/QHzTM18S', 'City Medicos', 'Indirapuram, Ghaziabad', 28.6600, 77.3570, TRUE),
('Apex Owner', '+918888888883', '$2b$12$Bb1hKx4tFBz0uPIq/J072euGhYXRy3cOaI7bVSDKDSF4/QHzTM18S', 'Apex Pharma', 'Sector 15, Vasundhara, Ghaziabad', 28.6660, 77.3620, TRUE),
('Krishna Owner', '+918888888884', '$2b$12$Bb1hKx4tFBz0uPIq/J072euGhYXRy3cOaI7bVSDKDSF4/QHzTM18S', 'Krishna Medicos', 'Vasundhara, Ghaziabad', 28.6580, 77.3550, TRUE);

-- 3.5 Seed Medicines Catalog
INSERT INTO medicines (generic_name, brand_names, category, schedule, standard_dosages)
VALUES 
('Paracetamol', '["Crocin", "Calpol", "Dolo 500"]'::jsonb, 'Analgesic', 'H', '["500mg", "650mg"]'::jsonb),
('Amoxicillin', '["Novamox", "Mox", "Amoxil"]'::jsonb, 'Antibiotic', 'H', '["250mg", "500mg"]'::jsonb),
('Metformin', '["Glycomet", "Obimet", "Gluformin"]'::jsonb, 'Antidiabetic', 'H', '["500mg", "850mg"]'::jsonb),
('Atorvastatin', '["Lipvas", "Atorva", "Lipitor"]'::jsonb, 'Statins', 'H', '["10mg", "20mg"]'::jsonb),
('Ibuprofen', '["Brufen", "Ibugesic"]'::jsonb, 'NSAID', 'H', '["400mg"]'::jsonb),
('Amlodipine', '["Amlopin", "Amlodac"]'::jsonb, 'Antihypertensive', 'H', '["5mg"]'::jsonb),
('Ferrous Sulfate', '["FeSO4", "Autrin", "Orofer", "Fefol", "Iron", "Imeron"]'::jsonb, 'Hematinic', 'H', '["200mg"]'::jsonb),
('Ascorbic Acid', '["Vitamin C", "Limcee", "Celin", "Suckcee", "Ascorbic Acid"]'::jsonb, 'Vitamin', 'OTC', '["100mg", "500mg"]'::jsonb);

-- 3.6 Seed Chemist Stock Levels
INSERT INTO chemist_stock (chemist_id, medicine_id, is_available, last_updated)
VALUES 
(1, 1, TRUE, CURRENT_TIMESTAMP), -- Mohan Chemists has Paracetamol
(1, 3, TRUE, CURRENT_TIMESTAMP), -- Mohan Chemists has Metformin
(1, 5, TRUE, CURRENT_TIMESTAMP), -- Mohan Chemists has Ibuprofen
(1, 7, TRUE, CURRENT_TIMESTAMP), -- Mohan Chemists has Ferrous Sulfate
(1, 8, TRUE, CURRENT_TIMESTAMP), -- Mohan Chemists has Ascorbic Acid
(2, 2, TRUE, CURRENT_TIMESTAMP), -- Gupta Pharmacy has Amoxicillin
(2, 4, TRUE, CURRENT_TIMESTAMP), -- Gupta Pharmacy has Atorvastatin
(4, 7, TRUE, CURRENT_TIMESTAMP), -- Apex Pharma has Ferrous Sulfate
(4, 8, TRUE, CURRENT_TIMESTAMP); -- Apex Pharma has Ascorbic Acid

-- 3.7 Seed 5 Blood Banks
-- All password hashes decrypt to 'sehat123'
INSERT INTO blood_banks (name, address, phone, password_hash, latitude, longitude, is_open_24hrs)
VALUES 
('City Blood Bank', '10, Indirapuram, Ghaziabad', '+917777777777', '$2b$12$Dz4.ku9x0fOnLrcnOLXkROkOIHO1Ygmz/6ZqgzhRCuPZwugazM7pG', 28.6610, 77.3580, TRUE),
('Red Cross Blood Centre', 'Sector 12, Vasundhara, Ghaziabad', '+917777777771', '$2b$12$Dz4.ku9x0fOnLrcnOLXkROkOIHO1Ygmz/6ZqgzhRCuPZwugazM7pG', 28.6650, 77.3600, TRUE),
('Metro Blood Bank', 'Indirapuram, Ghaziabad', '+917777777772', '$2b$12$Dz4.ku9x0fOnLrcnOLXkROkOIHO1Ygmz/6ZqgzhRCuPZwugazM7pG', 28.6585, 77.3565, TRUE),
('Lifeline Blood Services', 'Sector 15, Vasundhara, Ghaziabad', '+917777777773', '$2b$12$Dz4.ku9x0fOnLrcnOLXkROkOIHO1Ygmz/6ZqgzhRCuPZwugazM7pG', 28.6700, 77.3650, TRUE),
('Apex Blood Care', 'Sector 6, Vasundhara, Ghaziabad', '+917777777774', '$2b$12$Dz4.ku9x0fOnLrcnOLXkROkOIHO1Ygmz/6ZqgzhRCuPZwugazM7pG', 28.6520, 77.3500, TRUE);

-- 3.8 Seed Blood Bank Stock Levels
-- Seed 4 groups (A+, B+, O-, AB+) for each blood bank
INSERT INTO blood_stocks (blood_bank_id, blood_group, units_available, last_updated)
VALUES 
(1, 'B+', 10, CURRENT_TIMESTAMP), (1, 'O-', 2, CURRENT_TIMESTAMP), (1, 'AB+', 4, CURRENT_TIMESTAMP), (1, 'A+', 5, CURRENT_TIMESTAMP),
(2, 'B+', 4, CURRENT_TIMESTAMP),  (2, 'O-', 6, CURRENT_TIMESTAMP), (2, 'AB+', 8, CURRENT_TIMESTAMP), (2, 'A+', 3, CURRENT_TIMESTAMP),
(3, 'B+', 6, CURRENT_TIMESTAMP),  (3, 'O-', 2, CURRENT_TIMESTAMP), (3, 'AB+', 5, CURRENT_TIMESTAMP), (3, 'A+', 4, CURRENT_TIMESTAMP),
(4, 'B+', 8, CURRENT_TIMESTAMP),  (4, 'O-', 4, CURRENT_TIMESTAMP), (4, 'AB+', 2, CURRENT_TIMESTAMP), (4, 'A+', 6, CURRENT_TIMESTAMP),
(5, 'B+', 2, CURRENT_TIMESTAMP),  (5, 'O-', 8, CURRENT_TIMESTAMP), (5, 'AB+', 6, CURRENT_TIMESTAMP), (5, 'A+', 7, CURRENT_TIMESTAMP);

-- 3.9 Seed Queue Tokens
INSERT INTO queue_tokens (doctor_id, patient_phone, patient_name, token_number, position, status, estimated_wait_minutes, booked_at)
VALUES 
(1, '+919999999901', 'Mohan Singh', 1, 1, 'waiting', 15, CURRENT_TIMESTAMP),
(1, '+919999999902', 'Rajesh Kumar', 2, 2, 'waiting', 30, CURRENT_TIMESTAMP),
(1, '+919999999903', 'Priya Sharma', 3, 3, 'called', 0, CURRENT_TIMESTAMP),
(2, '+919999999904', 'Amit Patel', 1, 1, 'waiting', 15, CURRENT_TIMESTAMP),
(2, '+919999999905', 'Sunita Rani', 2, 2, 'seen', 0, CURRENT_TIMESTAMP);

-- 3.10 Seed Prescription Logs
INSERT INTO prescription_logs (patient_phone, image_url, extracted_medicines, matched_chemist_id, hindi_explanation, ocr_confidence)
VALUES 
('+919999999901', 'https://example.com/rx1.jpg', '{"medicines": [{"name": "Paracetamol", "dosage": "500mg", "frequency": "twice a day"}]}'::jsonb, 1, 'पैरासिटामोल 500mg - दिन में दो बार (दर्द और बुखार के लिए)', 0.95),
('+919999999902', 'https://example.com/rx2.jpg', '{"medicines": [{"name": "Amoxicillin", "dosage": "250mg", "frequency": "thrice a day"}]}'::jsonb, 2, 'एमोक्सिसिलिन 250mg - दिन में तीन बार (बैक्टीरियल इन्फेक्शन के लिए)', 0.88);
