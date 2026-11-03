"""Seed 50 demo donors for Agra (5 per locality, all blood groups covered).
Run once: python seed.py  (safe to re-run: it clears demo donors first)
Phones here are demo placeholders (9000000001-9000000050), not real people.
Availability: 44 available, 6 unavailable (so the availability filter is
demonstrable). Contact consent varies, so phone masking is demonstrable."""
import sqlite3
from app import DB, init_db
from dsa import PLACES

# name, group, locality, available, share_contact
DONORS = [
    ("Aarav Sharma", "O+", "Sikandra", 1, 1),
    ("Priya Singh", "O-", "Civil Lines", 1, 1),
    ("Rahul Verma", "B+", "Tajganj", 1, 1),
    ("Anjali Mehta", "A-", "Khandari", 0, 1),
    ("Vikram Thakur", "AB+", "Shahganj", 1, 0),
    ("Neha Kapoor", "B-", "Sadar Bazaar", 1, 1),
    ("Amit Rajput", "O+", "Bodla", 1, 1),
    ("Sana Fatima", "AB-", "Agra Cantt", 1, 1),
    ("Rohan Gupta", "A+", "Dayal Bagh", 1, 1),
    ("Kavya Yadav", "O+", "Kamla Nagar", 1, 0),
    ("Arjun Singh", "O+", "Sikandra", 1, 1),
    ("Divya Nair", "A+", "Civil Lines", 1, 1),
    ("Karan Malhotra", "B+", "Tajganj", 1, 0),
    ("Pooja Sharma", "O-", "Khandari", 1, 1),
    ("Manish Kumar", "A+", "Shahganj", 0, 1),
    ("Ritu Agarwal", "O+", "Sadar Bazaar", 1, 1),
    ("Sanjay Patel", "B-", "Bodla", 1, 1),
    ("Meera Joshi", "AB+", "Agra Cantt", 1, 0),
    ("Nikhil Rao", "A-", "Dayal Bagh", 1, 1),
    ("Simran Kaur", "O+", "Kamla Nagar", 1, 1),
    ("Deepak Yadav", "O+", "Sikandra", 1, 0),
    ("Ananya Iyer", "B+", "Civil Lines", 1, 1),
    ("Rajesh Gupta", "A+", "Tajganj", 1, 1),
    ("Shreya Verma", "O-", "Khandari", 1, 0),
    ("Varun Khanna", "AB-", "Shahganj", 1, 1),
    ("Tanvi Desai", "B+", "Sadar Bazaar", 0, 1),
    ("Mohit Chauhan", "O+", "Bodla", 1, 1),
    ("Ishita Bose", "A+", "Agra Cantt", 1, 1),
    ("Aditya Menon", "B-", "Dayal Bagh", 1, 0),
    ("Geeta Rani", "O+", "Kamla Nagar", 1, 1),
    ("Suresh Tiwari", "A-", "Sikandra", 1, 1),
    ("Lakshmi Pillai", "AB+", "Civil Lines", 1, 0),
    ("Harsh Vardhan", "O+", "Tajganj", 1, 1),
    ("Nisha Jain", "B+", "Khandari", 1, 1),
    ("Abhishek Singh", "A+", "Shahganj", 1, 0),
    ("Radhika Menon", "O-", "Sadar Bazaar", 0, 1),
    ("Vivek Sharma", "B+", "Bodla", 1, 1),
    ("Komal Singh", "O+", "Agra Cantt", 1, 1),
    ("Ravi Kumar", "A+", "Dayal Bagh", 1, 0),
    ("Sunita Devi", "B-", "Kamla Nagar", 1, 1),
    ("Akash Verma", "O+", "Sikandra", 1, 1),
    ("Preeti Nair", "A+", "Civil Lines", 1, 0),
    ("Gaurav Mishra", "AB+", "Tajganj", 0, 1),
    ("Swati Kulkarni", "O-", "Khandari", 1, 1),
    ("Tarun Bhatt", "B+", "Shahganj", 1, 1),
    ("Jyoti Sharma", "A-", "Sadar Bazaar", 1, 0),
    ("Pankaj Singh", "O+", "Bodla", 1, 1),
    ("Rekha Gupta", "B+", "Agra Cantt", 1, 1),
    ("Ankit Yadav", "A+", "Dayal Bagh", 1, 1),
    ("Farah Khan", "O+", "Kamla Nagar", 0, 1),
]

assert len(DONORS) == 50, f"Expected 50 donors, got {len(DONORS)}"

if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM donors")
    conn.execute("DELETE FROM requests")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='donors'")
    for i, (name, group, loc, avail, share) in enumerate(DONORS, start=1):
        lat, lon = PLACES[loc]
        # 9000000001..9000000050 are 10-digit demo placeholders
        phone = f"9000000{i:03d}"
        conn.execute(
            "INSERT INTO donors (name,blood_group,city,locality,latitude,longitude,"
            "phone,available,verified,share_contact) VALUES (?,?,?,?,?,?,?,?,1,?)",
            (name, group, "Agra", loc, lat, lon, phone, avail, share))
    conn.commit()
    n = conn.execute("SELECT COUNT(*), SUM(available) FROM donors").fetchone()
    print(f"Seeded {n[0]} demo donors ({n[1]} available) into {DB}")
    conn.close()
