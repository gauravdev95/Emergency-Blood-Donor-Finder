"""Emergency Blood Donor Finder - Flask backend + SQLite.

Run:  pip install -r requirements.txt
      python seed.py        (first run only - demo Agra donors)
      python app.py         -> http://127.0.0.1:5000
Test: python -m unittest test_app -v

Privacy: donor phone numbers are shown in full ONLY when the donor
gave contact consent at registration; otherwise they are masked.
This is a donor-discovery / coordination tool, NOT a medical
blood-matching or blood-bank replacement system. A hospital or
licensed blood bank must confirm compatibility, eligibility and
suitability before any donation.
"""
import os
import sqlite3
from flask import Flask, g, jsonify, render_template, request

from dsa import (PLACES, VALID_GROUPS, compatible_groups, find_nearest_donors,
                 mask_phone)

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "blood_donors.db")
app = Flask(__name__)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_e=None):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS donors (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        blood_group TEXT NOT NULL, city TEXT DEFAULT 'Agra',
        locality TEXT, latitude REAL, longitude REAL, phone TEXT,
        available INTEGER DEFAULT 1, verified INTEGER DEFAULT 0,
        share_contact INTEGER DEFAULT 0, last_donation TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, patient_name TEXT NOT NULL,
        blood_group TEXT NOT NULL, hospital TEXT, locality TEXT,
        latitude REAL, longitude REAL, urgency TEXT DEFAULT 'Urgent',
        status TEXT DEFAULT 'Pending', contact TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit(); conn.close()


def donors_all():
    return [dict(r) for r in db().execute(
        "SELECT * FROM donors ORDER BY id").fetchall()]


def public_donor(d):
    d = dict(d)
    d["phone_display"] = mask_phone(d.get("phone", ""), bool(d.get("share_contact")))
    d.pop("phone", None)
    return d


@app.route("/")
def home():
    stats = db().execute(
        "SELECT (SELECT COUNT(*) FROM donors) d, "
        "(SELECT COUNT(*) FROM donors WHERE available=1) a, "
        "(SELECT COUNT(*) FROM requests) r").fetchone()
    return render_template("index.html", stats=stats, places=sorted(PLACES), groups=VALID_GROUPS)


@app.route("/register")
def register_page():
    return render_template("register.html", places=sorted(PLACES), groups=VALID_GROUPS)


@app.route("/request")
def request_page():
    return render_template("request.html", places=sorted(PLACES), groups=VALID_GROUPS)


@app.route("/find")
def find_page():
    return render_template("find.html", places=sorted(PLACES), groups=VALID_GROUPS)


@app.route("/map")
def map_page():
    return render_template("map.html", places=PLACES)


@app.route("/admin")
def admin_page():
    donors = donors_all()
    reqs = [dict(r) for r in db().execute(
        "SELECT * FROM requests ORDER BY id DESC").fetchall()]
    return render_template("admin.html", donors=donors, requests=reqs)


# ---------------- APIs ----------------
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True, silent=True) or request.form
    name = (data.get("name") or "").strip()
    group = (data.get("blood_group") or "").strip().upper()
    if not name or group not in VALID_GROUPS:
        return jsonify({"error": "Name and a valid blood group are required."}), 400
    locality = (data.get("locality") or "").strip()
    lat, lon = data.get("latitude"), data.get("longitude")
    if locality in PLACES and (lat in (None, "")):
        lat, lon = PLACES[locality]
    cur = db().execute(
        "INSERT INTO donors (name,blood_group,city,locality,latitude,longitude,phone,"
        "available,share_contact,last_donation) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (name, group, data.get("city") or "Agra", locality,
         float(lat) if lat not in (None, "") else None,
         float(lon) if lon not in (None, "") else None,
         data.get("phone") or "", 1 if str(data.get("available", "1")) in ("1", "true", "on") else 0,
         1 if str(data.get("share_contact", "0")) in ("1", "true", "on") else 0,
         data.get("last_donation") or None))
    db().commit()
    return jsonify({"ok": True, "donor_id": cur.lastrowid}), 201


@app.route("/api/search")
def api_search():
    group = (request.args.get("blood_group") or "").strip().upper()
    # Safety net for an unencoded '+' in the URL: browsers/servers turn a
    # raw '+' in a query string into a space, so "O+" arrives as "O ".
    # Bare O/A/B/AB are not valid groups anyway, so map them to the + form.
    group = {"O": "O+", "A": "A+", "B": "B+", "AB": "AB+"}.get(group, group)
    if group not in VALID_GROUPS:
        return jsonify({"error": f"Invalid blood group. Use one of: {', '.join(VALID_GROUPS)}"}), 400
    locality = request.args.get("locality") or None
    lat = request.args.get("latitude"); lon = request.args.get("longitude")
    results = find_nearest_donors(
        donors_all(), group,
        req_lat=float(lat) if lat else None, req_lon=float(lon) if lon else None,
        req_place=locality if locality in PLACES else None,
        limit=int(request.args.get("limit", 20)),
        exact_only=request.args.get("exact_only") == "1")
    return jsonify({"blood_group": group, "compatible_groups": compatible_groups(group),
                    "count": len(results), "donors": results})


@app.route("/api/donors")
def api_donors():
    return jsonify([public_donor(d) for d in donors_all()])


@app.route("/api/requests", methods=["GET", "POST"])
def api_requests():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or request.form
        group = (data.get("blood_group") or "").strip().upper()
        if not (data.get("patient_name") or "").strip() or group not in VALID_GROUPS:
            return jsonify({"error": "Patient name and a valid blood group are required."}), 400
        locality = (data.get("locality") or "").strip()
        lat, lon = data.get("latitude"), data.get("longitude")
        if locality in PLACES and (lat in (None, "")):
            lat, lon = PLACES[locality]
        cur = db().execute(
            "INSERT INTO requests (patient_name,blood_group,hospital,locality,latitude,"
            "longitude,urgency,contact) VALUES (?,?,?,?,?,?,?,?)",
            (data["patient_name"], group, data.get("hospital") or "",
             locality, float(lat) if lat not in (None, "") else None,
             float(lon) if lon not in (None, "") else None,
             data.get("urgency") or "Urgent", data.get("contact") or ""))
        db().commit()
        return jsonify({"ok": True, "request_id": cur.lastrowid}), 201
    return jsonify([dict(r) for r in db().execute(
        "SELECT * FROM requests ORDER BY id DESC").fetchall()])


@app.route("/api/donors/<int:donor_id>/availability", methods=["POST"])
def api_availability(donor_id):
    data = request.get_json(force=True, silent=True) or {}
    avail = 1 if str(data.get("available", "1")) in ("1", "true", "on") else 0
    cur = db().execute("UPDATE donors SET available=? WHERE id=?", (avail, donor_id))
    db().commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Donor not found."}), 404
    return jsonify({"ok": True, "donor_id": donor_id, "available": avail})


@app.route("/api/donors/<int:donor_id>/verify", methods=["POST"])
def api_verify(donor_id):
    cur = db().execute("UPDATE donors SET verified=1 WHERE id=?", (donor_id,))
    db().commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Donor not found."}), 404
    return jsonify({"ok": True, "donor_id": donor_id, "verified": 1})


@app.route("/api/requests/<int:req_id>/status", methods=["POST"])
def api_request_status(req_id):
    data = request.get_json(force=True, silent=True) or {}
    status = data.get("status") or "Completed"
    if status not in ("Pending", "Completed", "Cancelled"):
        return jsonify({"error": "Status must be Pending, Completed or Cancelled."}), 400
    cur = db().execute("UPDATE requests SET status=? WHERE id=?", (status, req_id))
    db().commit()
    if cur.rowcount == 0:
        return jsonify({"error": "Request not found."}), 404
    return jsonify({"ok": True, "request_id": req_id, "status": status})


@app.route("/api/stats")
def api_stats():
    row = db().execute(
        "SELECT (SELECT COUNT(*) FROM donors) donors, "
        "(SELECT COUNT(*) FROM donors WHERE available=1) available, "
        "(SELECT COUNT(*) FROM requests) requests, "
        "(SELECT COUNT(*) FROM requests WHERE status='Pending') pending").fetchone()
    return jsonify(dict(row))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
