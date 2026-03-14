"""
Seed patient records for testing.
Run: python -m scripts.seed_patients
Deletes all existing patients and adds 200 new ones with varied visit statuses.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.init_db import get_connection

VILLAGES = [
    "Bhandardaha", "Chakdaha", "Kalyani", "Ranaghat", "Krishnanagar",
    "Shantipur", "Naihati", "Barrackpore", "Bongaon", "Basirhat",
    "Diamond Harbour", "Baruipur", "Canning", "Kakdwip", "Haldia",
    "Madhyamgram", "Barasat", "Habra", "Ashoknagar", "Budge Budge",
]

MOTIVATORS = [
    "Asha Worker", "ANM", "Dr. Priya Sharma", "Dr. Rajesh Kumar",
    "Community Health Worker", "Sister Mary", "Dr. Anita Das",
    "Others", "Local NGO", "Government Scheme", "Dr. Smita Roy",
    "Dr. Amit Ghosh", "Health Volunteer", "Anganwadi Worker",
]

# 200 names - mix of Bengali/Indian names
NAMES = [
    "Anita Mondal", "Bina Das", "Chandana Roy", "Deepa Sarkar", "Esha Ghosh",
    "Fatima Khatun", "Gita Banerjee", "Hema Chakraborty", "Indira Naskar", "Jaya Pal",
    "Kavita Sen", "Lakshmi Dutta", "Mala Biswas", "Nandini Mukherjee", "Oindrila Bose",
    "Padmini Chatterjee", "Queena Ahmed", "Rekha Mandal", "Sonali De", "Tulika Hazra",
    "Uma Roy", "Vandana Paul", "Wahida Bibi", "Yamuna Singh", "Zarina Khatun",
    "Anjali Gupta", "Bharti Yadav", "Champa Devi", "Durga Kumari", "Ela Rani",
    "Farida Begum", "Ganga Devi", "Hena Parvin", "Ishita Roy", "Jhumur Naskar",
    "Kalyani Saha", "Lata Majumdar", "Mousumi Das", "Nupur Banerjee", "Oindrila Saha",
    "Priti Ghosh", "Rupa Mondal", "Sangita Roy", "Tandra Das", "Urmi Chakraborty",
    "Vandana Roy", "Swapna Biswas", "Tanusree Naskar", "Usha Devi", "Anamika Bose",
    "Bhaswati Chakraborty", "Chandrika Dutta", "Debjani Ghosh", "Eshita Naskar",
    "Falguni Pal", "Gargi Sen", "Haimanti Roy", "Indrani Das", "Jhuma Mondal",
    "Kanchana Saha", "Lopamudra Banerjee", "Maitreyi Chatterjee", "Nandita Paul",
    "Oindrila Hazra", "Paromita De", "Rituparna Sarkar", "Sreemoyee Biswas",
    "Tanusree Gupta", "Ushashi Yadav", "Ananya Roy", "Bipasha Das", "Chandana Ghosh",
    "Dipti Naskar", "Eshita Pal", "Farida Sen", "Gayatri Roy", "Hena Das",
    "Ipsita Mondal", "Jaya Saha", "Kasturi Banerjee", "Lipika Chatterjee",
    "Moumita Paul", "Nabanita Sarkar", "Oindrila Biswas", "Poulomi Gupta",
    "Riya Yadav", "Sneha Roy", "Tripti Das", "Urvashi Ghosh", "Ankita Naskar",
    "Bristi Pal", "Chandrima Sen", "Dola Roy", "Eshani Das", "Faria Mondal",
    "Gunjan Saha", "Hridita Banerjee", "Ishani Chatterjee", "Juhi Paul",
    "Koyel Sarkar", "Liza Biswas", "Moumita Gupta", "Nandini Yadav",
    "Oindrila Roy", "Puja Das", "Riya Ghosh", "Sneha Naskar", "Tulika Pal",
    "Uma Sen", "Vandana Roy", "Swapna Das", "Tanusree Mondal", "Usha Saha",
    "Anamika Banerjee", "Bhaswati Chatterjee", "Chandrika Paul", "Debjani Sarkar",
    "Eshita Biswas", "Falguni Gupta", "Gargi Yadav", "Haimanti Roy", "Indrani Das",
    "Jhuma Ghosh", "Kanchana Naskar", "Lopamudra Pal", "Maitreyi Sen",
    "Nandita Roy", "Oindrila Das", "Paromita Mondal", "Rituparna Saha",
    "Sreemoyee Banerjee", "Tanusree Chatterjee", "Ushashi Paul", "Ananya Sarkar",
    "Bipasha Biswas", "Chandana Gupta", "Dipti Yadav", "Eshita Roy",
    "Farida Das", "Gayatri Ghosh", "Hena Naskar", "Ipsita Pal", "Jaya Sen",
    "Kasturi Roy", "Lipika Das", "Moumita Mondal", "Nabanita Saha",
    "Oindrila Banerjee", "Poulomi Chatterjee", "Riya Paul", "Sneha Sarkar",
    "Tripti Biswas", "Urvashi Gupta", "Ankita Yadav", "Bristi Roy",
    "Chandrima Das", "Dola Ghosh", "Eshani Naskar", "Faria Pal", "Gunjan Sen",
    "Hridita Roy", "Ishani Das", "Juhi Mondal", "Koyel Saha", "Liza Banerjee",
    "Moumita Chatterjee", "Nandini Paul", "Oindrila Sarkar", "Puja Biswas",
    "Riya Gupta", "Sneha Yadav", "Tulika Roy", "Uma Das", "Vandana Ghosh",
    "Swapna Naskar", "Tanusree Pal", "Usha Sen", "Anita Roy", "Bina Das",
    "Chandana Ghosh", "Deepa Naskar", "Esha Pal", "Fatima Sen", "Gita Roy",
    "Hema Das", "Indira Mondal", "Jaya Saha", "Kavita Banerjee", "Lakshmi Chatterjee",
    "Mala Paul", "Nandini Sarkar", "Oindrila Biswas", "Padmini Gupta",
    "Queena Yadav", "Rekha Roy", "Sonali Das", "Tulika Ghosh", "Uma Naskar",
    "Vandana Pal", "Wahida Sen", "Yamuna Roy", "Zarina Das", "Anjali Mondal",
    "Bharti Saha", "Champa Banerjee", "Durga Chatterjee", "Ela Paul",
    "Farida Sarkar", "Ganga Biswas", "Hena Gupta", "Ishita Yadav", "Jhumur Roy",
    "Kalyani Das", "Lata Ghosh", "Mousumi Naskar", "Nupur Pal", "Oindrila Sen",
    "Priti Roy", "Rupa Das", "Sangita Mondal", "Tandra Saha", "Urmi Banerjee",
    "Vandana Chatterjee", "Swapna Paul", "Tanusree Sarkar", "Usha Biswas",
]


def main() -> int:
    conn = get_connection()
    cur = conn.cursor()

    # Delete change_logs first (foreign key to patients)
    cur.execute("DELETE FROM change_logs")
    cur.execute("DELETE FROM patients")
    deleted = cur.rowcount
    conn.commit()

    today = date.today()
    total = 200

    # Distribution: 50 completed, 50 on 3rd visit, 50 on 2nd visit, 50 EDD in next 30 days
    for i in range(total):
        serial = i + 1
        name = NAMES[i % len(NAMES)]
        patient_id = f"MTS{today.year}{serial:04d}"
        mobile = f"9{7000000000 + (i * 12345) % 1000000000}"
        village = VILLAGES[i % len(VILLAGES)]
        motivator = MOTIVATORS[i % len(MOTIVATORS)]

        # LMP spread over past 6 months
        lmp_offset = -(i * 5) % 180 - 30
        lmp = today + timedelta(days=lmp_offset)
        edd = lmp + timedelta(days=280)

        # Entry date: spread over last 4 months
        entry_offset = -(i * 3) % 120
        entry_date = today + timedelta(days=entry_offset)

        visit1 = entry_date
        visit2 = None
        visit3 = None
        final_visit = None

        if i < 50:
            # Completed - all 4 visits done
            visit2 = visit1 + timedelta(days=28)
            visit3 = visit2 + timedelta(days=28)
            final_visit = visit3 + timedelta(days=14)
        elif i < 100:
            # On 3rd visit - visit1, visit2 done, visit3 due
            visit2 = visit1 + timedelta(days=30)
            visit3 = today + timedelta(days=(i % 14) - 7)  # -7 to +7 days
        elif i < 150:
            # On 2nd visit - visit1 done, visit2 due
            visit2 = today + timedelta(days=(i % 21) - 5)  # -5 to +16 days
        else:
            # EDD in next 30 days - no visits or early visits
            edd = today + timedelta(days=(i % 30) + 1)  # 1-30 days from now
            lmp = edd - timedelta(days=280)
            if i < 175:
                visit1 = entry_date
                visit2 = visit1 + timedelta(days=28)
            # else: visit1 only or none

        def fmt(d):
            return d.isoformat() if d else None

        try:
            cur.execute(
                """
                INSERT INTO patients (
                    serial_number, patient_name, patient_id, mobile_number, village_name,
                    lmp_date, edd_date, motivator_name, visit1, visit2, visit3, final_visit,
                    entry_date, record_locked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    serial,
                    name,
                    patient_id,
                    mobile,
                    village,
                    fmt(lmp),
                    fmt(edd),
                    motivator,
                    fmt(visit1),
                    fmt(visit2),
                    fmt(visit3),
                    fmt(final_visit),
                    fmt(entry_date),
                    1 if final_visit else 0,
                ),
            )
        except Exception as e:
            print(f"Skip {patient_id}: {e}")

    conn.commit()
    conn.close()
    print(f"Deleted existing patients. Inserted 200 new patients.")
    print(f"  - 50 completed (all 4 visits)")
    print(f"  - 50 on 3rd visit")
    print(f"  - 50 on 2nd visit")
    print(f"  - 50 with EDD in next 30 days")
    print(f"Patient IDs: MTS{today.year}0001 to MTS{today.year}0200")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
