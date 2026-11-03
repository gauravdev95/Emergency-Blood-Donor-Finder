# Emergency Blood Donor Finder 🩸

A real-world DSA-based web app: patients/hospitals find nearby, available
blood donors fast in an emergency, ranked nearest-first.

## Run it (2 minutes)

```bash
pip install -r requirements.txt
python seed.py      # demo Agra donors (first run only)
python app.py       # -> http://127.0.0.1:5000
```

Pages: `/` Home · `/register` Donor registration · `/request` Blood request ·
`/find` Find donors · `/map` Leaflet/OpenStreetMap donor map · `/admin` Admin dashboard

Design: the page background is a local vector file, `static/bg-healthcare.svg`
(pale-blue healthcare scene: blue leaves bottom-left, stethoscope top-right,
in the style of the reference image). It loads fully offline and stays sharp
at any screen size — no online image or font is used for the design.

## DSA implemented (in `dsa.py`, explained for viva)

| Concept | Where / how |
|---|---|
| HashMap | `build_hashmap()` — blood group → donor list, O(1) lookup |
| Graph | `build_graph()` — Agra localities as nodes, roads as weighted edges |
| Dijkstra | `dijkstra()` — shortest road route, e.g. Sikandra → Civil Lines = 12.0 km via Bodla, Kamla Nagar, Khandari |
| Min-Heap | `heapq` in `find_nearest_donors()` — nearest donor pops first |
| Sorting | Final list is distance-sorted, exact group before other compatible groups |
| Haversine | Straight-line km when a place is not on the road graph |
| Searching | Group lookup + availability filter before ranking |

Pipeline: request → HashMap → availability filter → distance (Dijkstra, else
Haversine) → Min-Heap → nearest-first list.

## Compatibility (discovery filter only)

O+ patients can receive from O+, O−; O− only from O−; AB+ from all groups;
full table in `dsa.py:COMPATIBLE_DONORS`. **A hospital / licensed blood bank
must always confirm compatibility, eligibility and suitability before any
donation. This app is not a blood bank or medical matching system.**

## Privacy

Donor phone numbers show in full only if the donor ticked contact consent
at registration; otherwise they are masked (`********10`). Exact donor
addresses are never stored — only locality + coordinates.

## API

| Endpoint | Purpose |
|---|---|
| `POST /api/register` | Register a donor |
| `GET /api/search?blood_group=O+&locality=Civil Lines` | Nearest compatible donors |
| `GET /api/donors` | All donors (phones masked per consent) |
| `POST /api/requests` / `GET /api/requests` | Create / list blood requests |
| `POST /api/donors/<id>/availability` | Toggle availability |
| `POST /api/donors/<id>/verify` | Admin verify |
| `POST /api/requests/<id>/status` | Pending / Completed / Cancelled |
| `GET /api/stats` | Counts |

## Tests

```bash
python -m unittest test_app -v
```

Covers: HashMap lookup, compatibility (incl. invalid group), Dijkstra
shortest path, Haversine, heap nearest-first ordering, unavailable-donor
exclusion, incompatible-group exclusion, API search / no-match / invalid
group / availability toggle / request creation / empty-database search.

## Viva cheat-sheet

- Why HashMap? Finding O+ donors without scanning every donor record.
- Why Min-Heap, not just sort? Nearest donor is available in O(log n) pops;
  final output is still sorted for display.
- Why Dijkstra over Haversine? Haversine is straight-line; Dijkstra gives
  the actual shortest *road* route on the locality graph.
- Time complexity: group lookup O(1), Dijkstra O((V+E) log V), heap ranking
  O(k log k) for k matching donors.

## Future scope

OTP verification, email/SMS alerts to nearby donors, live GPS, donor
history & last-donation eligibility (90-day gap), analytics dashboard,
admin login (add before any public deployment).
