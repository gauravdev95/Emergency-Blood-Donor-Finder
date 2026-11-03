"""Seed demo donors for Agra (the example from the project brief + more).
Run once: python seed.py  (safe to re-run: it clears demo donors first)
Phones here are demo placeholders, not real people."""
import sqlite3
from app import DB, init_db
from dsa import PLACES

DONORS = [
    # name, group, locality, phone(demo), available, share_contact
    ("Donor A", "O+", "Sikandra", "98XXXXXX01", 1, 1),
    ("Donor B", "O+", "Kamla Nagar", "98XXXXXX02", 1, 1),
    ("Donor C", "O+", "Dayal Bagh", "98XXXXXX03", 1, 0),
    ("Donor D", "A+", "Civil Lines", "98XXXXXX04", 1, 1),
    ("Priya S.", "O-", "Civil Lines", "98XXXXXX05", 1, 1),
    ("Rahul V.", "B+", "Tajganj", "98XXXXXX06", 1, 1),
    ("Anjali M.", "A-", "Khandari", "98XXXXXX07", 0, 1),  # unavailable: must be excluded
    ("Vikram T.", "AB+", "Shahganj", "98XXXXXX08", 1, 0),
    ("Neha K.", "B-", "Sadar Bazaar", "98XXXXXX09", 1, 1),
    ("Amit R.", "O+", "Bodla", "98XXXXXX10", 1, 1),
    ("Sana F.", "AB-", "Agra Cantt", "98XXXXXX11", 1, 1),
    ("Rohan G.", "A+", "Dayal Bagh", "98XXXXXX12", 1, 1),
]

if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM donors")
    for name, group, loc, phone, avail, share in DONORS:
        lat, lon = PLACES[loc]
        conn.execute(
            "INSERT INTO donors (name,blood_group,city,locality,latitude,longitude,"
            "phone,available,verified,share_contact) VALUES (?,?,?,?,?,?,?,?,1,?)",
            (name, group, "Agra", loc, lat, lon, phone, avail, share))
    conn.commit()
    print(f"Seeded {len(DONORS)} demo donors into {DB}")
    conn.close()
