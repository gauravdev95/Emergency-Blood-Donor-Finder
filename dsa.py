"""DSA engine for Emergency Blood Donor Finder.

Implements, from scratch (with heapq as the heap primitive):
  1. HashMap  -> blood-group index: dict[group, list[donor]]
  2. Graph    -> Agra locality road network (adjacency list)
  3. Dijkstra -> shortest road route between two localities
  4. Min-Heap -> donors ordered by distance (nearest first)
  5. Sorting  -> final ranking by distance, exact-group first
  6. Haversine-> straight-line distance when a place is off the graph

Blood compatibility below is the standard red-cell donor->recipient
rule. It is a *discovery filter only* -- a hospital / licensed blood
bank must always confirm eligibility and suitability before donation.
"""
import heapq
import math

VALID_GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]

# Recipient -> donor groups that can donate to them
COMPATIBLE_DONORS = {
    "O+":  ["O+", "O-"],
    "O-":  ["O-"],
    "A+":  ["A+", "A-", "O+", "O-"],
    "A-":  ["A-", "O-"],
    "B+":  ["B+", "B-", "O+", "O-"],
    "B-":  ["B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
}

# Agra localities used in the demo data (lat, lon)
PLACES = {
    "Sikandra": (27.2180, 77.9550),
    "Kamla Nagar": (27.2110, 77.9970),
    "Dayal Bagh": (27.2230, 78.0140),
    "Civil Lines": (27.1980, 78.0080),
    "Tajganj": (27.1680, 78.0450),
    "Shahganj": (27.1950, 77.9850),
    "Sadar Bazaar": (27.1930, 78.0140),
    "Khandari": (27.2050, 78.0120),
    "Bodla": (27.2250, 77.9850),
    "Agra Cantt": (27.1830, 78.0050),
}

# Road network: (place A, place B, road distance in km)
ROADS = [
    ("Sikandra", "Bodla", 3.0), ("Bodla", "Kamla Nagar", 4.0),
    ("Kamla Nagar", "Shahganj", 2.5), ("Shahganj", "Civil Lines", 3.0),
    ("Civil Lines", "Sadar Bazaar", 2.0), ("Sadar Bazaar", "Tajganj", 4.5),
    ("Civil Lines", "Khandari", 2.2), ("Khandari", "Dayal Bagh", 3.0),
    ("Kamla Nagar", "Khandari", 2.8), ("Sadar Bazaar", "Agra Cantt", 2.5),
    ("Agra Cantt", "Tajganj", 3.8), ("Dayal Bagh", "Sadar Bazaar", 4.0),
]


def build_hashmap(donors):
    """HashMap: blood group -> list of donors. O(1) lookup by group."""
    index = {g: [] for g in VALID_GROUPS}
    for d in donors:
        if d["blood_group"] in index:
            index[d["blood_group"]].append(d)
    return index


def build_graph():
    """Graph: adjacency list {place: [(neighbour, km), ...]}."""
    graph = {p: [] for p in PLACES}
    for a, b, km in ROADS:
        graph[a].append((b, km))
        graph[b].append((a, km))
    return graph


def dijkstra(graph, start, end):
    """Dijkstra's shortest path. Returns (distance_km, path_list) or (None, [])."""
    if start not in graph or end not in graph:
        return None, []
    dist = {node: float("inf") for node in graph}
    prev = {}
    dist[start] = 0.0
    heap = [(0.0, start)]
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist[node]:
            continue
        if node == end:
            break
        for neighbour, w in graph[node]:
            nd = d + w
            if nd < dist[neighbour]:
                dist[neighbour] = nd
                prev[neighbour] = node
                heapq.heappush(heap, (nd, neighbour))
    if dist[end] == float("inf"):
        return None, []
    path, cur = [], end
    while cur != start:
        path.append(cur)
        cur = prev[cur]
    path.append(start)
    return round(dist[end], 2), list(reversed(path))


def haversine(lat1, lon1, lat2, lon2):
    """Straight-line distance in km between two lat/lon points."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)), 2)


def compatible_groups(recipient_group):
    if recipient_group not in VALID_GROUPS:
        raise ValueError(f"Invalid blood group: {recipient_group}")
    return COMPATIBLE_DONORS[recipient_group]


def mask_phone(phone, consent):
    """Privacy: show full phone only with donor consent, else mask it."""
    if consent:
        return phone
    if not phone or len(phone) < 4:
        return "Hidden"
    return "*" * (len(phone) - 2) + phone[-2:]


def find_nearest_donors(donors, recipient_group, req_lat=None, req_lon=None,
                        req_place=None, limit=20, exact_only=False):
    """
    Pipeline: HashMap lookup -> availability filter -> distance
    (Dijkstra on the road graph, else Haversine) -> Min-Heap ->
    sorted nearest-first list. Exact blood group ranks before
    other compatible groups at similar distance.
    """
    groups = [recipient_group] if exact_only else compatible_groups(recipient_group)
    index = build_hashmap(donors)
    graph = build_graph()
    heap = []  # Min-Heap of (distance, exact_match_rank, donor)
    for group in groups:
        for d in index[group]:
            if not d.get("available"):
                continue  # unavailable donors are excluded, never ranked
            if req_place and d.get("locality") and req_place in graph and d["locality"] in graph:
                distance, path = dijkstra(graph, req_place, d["locality"])
                method = "road (Dijkstra)"
            elif req_lat is not None and req_lon is not None and d.get("latitude") and d.get("longitude"):
                distance, path = haversine(req_lat, req_lon, d["latitude"], d["longitude"]), []
                method = "straight-line (Haversine)"
            else:
                distance, path, method = None, [], "unknown"
            exact_rank = 0 if d["blood_group"] == recipient_group else 1
            heapq.heappush(heap, (distance if distance is not None else 9999,
                                  exact_rank, d["id"], d, path, method))
    results = []
    while heap and len(results) < limit:
        distance, _, _, d, path, method = heapq.heappop(heap)
        out = dict(d)
        out["distance_km"] = None if distance == 9999 else distance
        out["route"] = path
        out["distance_method"] = method
        out["phone_display"] = mask_phone(d.get("phone", ""), bool(d.get("share_contact")))
        out.pop("phone", None)
        results.append(out)
    return results
