"""
F1 Tracker — FastAPI Backend
Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Optional, Set

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from live_data import build_race_state, get_latest_session
from calendar_2026 import (
    get_race_status, CALENDAR_2026, LAST_RACE_RESULTS,
    STANDINGS_2026, CONSTRUCTOR_STANDINGS_2026
)
from probability import (
    RaceState, DriverState,
    win_probability, podium_probability, safety_car_probability, driver_insights,
)
import f1_data as ff1

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
log = logging.getLogger("f1.main")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))


class AppState:
    race_state: dict = {}
    last_poll: float = 0.0
    clients: Set[WebSocket] = set()
    total_laps: int = 57

app_state = AppState()


def build_between_races_state() -> dict:
    """State served when no race is live — shows last race + next race info."""
    status = get_race_status()
    return {
        "mode":          "between_races",
        "demo_mode":     False,
        "is_live":       False,
        "race_status":   status,
        "last_race":     LAST_RACE_RESULTS,
        "next_race":     status.get("next_race"),
        "days_until_next": status.get("days_until_next"),
        "standings":     STANDINGS_2026,
        "constructors":  CONSTRUCTOR_STANDINGS_2026,
        "calendar":      CALENDAR_2026,
        "drivers":       [],
        "current_lap":   0,
        "total_laps":    0,
        "circuit":       status.get("last_race", {}).get("circuit", "shanghai"),
        "circuit_name":  status.get("last_race", {}).get("circuit_name", ""),
        "weather":       "dry",
        "safety_car":    False,
        "vsc":           False,
        "track_temp":    25,
        "air_temp":      20,
    }


def dict_to_race_state(raw: dict) -> RaceState:
    drivers = []
    total_laps = raw.get("total_laps", app_state.total_laps)
    for d in raw.get("drivers", []):
        drivers.append(DriverState(
            driver_code=d["driver_code"],
            position=d["position"],
            gap_to_leader=d.get("gap_to_leader", 0.0),
            interval=d.get("interval", 0.0),
            tyre_compound=d.get("tyre_compound", "MEDIUM"),
            tyre_age=d.get("tyre_age", 1),
            last_lap_time=d.get("last_lap_time", 92.0),
            best_lap_time=d.get("best_lap_time", 91.5),
            pit_stops=d.get("pit_stops", 0),
            total_laps=total_laps,
            laps_completed=d.get("laps_completed", raw.get("current_lap", 1)),
            team=d.get("team", ""),
            speed=d.get("speed", 300.0),
            throttle=d.get("throttle", 80.0),
            brake=d.get("brake", 0.0),
        ))
    return RaceState(
        circuit=raw.get("circuit", "unknown"),
        total_laps=total_laps,
        current_lap=raw.get("current_lap", 1),
        drivers=drivers,
        weather=raw.get("weather", "dry"),
        track_temp=raw.get("track_temp", 35.0),
        air_temp=raw.get("air_temp", 24.0),
        safety_car_active=raw.get("safety_car", False),
        vsc_active=raw.get("vsc", False),
    )


def enrich_with_probabilities(raw: dict) -> dict:
    if not raw.get("drivers"):
        return raw
    try:
        rs = dict_to_race_state(raw)
        win_probs = win_probability(rs)
        pod_probs = podium_probability(rs)
        sc_probs  = safety_car_probability(rs)
        for d in raw.get("drivers", []):
            code = d["driver_code"]
            d["win_probability"]    = win_probs.get(code, 0.0)
            d["podium_probability"] = pod_probs.get(code, 0.0)
        raw["incident_probability"] = sc_probs
    except Exception as e:
        log.warning(f"Probability enrichment failed: {e}")
    return raw


async def poll_live_data():
    async with httpx.AsyncClient() as client:
        while True:
            try:
                status = get_race_status()

                if status["is_live"]:
                    # Try OpenF1 live data
                    session = await get_latest_session(client)
                    if session:
                        app_state.total_laps = status["active_race"].get("total_laps", 57)
                        raw = await build_race_state(session["session_key"])
                        raw["circuit"]       = status["active_race"]["circuit"]
                        raw["circuit_name"]  = status["active_race"]["circuit_name"]
                        raw["total_laps"]    = app_state.total_laps
                        raw["is_live"]       = True
                        raw["demo_mode"]     = False
                        raw["race_status"]   = status
                        raw["next_race"]     = status.get("next_race")
                        raw["standings"]     = STANDINGS_2026
                        raw["constructors"]  = CONSTRUCTOR_STANDINGS_2026
                        app_state.race_state = enrich_with_probabilities(raw)
                    else:
                        app_state.race_state = build_between_races_state()
                else:
                    app_state.race_state = build_between_races_state()

                app_state.last_poll = time.time()

                # Broadcast to WebSocket clients
                if app_state.clients:
                    msg = json.dumps({"type": "race_update", "data": app_state.race_state})
                    dead = set()
                    for ws in app_state.clients:
                        try:
                            await ws.send_text(msg)
                        except Exception:
                            dead.add(ws)
                    app_state.clients -= dead

            except Exception as e:
                log.error(f"Poll error: {e}")

            await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise with between-races state immediately
    app_state.race_state = build_between_races_state()
    task = asyncio.create_task(poll_live_data())
    yield
    task.cancel()


app = FastAPI(title="F1 Tracker API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "F1 Tracker API running", "docs": "/docs"}


@app.get("/api/race")
async def get_race():
    return enrich_with_probabilities(app_state.race_state.copy())


@app.get("/api/status")
async def get_status():
    """Current race weekend status — live / between races / next race countdown."""
    return get_race_status()


@app.get("/api/calendar")
async def get_calendar():
    return {"season": 2026, "rounds": len(CALENDAR_2026), "calendar": CALENDAR_2026}


@app.get("/api/standings")
async def get_standings():
    return {
        "season": 2026,
        "after_round": LAST_RACE_RESULTS["round"],
        "drivers":      STANDINGS_2026,
        "constructors": CONSTRUCTOR_STANDINGS_2026,
    }


@app.get("/api/last-race")
async def get_last_race():
    return LAST_RACE_RESULTS


@app.get("/api/driver/{driver_code}/insights")
async def get_driver_insights(driver_code: str):
    rs = dict_to_race_state(app_state.race_state)
    if not rs.drivers:
        return {"error": "No live race data available"}
    return driver_insights(driver_code.upper(), rs)


@app.get("/api/season/{year}/schedule")
async def get_schedule(year: int):
    if year == 2026:
        return {"year": 2026, "schedule": CALENDAR_2026}
    schedule = ff1.get_race_schedule(year)
    return {"year": year, "schedule": schedule}


@app.get("/api/session/{year}/{round_name}/laps")
async def get_session_laps(year: int, round_name: str, session_type: str = Query("R")):
    session = ff1.get_session(year, round_name, session_type)
    return {"laps": ff1.get_lap_times(session)}


@app.get("/api/session/{year}/{round_name}/fastest")
async def get_fastest(year: int, round_name: str, session_type: str = Query("R")):
    session = ff1.get_session(year, round_name, session_type)
    return {"fastest_laps": ff1.get_fastest_laps(session)}


@app.get("/api/session/{year}/{round_name}/strategy")
async def get_strategy(year: int, round_name: str):
    session = ff1.get_session(year, round_name, "R")
    return {"strategies": ff1.get_tyre_strategies(session)}


@app.get("/api/session/{year}/{round_name}/positions")
async def get_positions_hist(year: int, round_name: str):
    session = ff1.get_session(year, round_name, "R")
    return {"positions": ff1.get_position_history(session)}


@app.get("/api/probabilities")
async def get_probabilities():
    rs = dict_to_race_state(app_state.race_state)
    if not rs.drivers:
        return {"error": "No live race in progress"}
    return {
        "win":       win_probability(rs),
        "podium":    podium_probability(rs),
        "incidents": safety_car_probability(rs),
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    app_state.clients.add(ws)
    log.info(f"WS connected. Total: {len(app_state.clients)}")
    try:
        await ws.send_text(json.dumps({
            "type": "race_update",
            "data": enrich_with_probabilities(app_state.race_state.copy()),
        }))
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.warning(f"WS error: {e}")
    finally:
        app_state.clients.discard(ws)
