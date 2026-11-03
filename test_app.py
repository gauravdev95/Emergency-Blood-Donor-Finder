"""Automated tests: DSA unit tests + Flask API tests. Run: python -m unittest test_app -v"""
import os
import tempfile
import unittest

import app as appmod
from dsa import (build_hashmap, compatible_groups, dijkstra, build_graph,
                 find_nearest_donors, haversine, mask_phone)


class TestDSA(unittest.TestCase):
    def test_hashmap_lookup(self):
        donors = [{"blood_group": "O+", "id": 1}, {"blood_group": "A+", "id": 2}]
        self.assertEqual(len(build_hashmap(donors)["O+"]), 1)

    def test_compatibility(self):
        self.assertEqual(compatible_groups("O+"), ["O+", "O-"])
        self.assertEqual(compatible_groups("AB+"), ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"])
        with self.assertRaises(ValueError):
            compatible_groups("X")

    def test_dijkstra_shortest(self):
        dist, path = dijkstra(build_graph(), "Sikandra", "Civil Lines")
        # Shortest: Sikandra-Bodla-Kamla Nagar-Khandari-Civil Lines = 3+4+2.8+2.2 = 12.0
        self.assertEqual(dist, 12.0)
        self.assertEqual(path, ["Sikandra", "Bodla", "Kamla Nagar", "Khandari", "Civil Lines"])
        self.assertEqual(path[0], "Sikandra"); self.assertEqual(path[-1], "Civil Lines")

    def test_haversine_positive(self):
        self.assertGreater(haversine(27.218, 77.955, 27.211, 77.997), 0)

    def test_heap_ranks_nearest_first_and_excludes_unavailable(self):
        donors = [
            {"id": 1, "blood_group": "O+", "available": 1, "locality": "Dayal Bagh", "phone": "1"},
            {"id": 2, "blood_group": "O+", "available": 1, "locality": "Sikandra", "phone": "2"},
            {"id": 3, "blood_group": "O+", "available": 0, "locality": "Sikandra", "phone": "3"},
            {"id": 4, "blood_group": "A+", "available": 1, "locality": "Sikandra", "phone": "4"},
        ]
        res = find_nearest_donors(donors, "O+", req_place="Civil Lines")
        ids = [r["id"] for r in res]
        self.assertNotIn(3, ids)   # unavailable excluded
        self.assertNotIn(4, ids)   # A+ cannot donate to O+
        dists = [r["distance_km"] for r in res]
        self.assertEqual(dists, sorted(dists))  # nearest first

    def test_mask_phone(self):
        self.assertEqual(mask_phone("9876543210", True), "9876543210")
        self.assertTrue(mask_phone("9876543210", False).endswith("10"))


class TestAPI(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        appmod.DB = path
        appmod.init_db()
        appmod.app.config["TESTING"] = True
        self.client = appmod.app.test_client()
        self.client.post("/api/register", json={"name": "Test O", "blood_group": "O+",
                                                "locality": "Sikandra", "phone": "9999999999",
                                                "share_contact": 1})
        self.client.post("/api/register", json={"name": "Test Off", "blood_group": "O+",
                                                "locality": "Kamla Nagar", "phone": "8888888888",
                                                "available": 0})

    def tearDown(self):
        os.unlink(appmod.DB)

    def test_search_o_plus(self):
        r = self.client.get("/api/search", query_string={"blood_group": "O+", "locality": "Civil Lines"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["count"], 1)  # unavailable donor excluded

    def test_unencoded_plus_group(self):
        # Regression test for the screenshot bug: a raw '+' in a query
        # string is decoded as a space by the server ("O+" -> "O ").
        # The API must still return the O+ donors, not a 400 error.
        r = self.client.get("/api/search?blood_group=O+&locality=Civil Lines")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["blood_group"], "O+")
        self.assertGreater(r.json["count"], 0)

    def test_no_matching_donors(self):
        r = self.client.get("/api/search", query_string={"blood_group": "AB-", "locality": "Civil Lines"})
        self.assertEqual(r.status_code, 200); self.assertEqual(r.json["count"], 0)

    def test_invalid_blood_group(self):
        r = self.client.get("/api/search", query_string={"blood_group": "X"})
        self.assertEqual(r.status_code, 400)

    def test_availability_toggle(self):
        r = self.client.post("/api/donors/1/availability", json={"available": 0})
        self.assertEqual(r.json["available"], 0)
        r = self.client.get("/api/search", query_string={"blood_group": "O+"})
        self.assertEqual(r.json["count"], 0)

    def test_create_request(self):
        r = self.client.post("/api/requests", json={"patient_name": "Patient X",
                                                    "blood_group": "O+", "locality": "Sikandra"})
        self.assertEqual(r.status_code, 201)

    def test_empty_db_search(self):
        # fresh DB with no donors still returns a clean empty list, not an error
        original = appmod.DB
        fd, path = tempfile.mkstemp(suffix=".db"); os.close(fd)
        appmod.DB = path; appmod.init_db()
        c = appmod.app.test_client()
        r = c.get("/api/search", query_string={"blood_group": "O+"})
        self.assertEqual(r.json["count"], 0)
        os.unlink(path)
        appmod.DB = original  # restore so tearDown deletes the setUp DB


if __name__ == "__main__":
    unittest.main()
