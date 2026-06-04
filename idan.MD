# 🛩️→🟧 Dorel → Core — How to Connect & Read/Write Data (code examples)

> For the Dorel team (Python). How to reach the Core service for aircraft/targets/events/path-history,
> with working request examples. Core is REST + `X-Api-Key`. Verified against prod 2026-06-04.
>
> ⚠️ **Preferred:** Dorel does NOT call Core directly for the live flow — it publishes to Live-Data
> (Kafka/Redis) and **Live-Data** persists to Core. But for reads (aircraft list, types) or direct writes
> (e.g. path-history), here's how to hit Core.

---

## 0. Connection
```python
import requests

CORE_BASE = "https://core-service-1015949672422.europe-west1.run.app"
API_KEY   = "adminkey123456789"   # from env CORE_API_KEY in real deploy

HEADERS = {
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY,          # ⚠️ REQUIRED on every protected route
}
```
Rules:
- Every `/api/*` route needs `X-Api-Key` (401 without it).
- Query `limit` must be **≤ 100** (400 otherwise).
- Coordinates are **GeoJSON `[lng, lat]`** (NOT [lat, lng]).
- `status` enum is **lowercase**: `free` / `busy` / `broken`.

---

## 1. Read aircraft (list / by status)
```python
def get_aircraft(status=None):
    params = {"limit": 100, "page": 1}
    if status:
        params["status"] = status.lower()   # 'free' | 'busy' | 'broken'
    r = requests.get(f"{CORE_BASE}/api/aircraft", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()["aircraft"]   # → [{ aircraft_id, aircraft_type, status }, ...]

free = get_aircraft("free")
```

## 2. Read aircraft types (price / payload metadata)
```python
def get_aircraft_types():
    r = requests.get(f"{CORE_BASE}/api/aircraft-types",
                     headers=HEADERS, params={"limit": 100, "page": 1}, timeout=10)
    r.raise_for_status()
    return r.json()   # { aircraft_types? / aircraft? : [...] }
```

## 3. Read the no-fly polygons (for route avoidance)
```python
def get_polygons():
    r = requests.get(f"{CORE_BASE}/api/polygons",
                     headers=HEADERS, params={"limit": 100, "page": 1}, timeout=10)
    r.raise_for_status()
    data = r.json()
    # shape: { "polygons": [ { id, name, zone, area/geojson:{type:'Polygon',coordinates:[[[lng,lat],...]]} } ] }
    return data.get("polygons", [])

# use the polygon coordinates as obstacles in the flight-path calculator
for p in get_polygons():
    poly = p.get("geojson") or p.get("area")
    rings = poly["coordinates"]   # [[[lng,lat], ...]]
```

## 4. Write a path-history point (after each tick) — if Dorel writes directly
```python
def append_path_history(aircraft_id, lng, lat, altitude, heading, speed):
    body = {
        "location": {"type": "Point", "coordinates": [lng, lat]},  # [lng,lat]!
        "altitude": altitude,
        "horizontal_speed_mps": speed,
        "vertical_speed_mps": 0,
        "heading_degrees": heading,
        "position_accuracy_m": 5,
    }
    r = requests.post(f"{CORE_BASE}/api/aircraft/{aircraft_id}/path-history",
                      headers=HEADERS, json=body, timeout=10)
    r.raise_for_status()
    return r.json()
```
> NOTE: in the agreed flow, **Live-Data** persists path-history (it consumes your position stream). Only write
> directly if we decide Dorel owns persistence. Coordinate with Idan/Daniel.

## 5. Read a single aircraft's latest position
```python
def latest_position(aircraft_id):
    r = requests.get(f"{CORE_BASE}/api/aircraft/{aircraft_id}/latest-position",
                     headers=HEADERS, timeout=10)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()   # { location:{type:'Point',coordinates:[lng,lat]}, altitude, ... }
```

---

## 6. ⭐ Recommended path: don't hit Core for the live flow — talk to Live-Data
For positions/dispatch, **publish to Live-Data** (it normalizes + persists + pushes to the COP). Two options
(decision pending — see CONN-3):

### Option A — Kafka (what your branches use)
```python
from confluent_kafka import Producer
import json
p = Producer({
    "bootstrap.servers": "pkc-619z3.us-east1.gcp.confluent.cloud:9092",
    "security.protocol": "SASL_SSL", "sasl.mechanisms": "PLAIN",
    "sasl.username": "<key>", "sasl.password": "<secret>",   # from env
})
# live position each tick → topic 'flight-routes'
p.produce("flight-routes", json.dumps({
    "aircraft_id": aid, "aircraft_type": "F-15",
    "location": {"latitude": lat, "longitude": lng},
    "altitude": alt, "heading_degrees": hdg, "horizontal_speed_mps": spd,
    "type": "movement",  # or 'attack' when dispatched
    "update_date": iso_now,
}))
# dispatch progress → topic 'aircraft.dispatch'
p.produce("aircraft.dispatch", json.dumps({
    "event_id": eid, "aircraft_id": aid, "phase": "enroute",   # enroute|arrived|struck|aborted
    "etaSec": eta, "origin": {...}, "target": {...}, "location": {...},
}))
p.flush()
```

### Option B — Redis (the design target, CONN-3)
```python
import redis, json
r = redis.from_url("redis://127.0.0.1:6379")   # GCP Memorystore via IAP tunnel
r.publish("c2:positions", json.dumps({...}))            # each tick
r.xadd("c2:dispatch", {"data": json.dumps({...})})      # phase progress
# consume our commands:
# r.xreadgroup('dorel','d', {'c2:commands': '>'}, count=10)
```

---

## 7. Quick test
```bash
curl "https://core-service-1015949672422.europe-west1.run.app/api/aircraft?status=free&limit=100" \
  -H "X-Api-Key: adminkey123456789"
# → 200 { "aircraft": [...] }
```

> Contracts: `BACKEND-INTEGRATION.md` (Core REST table) · `DOREL-REDIS-TO-FRONTEND.md` / `DOREL-TO-MAPS-FLOW.md` (the flow to the map) · `GCP-TEST-URLS.md` (URLs/keys).