"""
F1 2026 Season Calendar + Live Results Fetcher
- Race schedule is hardcoded (doesn't change mid-season)
- Last race results + standings are fetched LIVE from Jolpica API
  (free, no API key, modern Ergast replacement: api.jolpi.ca)
- Falls back to hardcoded data if API is unreachable
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List

import httpx

log = logging.getLogger("f1.calendar")

JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"

# ── 2026 Race Calendar ────────────────────────────────────────────────────────
# Bahrain (Rd 4) and Saudi Arabia (Rd 5) cancelled - 22 race season

CALENDAR_2026: List[Dict] = [
    {"round": 1,  "name": "Australian Grand Prix",    "circuit": "albert_park",   "circuit_name": "Albert Park Circuit",           "country": "Australia",   "city": "Melbourne",   "race_date": "2026-03-08T05:00:00Z", "sprint": False},
    {"round": 2,  "name": "Chinese Grand Prix",       "circuit": "shanghai",      "circuit_name": "Shanghai International Circuit", "country": "China",       "city": "Shanghai",    "race_date": "2026-03-15T07:00:00Z", "sprint": True},
    {"round": 3,  "name": "Japanese Grand Prix",      "circuit": "suzuka",        "circuit_name": "Suzuka International Racing Course","country": "Japan",    "city": "Suzuka",      "race_date": "2026-03-29T05:00:00Z", "sprint": False},
    {"round": 4,  "name": "Miami Grand Prix",         "circuit": "miami",         "circuit_name": "Miami International Autodrome",  "country": "USA",         "city": "Miami",       "race_date": "2026-05-03T19:00:00Z", "sprint": True},
    {"round": 5,  "name": "Canadian Grand Prix",      "circuit": "montreal",      "circuit_name": "Circuit Gilles Villeneuve",      "country": "Canada",      "city": "Montreal",    "race_date": "2026-05-24T18:00:00Z", "sprint": True},
    {"round": 6,  "name": "Monaco Grand Prix",        "circuit": "monaco",        "circuit_name": "Circuit de Monaco",              "country": "Monaco",      "city": "Monte Carlo", "race_date": "2026-06-07T13:00:00Z", "sprint": False},
    {"round": 7,  "name": "Spanish Grand Prix",       "circuit": "barcelona",     "circuit_name": "Circuit de Barcelona-Catalunya", "country": "Spain",       "city": "Barcelona",   "race_date": "2026-06-14T13:00:00Z", "sprint": False},
    {"round": 8,  "name": "Austrian Grand Prix",      "circuit": "red_bull_ring", "circuit_name": "Red Bull Ring",                  "country": "Austria",     "city": "Spielberg",   "race_date": "2026-06-28T13:00:00Z", "sprint": False},
    {"round": 9,  "name": "British Grand Prix",       "circuit": "silverstone",   "circuit_name": "Silverstone Circuit",            "country": "UK",          "city": "Silverstone", "race_date": "2026-07-05T14:00:00Z", "sprint": True},
    {"round": 10, "name": "Belgian Grand Prix",       "circuit": "spa",           "circuit_name": "Circuit de Spa-Francorchamps",   "country": "Belgium",     "city": "Spa",         "race_date": "2026-07-19T13:00:00Z", "sprint": False},
    {"round": 11, "name": "Hungarian Grand Prix",     "circuit": "hungaroring",   "circuit_name": "Hungaroring",                    "country": "Hungary",     "city": "Budapest",    "race_date": "2026-07-26T13:00:00Z", "sprint": False},
    {"round": 12, "name": "Dutch Grand Prix",         "circuit": "zandvoort",     "circuit_name": "Circuit Zandvoort",              "country": "Netherlands", "city": "Zandvoort",   "race_date": "2026-08-23T13:00:00Z", "sprint": True},
    {"round": 13, "name": "Italian Grand Prix",       "circuit": "monza",         "circuit_name": "Autodromo Nazionale Monza",      "country": "Italy",       "city": "Monza",       "race_date": "2026-09-06T13:00:00Z", "sprint": False},
    {"round": 14, "name": "Madrid Grand Prix",        "circuit": "madrid",        "circuit_name": "Madring Street Circuit",          "country": "Spain",       "city": "Madrid",      "race_date": "2026-09-13T13:00:00Z", "sprint": False},
    {"round": 15, "name": "Azerbaijan Grand Prix",    "circuit": "baku",          "circuit_name": "Baku City Circuit",              "country": "Azerbaijan",  "city": "Baku",        "race_date": "2026-09-26T11:00:00Z", "sprint": False},
    {"round": 16, "name": "Singapore Grand Prix",     "circuit": "singapore",     "circuit_name": "Marina Bay Street Circuit",      "country": "Singapore",   "city": "Singapore",   "race_date": "2026-10-11T12:00:00Z", "sprint": True},
    {"round": 17, "name": "United States Grand Prix", "circuit": "austin",        "circuit_name": "Circuit of the Americas",        "country": "USA",         "city": "Austin",      "race_date": "2026-10-25T19:00:00Z", "sprint": False},
    {"round": 18, "name": "Mexico City Grand Prix",   "circuit": "mexico_city",   "circuit_name": "Autodromo Hermanos Rodriguez",   "country": "Mexico",      "city": "Mexico City", "race_date": "2026-11-01T20:00:00Z", "sprint": False},
    {"round": 19, "name": "São Paulo Grand Prix",     "circuit": "interlagos",    "circuit_name": "Autodromo Jose Carlos Pace",     "country": "Brazil",      "city": "São Paulo",   "race_date": "2026-11-08T17:00:00Z", "sprint": False},
    {"round": 20, "name": "Las Vegas Grand Prix",     "circuit": "las_vegas",     "circuit_name": "Las Vegas Strip Circuit",        "country": "USA",         "city": "Las Vegas",   "race_date": "2026-11-21T06:00:00Z", "sprint": False},
    {"round": 21, "name": "Qatar Grand Prix",         "circuit": "losail",        "circuit_name": "Lusail International Circuit",   "country": "Qatar",       "city": "Lusail",      "race_date": "2026-11-29T17:00:00Z", "sprint": False},
    {"round": 22, "name": "Abu Dhabi Grand Prix",     "circuit": "yas_marina",    "circuit_name": "Yas Marina Circuit",             "country": "UAE",         "city": "Abu Dhabi",   "race_date": "2026-12-06T13:00:00Z", "sprint": False},
]

TEAM_COLORS = {
    "Red Bull":       "#3671C6", "Red Bull Racing":    "#3671C6",
    "Mercedes":       "#27F4D2",
    "Ferrari":        "#E8002D",
    "McLaren":        "#FF8000",
    "Aston Martin":   "#358C75",
    "Alpine":         "#0093CC",
    "Williams":       "#005AFF",
    "RB":             "#5E8FAA", "AlphaTauri":         "#5E8FAA",
    "Kick Sauber":    "#52E252", "Sauber":             "#52E252", "Audi": "#C6C6C6",
    "Haas":           "#B6BABD",
}

# ── Fallback hardcoded results (used if API is down) ─────────────────────────

FALLBACK_LAST_RACE = {
    "round": 2, "name": "Chinese Grand Prix",
    "circuit": "shanghai", "circuit_name": "Shanghai International Circuit",
    "date": "2026-03-15", "total_laps": 56, "weather": "dry",
    "podium": [
        {"pos": 1, "driver": "ANT", "full_name": "Kimi Antonelli",  "team": "Mercedes", "team_color": "#27F4D2", "time": "1:33:15.607", "points": 25},
        {"pos": 2, "driver": "RUS", "full_name": "George Russell",  "team": "Mercedes", "team_color": "#27F4D2", "time": "+5.515",      "points": 18},
        {"pos": 3, "driver": "HAM", "full_name": "Lewis Hamilton",  "team": "Ferrari",  "team_color": "#E8002D", "time": "+15.519",     "points": 15},
    ],
    "results": [
        {"pos": 1,  "driver": "ANT", "full_name": "Kimi Antonelli",  "team": "Mercedes",        "team_color": "#27F4D2", "points": 25},
        {"pos": 2,  "driver": "RUS", "full_name": "George Russell",  "team": "Mercedes",        "team_color": "#27F4D2", "points": 18},
        {"pos": 3,  "driver": "HAM", "full_name": "Lewis Hamilton",  "team": "Ferrari",         "team_color": "#E8002D", "points": 15},
        {"pos": 4,  "driver": "NOR", "full_name": "Lando Norris",    "team": "McLaren",         "team_color": "#FF8000", "points": 12},
        {"pos": 5,  "driver": "LEC", "full_name": "Charles Leclerc", "team": "Ferrari",         "team_color": "#E8002D", "points": 10},
        {"pos": 6,  "driver": "PIA", "full_name": "Oscar Piastri",   "team": "McLaren",         "team_color": "#FF8000", "points": 8},
        {"pos": 7,  "driver": "VER", "full_name": "Max Verstappen",  "team": "Red Bull Racing", "team_color": "#3671C6", "points": 6},
        {"pos": 8,  "driver": "ALO", "full_name": "Fernando Alonso", "team": "Aston Martin",    "team_color": "#358C75", "points": 4},
        {"pos": 9,  "driver": "GAS", "full_name": "Pierre Gasly",    "team": "Alpine",          "team_color": "#0093CC", "points": 2},
        {"pos": 10, "driver": "STR", "full_name": "Lance Stroll",    "team": "Aston Martin",    "team_color": "#358C75", "points": 1},
    ],
    "fastest_lap": {"driver": "NOR", "time": "1:35.412"},
}

FALLBACK_STANDINGS = [
    {"pos": 1,  "driver": "RUS", "full_name": "George Russell",     "team": "Mercedes",        "team_color": "#27F4D2", "pts": 43, "wins": 1},
    {"pos": 2,  "driver": "ANT", "full_name": "Kimi Antonelli",     "team": "Mercedes",        "team_color": "#27F4D2", "pts": 37, "wins": 1},
    {"pos": 3,  "driver": "LEC", "full_name": "Charles Leclerc",    "team": "Ferrari",         "team_color": "#E8002D", "pts": 30, "wins": 0},
    {"pos": 4,  "driver": "HAM", "full_name": "Lewis Hamilton",     "team": "Ferrari",         "team_color": "#E8002D", "pts": 27, "wins": 0},
    {"pos": 5,  "driver": "NOR", "full_name": "Lando Norris",       "team": "McLaren",         "team_color": "#FF8000", "pts": 24, "wins": 0},
    {"pos": 6,  "driver": "PIA", "full_name": "Oscar Piastri",      "team": "McLaren",         "team_color": "#FF8000", "pts": 16, "wins": 0},
    {"pos": 7,  "driver": "VER", "full_name": "Max Verstappen",     "team": "Red Bull Racing", "team_color": "#3671C6", "pts": 14, "wins": 0},
    {"pos": 8,  "driver": "ALO", "full_name": "Fernando Alonso",    "team": "Aston Martin",    "team_color": "#358C75", "pts": 10, "wins": 0},
    {"pos": 9,  "driver": "GAS", "full_name": "Pierre Gasly",       "team": "Alpine",          "team_color": "#0093CC", "pts": 6,  "wins": 0},
    {"pos": 10, "driver": "STR", "full_name": "Lance Stroll",       "team": "Aston Martin",    "team_color": "#358C75", "pts": 5,  "wins": 0},
]

FALLBACK_CONSTRUCTORS = [
    {"pos": 1, "team": "Mercedes",        "color": "#27F4D2", "pts": 80},
    {"pos": 2, "team": "Ferrari",         "color": "#E8002D", "pts": 57},
    {"pos": 3, "team": "McLaren",         "color": "#FF8000", "pts": 40},
    {"pos": 4, "team": "Aston Martin",    "color": "#358C75", "pts": 15},
    {"pos": 5, "team": "Red Bull Racing", "color": "#3671C6", "pts": 14},
    {"pos": 6, "team": "Alpine",          "color": "#0093CC", "pts": 8},
    {"pos": 7, "team": "Audi",            "color": "#C6C6C6", "pts": 4},
    {"pos": 8, "team": "Williams",        "color": "#005AFF", "pts": 3},
]

# ── In-memory cache (refreshed every 30 mins) ─────────────────────────────────

_cache: Dict = {
    "last_race":     None,
    "standings":     None,
    "constructors":  None,
    "fetched_at":    0,
}
CACHE_TTL = 1800  # 30 minutes


# ── Jolpica API fetchers ───────────────────────────────────────────────────────

async def _fetch_last_race_results() -> Optional[Dict]:
    """Fetch the most recent completed race result from Jolpica."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{JOLPICA_BASE}/2026/results.json?limit=1&offset=0")
            r.raise_for_status()
            data = r.json()
            races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            if not races:
                return None

            # Get the last race in the list
            race = races[-1]
            results_raw = race.get("Results", [])

            # Find matching calendar entry for circuit key
            race_name = race.get("raceName", "")
            circuit_key = _circuit_key_from_name(race_name)
            cal_entry = next((c for c in CALENDAR_2026 if c["name"] == race_name), None)

            results = []
            for r in results_raw:
                driver     = r.get("Driver", {})
                constructor = r.get("Constructor", {})
                team_name  = constructor.get("name", "")
                code       = driver.get("code", driver.get("driverId", "???").upper()[:3])
                pos        = int(r.get("position", 99))
                pts        = int(float(r.get("points", 0)))
                results.append({
                    "pos":        pos,
                    "driver":     code,
                    "full_name":  f"{driver.get('givenName','')} {driver.get('familyName','')}".strip(),
                    "team":       team_name,
                    "team_color": TEAM_COLORS.get(team_name, "#888"),
                    "points":     pts,
                    "time":       r.get("Time", {}).get("time") or r.get("status", ""),
                })

            # Fastest lap
            fastest = None
            for r in results_raw:
                fl = r.get("FastestLap", {})
                if fl.get("rank") == "1":
                    d = r.get("Driver", {})
                    fastest = {
                        "driver": d.get("code", "???"),
                        "time":   fl.get("Time", {}).get("time", ""),
                    }
                    break

            podium = [r for r in results if r["pos"] <= 3]
            # Add time to podium from raw
            for p in podium:
                raw = next((x for x in results_raw if int(x.get("position",0)) == p["pos"]), {})
                p["time"] = raw.get("Time", {}).get("time") or ("WINNER" if p["pos"] == 1 else raw.get("status",""))

            return {
                "round":        int(race.get("round", 0)),
                "name":         race_name,
                "circuit":      circuit_key,
                "circuit_name": race.get("Circuit", {}).get("circuitName", ""),
                "date":         race.get("date", ""),
                "total_laps":   max((int(r.get("laps","0")) for r in results_raw), default=0),
                "weather":      "dry",
                "podium":       podium,
                "results":      results,
                "fastest_lap":  fastest,
            }
    except Exception as e:
        log.warning(f"Jolpica last race fetch failed: {e}")
        return None


async def _fetch_driver_standings() -> Optional[List[Dict]]:
    """Fetch current WDC standings from Jolpica."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{JOLPICA_BASE}/2026/driverStandings.json")
            r.raise_for_status()
            data = r.json()
            standings_list = (data.get("MRData", {})
                              .get("StandingsTable", {})
                              .get("StandingsLists", []))
            if not standings_list:
                return None
            drivers = standings_list[0].get("DriverStandings", [])
            result = []
            for i, d in enumerate(drivers):
                driver      = d.get("Driver", {})
                constructor = d.get("Constructors", [{}])[0]
                team_name   = constructor.get("name", "")
                code        = driver.get("code", driver.get("driverId","???").upper()[:3])
                result.append({
                    "pos":       i + 1,
                    "driver":    code,
                    "full_name": f"{driver.get('givenName','')} {driver.get('familyName','')}".strip(),
                    "team":      team_name,
                    "team_color": TEAM_COLORS.get(team_name, "#888"),
                    "pts":       int(float(d.get("points", 0))),
                    "wins":      int(d.get("wins", 0)),
                })
            return result
    except Exception as e:
        log.warning(f"Jolpica standings fetch failed: {e}")
        return None


async def _fetch_constructor_standings() -> Optional[List[Dict]]:
    """Fetch current WCC standings from Jolpica."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{JOLPICA_BASE}/2026/constructorStandings.json")
            r.raise_for_status()
            data = r.json()
            standings_list = (data.get("MRData", {})
                              .get("StandingsTable", {})
                              .get("StandingsLists", []))
            if not standings_list:
                return None
            constructors = standings_list[0].get("ConstructorStandings", [])
            result = []
            for i, c in enumerate(constructors):
                constructor = c.get("Constructor", {})
                name        = constructor.get("name", "")
                result.append({
                    "pos":   i + 1,
                    "team":  name,
                    "color": TEAM_COLORS.get(name, "#888"),
                    "pts":   int(float(c.get("points", 0))),
                    "wins":  int(c.get("wins", 0)),
                })
            return result
    except Exception as e:
        log.warning(f"Jolpica constructors fetch failed: {e}")
        return None


def _circuit_key_from_name(race_name: str) -> str:
    """Map race name to our internal circuit key."""
    mapping = {
        "Australian": "albert_park", "Chinese": "shanghai", "Japanese": "suzuka",
        "Miami": "miami", "Canadian": "montreal", "Monaco": "monaco",
        "Spanish": "barcelona", "Austrian": "red_bull_ring", "British": "silverstone",
        "Belgian": "spa", "Hungarian": "hungaroring", "Dutch": "zandvoort",
        "Italian": "monza", "Madrid": "madrid", "Azerbaijan": "baku",
        "Singapore": "singapore", "United States": "austin", "Mexico City": "mexico_city",
        "São Paulo": "interlagos", "Las Vegas": "las_vegas", "Qatar": "losail",
        "Abu Dhabi": "yas_marina",
    }
    for key, val in mapping.items():
        if key.lower() in race_name.lower():
            return val
    return "unknown"


# ── Public refresh function (called by main.py background task) ───────────────

async def refresh_live_data():
    """
    Fetch latest results + standings from Jolpica API.
    Called every 30 minutes by the background poller in main.py.
    Falls back to hardcoded data if the API is unreachable.
    """
    import time
    now = time.time()

    # Skip if cache is fresh
    if _cache["last_race"] and (now - _cache["fetched_at"]) < CACHE_TTL:
        return

    log.info("Refreshing F1 results from Jolpica API...")

    last_race, standings, constructors = await asyncio.gather(
        _fetch_last_race_results(),
        _fetch_driver_standings(),
        _fetch_constructor_standings(),
        return_exceptions=True,
    )

    if isinstance(last_race, Exception):   last_race    = None
    if isinstance(standings, Exception):   standings    = None
    if isinstance(constructors, Exception): constructors = None

    _cache["last_race"]    = last_race    or FALLBACK_LAST_RACE
    _cache["standings"]    = standings    or FALLBACK_STANDINGS
    _cache["constructors"] = constructors or FALLBACK_CONSTRUCTORS
    _cache["fetched_at"]   = now

    round_num = _cache["last_race"].get("round", "?")
    log.info(f"Results refreshed — last race: Round {round_num} {_cache['last_race'].get('name','')}")


def get_last_race_results() -> Dict:
    return _cache["last_race"] or FALLBACK_LAST_RACE

def get_standings() -> List[Dict]:
    return _cache["standings"] or FALLBACK_STANDINGS

def get_constructor_standings() -> List[Dict]:
    return _cache["constructors"] or FALLBACK_CONSTRUCTORS


# ── Race status helpers ────────────────────────────────────────────────────────

def get_now() -> datetime:
    return datetime.now(timezone.utc)


def get_race_status() -> Dict:
    now        = get_now()
    last_race  = None
    next_race  = None

    for race in CALENDAR_2026:
        race_dt = datetime.fromisoformat(race["race_date"].replace("Z", "+00:00"))
        if race_dt < now:
            last_race = race
        elif next_race is None:
            next_race = race

    is_live    = False
    is_weekend = False

    if next_race:
        race_dt    = datetime.fromisoformat(next_race["race_date"].replace("Z", "+00:00"))
        diff_hours = (race_dt - now).total_seconds() / 3600
        if -2.0 <= diff_hours <= 1.5:
            is_live    = True
        if -72 <= diff_hours <= 4:
            is_weekend = True

    days_until = None
    if next_race and not is_live:
        race_dt    = datetime.fromisoformat(next_race["race_date"].replace("Z", "+00:00"))
        days_until = max(0, int((race_dt - now).total_seconds() / 86400))

    return {
        "is_live":         is_live,
        "is_weekend":      is_weekend,
        "last_race":       last_race,
        "next_race":       next_race,
        "days_until_next": days_until,
        "season_round":    last_race["round"] if last_race else 0,
        "total_rounds":    len(CALENDAR_2026),
    }
