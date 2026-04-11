#!/usr/bin/env python3
"""Medigraph Dataset Generator - Optimized Version"""

import csv
import random
from pathlib import Path

random.seed(42)

# === DATA POOLS ===

DISEASE_CATEGORIES = [
    "Cardiovascular", "Respiratory", "Neurological", "Gastrointestinal",
    "Endocrine", "Infectious", "Oncological", "Musculoskeletal", "Dermatological",
    "Renal", "Hematological", "Immunological", "Ophthalmological", "Psychiatric",
    "Hepatobiliary", "Thyroid"
]

DISEASE_TEMPLATES = {
    "Cardiovascular": ["Hypertension", "Coronary Artery Disease", "Heart Failure", "Atrial Fibrillation",
        "Ventricular Tachycardia", "Bradycardia", "Cardiomyopathy", "Pericarditis",
        "Aortic Stenosis", "Mitral Regurgitation", "Pulmonary Embolism", "Deep Vein Thrombosis",
        "Peripheral Artery Disease", "Aortic Aneurysm", "Pulmonary Hypertension"],
    "Respiratory": ["Asthma", "COPD", "Pneumonia", "Bronchitis", "Pulmonary Fibrosis",
        "Sarcoidosis", "Tuberculosis", "Lung Cancer", "Mesothelioma", "Pleurisy",
        "Pneumothorax", "ARDS", "Sleep Apnea", "Cystic Fibrosis", "Bronchiectasis"],
    "Neurological": ["Epilepsy", "Parkinson's Disease", "Alzheimer's Disease", "Multiple Sclerosis",
        "Migraine", "Stroke", "Meningitis", "Encephalitis", "Huntington's Disease",
        "ALS", "Guillain-Barre Syndrome", "Myasthenia Gravis", "Neuropathy", "Sciatica"],
    "Gastrointestinal": ["GERD", "Peptic Ulcer", "Gastritis", "Crohn's Disease", "Ulcerative Colitis",
        "Irritable Bowel Syndrome", "Celiac Disease", "Diverticulitis", "Appendicitis",
        "Pancreatitis", "Cholecystitis", "Gallstones", "Hepatitis", "Cirrhosis"],
    "Endocrine": ["Type 2 Diabetes", "Type 1 Diabetes", "Gestational Diabetes", "Hypothyroidism",
        "Hyperthyroidism", "Thyroid Nodules", "Goiter", "Addison's Disease",
        "Cushing's Syndrome", "PCOS", "Hyperparathyroidism", "Acromegaly"],
    "Infectious": ["HIV/AIDS", "Influenza", "COVID-19", "Hepatitis B", "Hepatitis C",
        "Malaria", "Dengue Fever", "Typhoid", "Cholera", "Tetanus",
        "Measles", "Rubella", "Mumps", "Chickenpox", "Sepsis"],
    "Oncological": ["Breast Cancer", "Lung Cancer", "Prostate Cancer", "Colorectal Cancer",
        "Pancreatic Cancer", "Liver Cancer", "Stomach Cancer", "Ovarian Cancer",
        "Cervical Cancer", "Kidney Cancer", "Bladder Cancer", "Thyroid Cancer"],
    "Musculoskeletal": ["Osteoarthritis", "Rheumatoid Arthritis", "Osteoporosis", "Fibromyalgia",
        "Gout", "Lupus", "Scleroderma", "Ankylosing Spondylitis",
        "Carpal Tunnel Syndrome", "Rotator Cuff Injury", "Herniated Disc"],
    "Dermatological": ["Psoriasis", "Eczema", "Acne", "Rosacea", "Vitiligo",
        "Urticaria", "Contact Dermatitis", "Seborrheic Dermatitis", "Alopecia Areata",
        "Lichen Planus", "Herpes Simplex", "Shingles", "Scabies"],
    "Renal": ["Chronic Kidney Disease", "Acute Kidney Injury", "Kidney Stones",
        "Glomerulonephritis", "Pyelonephritis", "Nephrotic Syndrome", "Polycystic Kidney Disease"],
    "Hematological": ["Anemia", "Sickle Cell Disease", "Thalassemia", "Hemophilia",
        "Von Willebrand Disease", "Polycythemia Vera", "Aplastic Anemia"],
    "Immunological": ["Rheumatoid Arthritis", "Systemic Lupus Erythematosus", "Scleroderma",
        "Sjogren's Syndrome", "Vasculitis", "Sarcoidosis", "Amyloidosis"],
    "Ophthalmological": ["Cataracts", "Glaucoma", "Macular Degeneration", "Diabetic Retinopathy",
        "Retinal Detachment", "Conjunctivitis", "Uveitis", "Optic Neuritis"],
    "Psychiatric": ["Major Depressive Disorder", "Generalized Anxiety Disorder", "Panic Disorder",
        "PTSD", "OCD", "Bipolar Disorder", "Schizophrenia",
        "Borderline Personality Disorder", "Anorexia Nervosa", "Bulimia", "ADHD", "Insomnia"],
    "Hepatobiliary": ["Hepatitis A", "Hepatitis B", "Hepatitis C", "Fatty Liver Disease",
        "Alcoholic Liver Disease", "Liver Cirrhosis", "Cholangitis", "Biliary Atresia"],
    "Thyroid": ["Hypothyroidism", "Hyperthyroidism", "Thyroiditis", "Thyroid Nodules",
        "Thyroid Cancer", "Graves' Disease", "Hashimoto's Thyroiditis"]
}

SYMPTOMS = [
    ("Chest Pain", "Cardiovascular"), ("Shortness of Breath", "Respiratory"), ("Palpitations", "Cardiovascular"),
    ("Fatigue", "General"), ("Dizziness", "Neurological"), ("Headache", "Neurological"),
    ("Cough", "Respiratory"), ("Wheezing", "Respiratory"), ("Fever", "Infectious"),
    ("Abdominal Pain", "Gastrointestinal"), ("Nausea", "Gastrointestinal"), ("Vomiting", "Gastrointestinal"),
    ("Diarrhea", "Gastrointestinal"), ("Constipation", "Gastrointestinal"), ("Joint Pain", "Musculoskeletal"),
    ("Muscle Weakness", "Musculoskeletal"), ("Rash", "Dermatological"), ("Itching", "Dermatological"),
    ("Weight Loss", "General"), ("Weight Gain", "Endocrine"), ("Increased Thirst", "Endocrine"),
    ("Frequent Urination", "Endocrine"), ("Night Sweats", "Infectious"), ("Chills", "Infectious"),
    ("Seizures", "Neurological"), ("Tremor", "Neurological"), ("Numbness", "Neurological"),
    ("Blurred Vision", "Ophthalmological"), ("Eye Pain", "Ophthalmological"), ("Edema", "Cardiovascular"),
    ("Syncope", "Cardiovascular"), ("Hematuria", "Renal"), ("Proteinuria", "Renal"),
    ("Jaundice", "Hepatobiliary"), ("Dark Urine", "Hepatobiliary"), ("Confusion", "Psychiatric"),
    ("Anxiety", "Psychiatric"), ("Low Mood", "Psychiatric"), ("Insomnia", "Psychiatric"),
    ("Back Pain", "Musculoskeletal"), ("Stiffness", "Musculoskeletal"), ("Swelling", "General"),
    ("Loss of Appetite", "General"), ("Blood in Stool", "Gastrointestinal"), ("Heartburn", "Gastrointestinal"),
    ("Shortness of Breath at Rest", "Respiratory"), ("Rapid Breathing", "Respiratory"),
    ("Chest Tightness", "Cardiovascular"), ("Irregular Heartbeat", "Cardiovascular")
]

DRUGS = [
    "Lisinopril", "Enalapril", "Losartan", "Valsartan", "Metoprolol", "Atenolol", "Amlodipine",
    "Atorvastatin", "Simvastatin", "Rosuvastatin", "Omeprazole", "Pantoprazole", "Esomeprazole",
    "Metformin", "Glipizide", "Insulin Glargine", "Levothyroxine", "Prednisone", "Dexamethasone",
    "Amoxicillin", "Azithromycin", "Ciprofloxacin", "Metronidazole", "Doxycycline", "Vancomycin",
    "Warfarin", "Rivaroxaban", "Apixaban", "Heparin", "Lisinopril", "Spironolactone", "Furosemide",
    "Hydrochlorothiazide", "Sertraline", "Fluoxetine", "Escitalopram", "Venlafaxine", "Bupropion",
    "Amitriptyline", "Risperidone", "Quetiapine", "Aripiprazole", "Olanzapine", "Alprazolam",
    "Lorazepam", "Diazepam", "Clonazepam", "Levetiracetam", "Valproic Acid", "Carbamazepine",
    "Lamotrigine", "Ibuprofen", "Naproxen", "Diclofenac", "Celecoxib", "Acetaminophen",
    "Oxycodone", "Hydrocodone", "Morphine", "Tramadol", "Gabapentin", "Pregabalin",
    "Albuterol", "Ipratropium", "Salmeterol", "Tiotropium", "Montelukast", "Cetirizine",
    "Loratadine", "Diphenhydramine", "Acyclovir", "Valacyclovir", "Oseltamivir",
    "Fluconazole", "Itraconazole", "Allopurinol", "Colchicine", "Alendronate", "Denosumab",
    "Ciprofloxacin", "Levofloxacin", "Methylphenidate", "Atomoxetine", "Sildenafil", "Tadalafil"
]

TREATMENTS = [
    "Physical Therapy", "Occupational Therapy", "Speech Therapy", "Chemotherapy",
    "Radiation Therapy", "Immunotherapy", "Dialysis", "Cognitive Behavioral Therapy",
    "Electroconvulsive Therapy", "Appendectomy", "Cholecystectomy", "Colectomy",
    "Hernia Repair", "Coronary Artery Bypass Grafting", "Heart Valve Replacement",
    "Pacemaker Implantation", "Joint Replacement", "Arthroscopy", "Thyroidectomy",
    "Mastectomy", "Hysterectomy", "Prostatectomy", "Dietary Modification",
    "Exercise Program", "Smoking Cessation", "Weight Management", "Stress Management",
    "Insulin Pump", "CPAP Machine", "Oxygen Therapy", "Nebulizer", "Cardiac Monitoring"
]

# === GENERATORS ===

def make_icd(category, idx):
    prefixes = {"Cardiovascular": "I", "Respiratory": "J", "Neurological": "G",
        "Gastrointestinal": "K", "Endocrine": "E", "Infectious": "A", "Oncological": "C",
        "Musculoskeletal": "M", "Dermatological": "L", "Renal": "N", "Hematological": "D",
        "Immunological": "D", "Ophthalmological": "H", "Psychiatric": "F", "Hepatobiliary": "K", "Thyroid": "E"}
    return f"{prefixes.get(category, 'Z')}{idx:02d}"

def main():
    print("Generating Medigraph dataset...")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Generate diseases
    diseases = []
    used_names = set()
    idx = 1

    prefixes = ["Primary", "Secondary", "Chronic", "Acute", "Idiopathic", "Familial", "Hereditary", "Sporadic", "Late-onset", "Early-onset"]
    modifiers = ["with complications", "in remission", "refractory", "recurrent", "with neuropathy", "with cardiomyopathy", "with renal involvement", "with hepatic involvement"]

    for category in DISEASE_CATEGORIES:
        templates = DISEASE_TEMPLATES.get(category, [])
        # First add all base templates
        for base in templates:
            if base not in used_names:
                diseases.append({
                    "id": f"DIS_{idx:05d}",
                    "name": base,
                    "category": category,
                    "icd_code": make_icd(category, idx % 100),
                    "description": f"A {category.lower()} condition.",
                    "severity": random.choice(["mild", "moderate", "severe", "life-threatening"])
                })
                used_names.add(base)
                idx += 1

        # Generate 50+ variants per category
        base_for_variants = templates[0] if templates else "Syndrome"
        for v in range(60):
            pref = random.choice(prefixes)
            mod = random.choice(modifiers) if random.random() > 0.5 else ""
            base = random.choice(templates) if random.random() > 0.3 else base_for_variants
            name = f"{pref} {base}"
            if mod:
                name += f" {mod}"
            if name not in used_names:
                diseases.append({
                    "id": f"DIS_{idx:05d}",
                    "name": name,
                    "category": category,
                    "icd_code": make_icd(category, idx % 100),
                    "description": f"A {category.lower()} condition.",
                    "severity": random.choice(["mild", "moderate", "severe", "life-threatening"])
                })
                used_names.add(name)
                idx += 1

    # Generate symptoms
    symptoms = []
    for i, (name, system) in enumerate(SYMPTOMS, 1):
        symptoms.append({
            "id": f"SYM_{i:03d}",
            "name": name,
            "body_system": system,
            "type": "symptom",
            "description": f"A {system.lower()} symptom."
        })

    # Generate drugs
    drugs = []
    for i, name in enumerate(DRUGS, 1):
        drugs.append({
            "id": f"DRG_{i:04d}",
            "name": name,
            "type": "drug",
            "category": "Pharmacological",
            "description": f"A medication used in treatment.",
            "side_effects": random.choice(["Nausea", "Dizziness", "Fatigue", "Headache", "Dry mouth"])
        })

    # Generate treatments
    treatments = []
    for i, name in enumerate(TREATMENTS, 1):
        treatments.append({
            "id": f"TRT_{i:04d}",
            "name": name,
            "type": "treatment",
            "category": "Intervention",
            "description": f"A treatment procedure.",
            "side_effects": ""
        })

    all_nodes = drugs + treatments

    # Generate relationships
    relationships = []
    sev = ["mild", "moderate", "severe", "life-threatening"]
    freq = ["occasional", "intermittent", "persistent", "constant"]
    eff = ["high", "moderate", "low", "variable"]

    symptom_pool = list(symptoms)
    drug_pool = list(drugs)
    treatment_pool = list(treatments)

    # Disease -> Symptom, Disease -> Treatment/Drug
    for d in diseases:
        cat = d["category"]
        # 3-6 symptoms
        n_syms = random.randint(3, 6)
        for _ in range(n_syms):
            s = random.choice(symptom_pool)
            relationships.append({
                "source_id": d["id"], "source_type": "Disease", "target_id": s["id"], "target_type": "Symptom",
                "type": "HAS_SYMPTOM", "severity": random.choice(sev), "frequency": random.choice(freq),
                "efficacy": None, "first_line": None, "interaction_type": None, "description": None
            })
            relationships.append({
                "source_id": s["id"], "source_type": "Symptom", "target_id": d["id"], "target_type": "Disease",
                "type": "CAUSED_BY", "severity": None, "frequency": None,
                "efficacy": None, "first_line": None, "interaction_type": None, "description": None
            })
        # 1-3 treatments
        for _ in range(random.randint(1, 3)):
            t = random.choice(all_nodes)
            relationships.append({
                "source_id": d["id"], "source_type": "Disease", "target_id": t["id"], "target_type": t["type"],
                "type": "TREATED_BY", "severity": None, "frequency": None,
                "efficacy": random.choice(eff), "first_line": random.choice([True, False]),
                "interaction_type": None, "description": None
            })

    # Drug -> Drug interactions
    interacted = set()
    for _ in range(300):
        d1, d2 = random.sample(drug_pool, 2)
        key = tuple(sorted([d1["id"], d2["id"]]))
        if key not in interacted:
            interacted.add(key)
            relationships.append({
                "source_id": d1["id"], "source_type": "Drug", "target_id": d2["id"], "target_type": "Drug",
                "type": "INTERACTS_WITH", "severity": None, "frequency": None, "efficacy": None, "first_line": None,
                "interaction_type": random.choice(["additive", "synergistic", "antagonistic", "pharmacokinetic"]),
                "description": f"May interact with {d2['name']}"
            })

    # Write CSVs
    print(f"Writing {len(diseases)} diseases...")
    with open(data_dir / "diseases.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "category", "icd_code", "description", "severity"])
        w.writeheader()
        w.writerows(diseases)

    print(f"Writing {len(symptoms)} symptoms...")
    with open(data_dir / "symptoms.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "body_system", "type", "description"])
        w.writeheader()
        w.writerows(symptoms)

    print(f"Writing {len(all_nodes)} treatments/drugs...")
    with open(data_dir / "treatments.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name", "type", "category", "description", "side_effects"])
        w.writeheader()
        w.writerows(all_nodes)

    print(f"Writing {len(relationships)} relationships...")
    fields = ["source_id", "source_type", "target_id", "target_type", "type", "severity",
              "frequency", "efficacy", "first_line", "interaction_type", "description"]
    with open(data_dir / "relationships.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(relationships)

    # Stats
    rel_types = {}
    for r in relationships:
        rel_types[r["type"]] = rel_types.get(r["type"], 0) + 1

    print("\n=== Dataset Complete ===")
    print(f"Diseases: {len(diseases)}")
    print(f"Symptoms: {len(symptoms)}")
    print(f"Drugs: {len(drugs)}")
    print(f"Treatments: {len(treatments)}")
    print(f"Total Relationships: {len(relationships)}")
    for t, c in sorted(rel_types.items()):
        print(f"  {t}: {c}")

if __name__ == "__main__":
    main()
