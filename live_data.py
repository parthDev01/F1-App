"""
OpenF1 Live Data Module
Polls https://api.openf1.org — completely free, no API key required.
Falls back to demo data when no live session is active.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
import httpx

log = logging.getLogger("f1.live")

OPENF1_BASE = "https://api.openf1.org/v1"

TEAM_COLORS = {
    "Red Bull Racing": "#3671C6", "Oracle Red Bull Racing": "#3671C6",
    "Mercedes":        "#27F4D2", "Mercedes-AMG Petronas": "#27F4D2",
    "Ferrari":         "#E8002D", "Scuderia Ferrari":      "#E8002D",
    "McLaren":         "#FF8000", "McLaren F1 Team":       "#FF8000",
    "Aston Martin":    "#358C75", "Aston Martin Aramco":   "#358C75",
    "Alpine":          "#0093CC", "BWT Alpine F1 Team":    "#0093CC",
    "Williams":        "#005AFF", "Williams Racing":       "#005AFF",
    "AlphaTauri":      "#5E8FAA", "RB":                    "#5E8FAA",
    "Sauber":          "#52E252", "Kick Sauber":           "#52E252",
    "Haas":            "#B6BABD", "MoneyGram Haas":        "#B6BABD",
}


async def fetch(client: httpx.AsyncClient, path: str, params: dict = None) -> Optional[Any]:
    try:
        resp = await client.get(f"{OPENF1_BASE}/{path}", params=params, timeout=8.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.warning(f"OpenF1 fetch failed [{path}]: {e}")
        return None


async def get_latest_session(client: httpx.AsyncClient) -> Optional[Dict]:
    data = await fetch(client, "sessions", {"session_type": "Race"})
    if not data:
        return None
    sorted_sessions = sorted(data, key=lambda s: s.get("date_start", ""), reverse=True)
    return sorted_sessions[0] if sorted_sessions else None


async def get_live_drivers(client: httpx.AsyncClient, session_key: int) -> List[Dict]:
    data = await fetch(client, "drivers", {"session_key": session_key})
    return data or []


async def get_positions(client: httpx.AsyncClient, session_key: int) -> List[Dict]:
    data = await fetch(client, "position", {"session_key": session_key})
    if not data:
        return []
    by_driver: Dict[int, Dict] = {}
    for entry in data:
        drv = entry.get("driver_number")
        if drv is None:
            continue
        existing = by_driver.get(drv)
        if existing is None or entry.get("date", "") > existing.get("date", ""):
            by_driver[drv] = entry
    return list(by_driver.values())


async def get_intervals(client: httpx.AsyncClient, session_key: int) -> List[Dict]:
    data = await fetch(client, "intervals", {"session_key": session_key})
    if not data:
        return []
    by_driver: Dict[int, Dict] = {}
    for entry in data:
        drv = entry.get("driver_number")
        if drv is None:
            continue
        existing = by_driver.get(drv)
        if existing is None or entry.get("date", "") > existing.get("date", ""):
            by_driver[drv] = entry
    return list(by_driver.values())


async def get_stints(client: httpx.AsyncClient, session_key: int) -> List[Dict]:
    data = await fetch(client, "stints", {"session_key": session_key})
    return data or []


async def get_lap_data(client: httpx.AsyncClient, session_key: int) -> List[Dict]:
    data = await fetch(client, "laps", {"session_key": session_key})
    return data or []


async def get_weather(client: httpx.AsyncClient, session_key: int) -> Optional[Dict]:
    data = await fetch(client, "weather", {"session_key": session_key})
    if not data:
        return None
    return data[-1] if isinstance(data, list) and data else data


async def get_race_control(client: httpx.AsyncClient, session_key: int) -> List[Dict]:
    data = await fetch(client, "race_control", {"session_key": session_key})
    return data or []


async def build_race_state(session_key: int) -> Dict:
    async with httpx.AsyncClient() as client:
        (drivers_raw, positions_raw, intervals_raw,
         stints_raw, laps_raw, weather_raw, rc_raw) = await asyncio.gather(
            get_live_drivers(client, session_key),
            get_positions(client, session_key),
            get_intervals(client, session_key),
            get_stints(client, session_key),
            get_lap_data(client, session_key),
            get_weather(client, session_key),
            get_race_control(client, session_key),
        )

    pos_map   = {p["driver_number"]: p for p in positions_raw}
    int_map   = {i["driver_number"]: i for i in intervals_raw}
    stint_map: Dict[int, Dict] = {}
    for s in stints_raw:
        drv = s.get("driver_number")
        lap = s.get("lap_start", 0)
        if drv and (drv not in stint_map or lap > stint_map[drv].get("lap_start", 0)):
            stint_map[drv] = s

    best_laps:  Dict[int, float] = {}
    last_laps:  Dict[int, float] = {}
    lap_counts: Dict[int, int]   = {}
    for lap in laps_raw:
        drv = lap.get("driver_number")
        if drv is None:
            continue
        dur = lap.get("lap_duration")
        if dur:
            if drv not in best_laps or dur < best_laps[drv]:
                best_laps[drv] = dur
            last_laps[drv] = dur
        lap_counts[drv] = max(lap_counts.get(drv, 0), lap.get("lap_number", 0))

    current_lap = max(lap_counts.values(), default=0) if lap_counts else 0

    sc_active  = False
    vsc_active = False
    red_flag   = False
    for msg in reversed(rc_raw or []):
        flag = (msg.get("flag") or "").upper()
        cat  = (msg.get("category") or "").upper()
        if "SAFETY CAR" in cat or flag == "SC":
            sc_active = True; break
        if "VIRTUAL" in cat or flag == "VSC":
            vsc_active = True; break
        if flag in ("RED", "RED FLAG"):
            red_flag = True; break
        if flag in ("GREEN", "CLEAR"):
            break

    weather_str = "dry"
    if weather_raw:
        rain = weather_raw.get("rainfall", 0)
        if rain > 0.5:
            weather_str = "wet"
        elif rain > 0:
            weather_str = "damp"

    drivers_out = []
    for drv in drivers_raw:
        num   = drv.get("driver_number")
        pos   = pos_map.get(num, {}).get("position", 20)
        intv  = int_map.get(num, {})
        stint = stint_map.get(num, {})

        gap_to_leader = intv.get("gap_to_leader") or 0.0
        interval      = intv.get("interval") or 0.0
        compound      = (stint.get("compound") or "MEDIUM").upper()
        tyre_age      = current_lap - (stint.get("lap_start") or 1) + 1

        team  = drv.get("team_name", "")
        color = TEAM_COLORS.get(team, "#888888")

        drivers_out.append({
            "driver_number":  num,
            "driver_code":    drv.get("name_acronym", "???"),
            "full_name":      drv.get("full_name", ""),
            "team":           team,
            "team_color":     color,
            "position":       pos,
            "gap_to_leader":  float(gap_to_leader) if isinstance(gap_to_leader, (int, float)) else 0.0,
            "interval":       float(interval) if isinstance(interval, (int, float)) else 0.0,
            "tyre_compound":  compound,
            "tyre_age":       max(1, tyre_age),
            "pit_stops":      stint.get("stint_number", 1) - 1,
            "last_lap_time":  round(last_laps.get(num, 0.0), 3),
            "best_lap_time":  round(best_laps.get(num, 0.0), 3),
            "laps_completed": lap_counts.get(num, 0),
        })

    drivers_out.sort(key=lambda d: d["position"])

    return {
        "session_key":  session_key,
        "current_lap":  current_lap,
        "weather":      weather_str,
        "safety_car":   sc_active,
        "vsc":          vsc_active,
        "red_flag":     red_flag,
        "track_temp":   weather_raw.get("track_temperature", 35) if weather_raw else 35,
        "air_temp":     weather_raw.get("air_temperature", 24)   if weather_raw else 24,
        "drivers":      drivers_out,
    }


# ── Demo data (shown between race weekends) ───────────────────────────────────

DEMO_DRIVERS = [
    {"driver_number":1,  "driver_code":"VER","full_name":"Max Verstappen",  "team":"Red Bull Racing","team_color":"#3671C6","position":1, "gap_to_leader":0.0,   "interval":0.0,  "tyre_compound":"MEDIUM","tyre_age":12,"pit_stops":0,"last_lap_time":92.456,"best_lap_time":91.831,"laps_completed":27},
    {"driver_number":44, "driver_code":"HAM","full_name":"Lewis Hamilton",   "team":"Mercedes",       "team_color":"#27F4D2","position":2, "gap_to_leader":4.234, "interval":4.234,"tyre_compound":"MEDIUM","tyre_age":12,"pit_stops":0,"last_lap_time":92.891,"best_lap_time":92.105,"laps_completed":27},
    {"driver_number":16, "driver_code":"LEC","full_name":"Charles Leclerc",  "team":"Ferrari",        "team_color":"#E8002D","position":3, "gap_to_leader":7.109, "interval":2.875,"tyre_compound":"SOFT",  "tyre_age":6, "pit_stops":1,"last_lap_time":92.711,"best_lap_time":91.903,"laps_completed":27},
    {"driver_number":11, "driver_code":"PER","full_name":"Sergio Perez",     "team":"Red Bull Racing","team_color":"#3671C6","position":4, "gap_to_leader":12.440,"interval":5.331,"tyre_compound":"MEDIUM","tyre_age":15,"pit_stops":0,"last_lap_time":93.201,"best_lap_time":92.415,"laps_completed":27},
    {"driver_number":55, "driver_code":"SAI","full_name":"Carlos Sainz",     "team":"Ferrari",        "team_color":"#E8002D","position":5, "gap_to_leader":15.882,"interval":3.442,"tyre_compound":"HARD",  "tyre_age":22,"pit_stops":0,"last_lap_time":93.544,"best_lap_time":92.701,"laps_completed":27},
    {"driver_number":63, "driver_code":"RUS","full_name":"George Russell",   "team":"Mercedes",       "team_color":"#27F4D2","position":6, "gap_to_leader":19.230,"interval":3.348,"tyre_compound":"HARD",  "tyre_age":22,"pit_stops":0,"last_lap_time":93.788,"best_lap_time":92.940,"laps_completed":27},
    {"driver_number":4,  "driver_code":"NOR","full_name":"Lando Norris",     "team":"McLaren",        "team_color":"#FF8000","position":7, "gap_to_leader":23.110,"interval":3.880,"tyre_compound":"MEDIUM","tyre_age":8, "pit_stops":1,"last_lap_time":94.012,"best_lap_time":92.788,"laps_completed":27},
    {"driver_number":81, "driver_code":"PIA","full_name":"Oscar Piastri",    "team":"McLaren",        "team_color":"#FF8000","position":8, "gap_to_leader":27.670,"interval":4.560,"tyre_compound":"MEDIUM","tyre_age":8, "pit_stops":1,"last_lap_time":94.234,"best_lap_time":93.011,"laps_completed":27},
    {"driver_number":14, "driver_code":"ALO","full_name":"Fernando Alonso",  "team":"Aston Martin",   "team_color":"#358C75","position":9, "gap_to_leader":31.990,"interval":4.320,"tyre_compound":"HARD",  "tyre_age":18,"pit_stops":0,"last_lap_time":94.456,"best_lap_time":93.221,"laps_completed":27},
    {"driver_number":18, "driver_code":"STR","full_name":"Lance Stroll",     "team":"Aston Martin",   "team_color":"#358C75","position":10,"gap_to_leader":38.220,"interval":6.230,"tyre_compound":"HARD",  "tyre_age":18,"pit_stops":0,"last_lap_time":94.788,"best_lap_time":93.540,"laps_completed":27},
]

DEMO_SESSION = {
    "session_key":    9999,
    "circuit":        "bahrain",
    "circuit_name":   "Bahrain International Circuit",
    "total_laps":     57,
    "current_lap":    27,
    "weather":        "dry",
    "safety_car":     False,
    "vsc":            False,
    "red_flag":       False,
    "track_temp":     35,
    "air_temp":       24,
    "drivers":        DEMO_DRIVERS,
    "demo_mode":      True,
}
