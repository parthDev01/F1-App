"""
F1DataService — combines two open-source data sources:
  • FastF1 (MIT License) — https://github.com/theOehrly/Fast-F1
    For historical session data: lap times, telemetry, tyre info
  • OpenF1 API (free public REST API) — https://openf1.org
    For live race data: positions, intervals, tyre compounds, pit stops
  • Jolpica/Ergast API (free public) — https://api.jolpi.ca
    For standings, schedule
"""

import httpx
import asyncio
import fastf1
import fastf1.core
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

# FastF1 cache — speeds up repeated data loads significantly
CACHE_DIR = Path(os.getenv("FF1_CACHE", "/tmp/fastf1_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

OPENF1_BASE = "https://api.openf1.org/v1"
JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"

TYRE_MAP = {"SOFT": "S", "MEDIUM": "M", "HARD": "H",
            "INTERMEDIATE": "I", "WET": "W", "UNKNOWN": "?"}

TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "Mercedes":        "#27F4D2",
    "Ferrari":         "#E8002D",
    "McLaren":         "#FF8000",
    "Aston Martin":    "#358C75",
    "Alpine":          "#0093CC",
    "Williams":        "#64C4FF",
    "RB":              "#6692FF",
    "Kick Sauber":     "#52E252",
    "Haas F1 Team":    "#B6BABD",
}


class F1DataService:
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=10.0)
        self._session_cache: dict = {}

    # ── OpenF1 helpers ────────────────────────────────────────────────────────
    async def _of1_get(self, path: str, params: dict = None) -> list | None:
        try:
            r = await self._client.get(f"{OPENF1_BASE}{path}", params=params)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning(f"OpenF1 {path} error: {e}")
            return None

    async def _jolpica_get(self, path: str) -> dict | None:
        try:
            r = await self._client.get(f"{JOLPICA_BASE}{path}.json")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning(f"Jolpica {path} error: {e}")
            return None

    # ── Current session ───────────────────────────────────────────────────────
    async def get_current_session(self) -> dict:
        sessions = await self._of1_get("/sessions", {"session_key": "latest"})
        if not sessions:
            return {}
        s = sessions[0]
        return {
            "session_key":  s.get("session_key"),
            "session_name": s.get("session_name"),
            "meeting_name": s.get("meeting_name"),
            "location":     s.get("location"),
            "country":      s.get("country_name"),
            "date_start":   s.get("date_start"),
            "date_end":     s.get("date_end"),
            "circuit_key":  s.get("circuit_key"),
            "year":         s.get("year"),
        }

    # ── Live race state (OpenF1) ──────────────────────────────────────────────
    async def get_live_state(self) -> dict | None:
        session_info, positions, intervals, car_data, pit_stops, weather, laps = await asyncio.gather(
            self._of1_get("/sessions", {"session_key": "latest"}),
            self._of1_get("/position",   {"session_key": "latest"}),
            self._of1_get("/intervals",  {"session_key": "latest"}),
            self._of1_get("/car_data",   {"session_key": "latest", "speed>=": 0}),
            self._of1_get("/pit",        {"session_key": "latest"}),
            self._of1_get("/weather",    {"session_key": "latest"}),
            self._of1_get("/laps",       {"session_key": "latest"}),
            return_exceptions=False
        )

        if not session_info:
            return None

        session = session_info[0]

        # Build per-driver lookup tables
        pos_map = {}
        if positions:
            for p in positions:
                d = p["driver_number"]
                pos_map[d] = p.get("position", 99)

        interval_map = {}
        if intervals:
            for i in intervals:
                d = i["driver_number"]
                interval_map[d] = {
                    "interval":    i.get("interval"),
                    "gap_to_leader": i.get("gap_to_leader"),
                }

        car_map = {}
        if car_data:
            for c in car_data:
                d = c["driver_number"]
                car_map[d] = {
                    "speed":    c.get("speed", 0),
                    "throttle": c.get("throttle", 0),
                    "brake":    c.get("brake", 0),
                    "drs":      c.get("drs", 0) > 8,
                    "gear":     c.get("n_gear", 0),
                    "rpm":      c.get("rpm", 0),
                }

        pit_map = {}  # driver_number -> list of pit stops
        if pit_stops:
            for p in pit_stops:
                d = p["driver_number"]
                pit_map.setdefault(d, []).append({
                    "lap":      p.get("lap_number"),
                    "duration": p.get("pit_duration"),
                })

        # Latest lap per driver
        lap_map = {}
        if laps:
            for l in laps:
                d = l["driver_number"]
                ln = l.get("lap_number", 0)
                if ln > lap_map.get(d, {}).get("lap_number", 0):
                    lap_map[d] = {
                        "lap_number":  ln,
                        "lap_time":    l.get("lap_duration"),
                        "tyre":        TYRE_MAP.get(l.get("compound", ""), "?"),
                        "tyre_age":    l.get("tyre_age_at_start", 0),
                        "is_pit_out":  l.get("is_pit_out_lap", False),
                        "sector1":     l.get("duration_sector_1"),
                        "sector2":     l.get("duration_sector_2"),
                        "sector3":     l.get("duration_sector_3"),
                    }

        # Total laps from session
        total_laps = session.get("total_laps") or 57
        current_lap = max((v.get("lap_number", 0) for v in lap_map.values()), default=0)

        # Get driver list from standings to enrich with names/teams
        drivers_info = await self._get_driver_info_of1()

        drivers = []
        for d_num, pos in sorted(pos_map.items(), key=lambda x: x[1]):
            d_info = drivers_info.get(str(d_num), {})
            lap_d = lap_map.get(d_num, {})
            car_d = car_map.get(d_num, {})
            iv = interval_map.get(d_num, {})
            pits = pit_map.get(d_num, [])

            lap_time_raw = lap_d.get("lap_time")
            lap_fmt = _fmt_laptime(lap_time_raw) if lap_time_raw else "--:--.---"

            team = d_info.get("team_name", "Unknown")
            drivers.append({
                "driver_number":  str(d_num),
                "position":       pos,
                "short_name":     d_info.get("name_acronym", str(d_num)),
                "full_name":      d_info.get("full_name", f"Driver {d_num}"),
                "team":           team,
                "color":          TEAM_COLORS.get(team, "#888888"),
                "gap":            _fmt_gap(iv.get("gap_to_leader"), pos),
                "interval":       _fmt_interval(iv.get("interval")),
                "tyre":           lap_d.get("tyre", "?"),
                "tyre_age":       lap_d.get("tyre_age", 0),
                "last_lap":       lap_fmt,
                "last_lap_raw":   lap_time_raw,
                "current_lap":    lap_d.get("lap_number", 0),
                "pit_stops":      len(pits),
                "pits":           pits,
                "speed":          car_d.get("speed", 0),
                "throttle":       car_d.get("throttle", 0),
                "brake":          car_d.get("brake", 0),
                "drs":            car_d.get("drs", False),
                "gear":           car_d.get("gear", 0),
                "rpm":            car_d.get("rpm", 0),
                "sector1":        lap_d.get("sector1"),
                "sector2":        lap_d.get("sector2"),
                "sector3":        lap_d.get("sector3"),
            })

        # Find fastest lap
        valid_laps = [d for d in drivers if d["last_lap_raw"]]
        if valid_laps:
            fastest = min(valid_laps, key=lambda x: x["last_lap_raw"])
            fastest["is_fastest_lap"] = True

        weather_latest = {}
        if weather:
            w = weather[-1]
            weather_latest = {
                "air_temp":    w.get("air_temperature"),
                "track_temp":  w.get("track_temperature"),
                "humidity":    w.get("humidity"),
                "rainfall":    w.get("rainfall"),
                "wind_speed":  w.get("wind_speed"),
            }

        return {
            "session_name":   session.get("session_name"),
            "meeting_name":   session.get("meeting_name"),
            "location":       session.get("location"),
            "circuit_key":    session.get("circuit_key"),
            "total_laps":     total_laps,
            "current_lap":    current_lap,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "drivers":        drivers,
            "weather":        weather_latest,
        }

    async def _get_driver_info_of1(self) -> dict:
        """Returns {driver_number: info_dict}"""
        data = await self._of1_get("/drivers", {"session_key": "latest"})
        if not data:
            return {}
        return {str(d["driver_number"]): d for d in data}

    # ── Drivers list ─────────────────────────────────────────────────────────
    async def get_drivers(self) -> list:
        data = await self._of1_get("/drivers", {"session_key": "latest"})
        return data or []

    # ── Historical FastF1 data ────────────────────────────────────────────────
    def _load_ff1_session(self, year: int, round_num: int, session_type: str = "R"):
        key = (year, round_num, session_type)
        if key not in self._session_cache:
            session = fastf1.get_session(year, round_num, session_type)
            session.load(telemetry=True, weather=False)
            self._session_cache[key] = session
        return self._session_cache[key]

    async def get_lap_times(self, year: int, round_num: int) -> dict:
        try:
            session = await asyncio.to_thread(self._load_ff1_session, year, round_num)
            laps = session.laps[["Driver", "LapNumber", "LapTime", "Compound",
                                  "TyreLife", "PitInTime", "PitOutTime"]].copy()
            laps["LapTimeSec"] = laps["LapTime"].dt.total_seconds()
            laps = laps.dropna(subset=["LapTimeSec"])
            result = {}
            for driver, grp in laps.groupby("Driver"):
                result[driver] = grp[["LapNumber", "LapTimeSec", "Compound", "TyreLife"]]\
                    .rename(columns={"LapNumber": "lap", "LapTimeSec": "time",
                                     "Compound": "compound", "TyreLife": "tyre_life"})\
                    .to_dict(orient="records")
            return {"year": year, "round": round_num, "lap_times": result}
        except Exception as e:
            logger.error(f"FastF1 lap times error: {e}")
            return {"error": str(e)}

    async def get_telemetry(self, year: int, round_num: int, driver: str) -> dict:
        try:
            session = await asyncio.to_thread(self._load_ff1_session, year, round_num)
            lap = session.laps.pick_driver(driver).pick_fastest()
            tel = lap.get_telemetry()
            # downsample to ~200 points for API response size
            step = max(1, len(tel) // 200)
            tel = tel.iloc[::step]
            return {
                "driver":    driver,
                "lap_time":  str(lap["LapTime"]),
                "telemetry": {
                    "distance":  tel["Distance"].tolist(),
                    "speed":     tel["Speed"].tolist(),
                    "throttle":  tel["Throttle"].tolist(),
                    "brake":     tel["Brake"].astype(int).tolist(),
                    "gear":      tel["nGear"].tolist(),
                    "rpm":       tel["RPM"].tolist(),
                    "drs":       tel["DRS"].tolist(),
                }
            }
        except Exception as e:
            logger.error(f"FastF1 telemetry error: {e}")
            return {"error": str(e)}

    async def get_tyre_strategy(self, year: int, round_num: int) -> dict:
        try:
            session = await asyncio.to_thread(self._load_ff1_session, year, round_num)
            laps = session.laps[["Driver", "LapNumber", "Compound", "TyreLife",
                                  "PitInTime", "Stint"]].copy()
            stints = laps.groupby(["Driver", "Stint", "Compound"]).agg(
                start_lap=("LapNumber", "min"),
                end_lap=("LapNumber", "max"),
            ).reset_index()
            result = {}
            for _, row in stints.iterrows():
                d = row["Driver"]
                result.setdefault(d, []).append({
                    "stint":    int(row["Stint"]),
                    "compound": row["Compound"],
                    "start":    int(row["start_lap"]),
                    "end":      int(row["end_lap"]),
                    "laps":     int(row["end_lap"] - row["start_lap"] + 1),
                })
            return {"year": year, "round": round_num, "strategies": result}
        except Exception as e:
            logger.error(f"FastF1 tyre strategy error: {e}")
            return {"error": str(e)}

    # ── Standings + Schedule (Jolpica/Ergast) ─────────────────────────────────
    async def get_driver_standings(self) -> dict:
        data = await self._jolpica_get("/current/driverStandings")
        if not data:
            return {}
        standings = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not standings:
            return {}
        return {
            "round":     standings[0].get("round"),
            "standings": [
                {
                    "position":   s["position"],
                    "driver":     f"{s['Driver']['givenName']} {s['Driver']['familyName']}",
                    "code":       s["Driver"]["code"],
                    "team":       s["Constructors"][0]["name"] if s.get("Constructors") else "",
                    "points":     float(s["points"]),
                    "wins":       int(s["wins"]),
                    "nationality": s["Driver"]["nationality"],
                }
                for s in standings[0]["DriverStandings"]
            ],
        }

    async def get_constructor_standings(self) -> dict:
        data = await self._jolpica_get("/current/constructorStandings")
        if not data:
            return {}
        standings = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not standings:
            return {}
        return {
            "standings": [
                {
                    "position": s["position"],
                    "team":     s["Constructor"]["name"],
                    "points":   float(s["points"]),
                    "wins":     int(s["wins"]),
                    "color":    TEAM_COLORS.get(s["Constructor"]["name"], "#888"),
                }
                for s in standings[0]["ConstructorStandings"]
            ]
        }

    async def get_schedule(self) -> dict:
        data = await self._jolpica_get("/current")
        if not data:
            return {}
        races = data["MRData"]["RaceTable"]["Races"]
        return {
            "season": data["MRData"]["RaceTable"]["season"],
            "races": [
                {
                    "round":    r["round"],
                    "name":     r["raceName"],
                    "circuit":  r["Circuit"]["circuitName"],
                    "country":  r["Circuit"]["Location"]["country"],
                    "date":     r["date"],
                    "time":     r.get("time", ""),
                }
                for r in races
            ],
        }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fmt_laptime(seconds: float | None) -> str:
    if seconds is None:
        return "--:--.---"
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:06.3f}"


def _fmt_gap(gap: float | str | None, pos: int) -> str:
    if pos == 1:
        return "LEADER"
    if gap is None:
        return "---"
    if isinstance(gap, str):
        return gap
    return f"+{gap:.3f}"


def _fmt_interval(iv: float | str | None) -> str:
    if iv is None:
        return "---"
    if isinstance(iv, str):
        return iv
    return f"+{iv:.3f}"
