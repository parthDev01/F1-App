"""
F1 Tracker — FastAPI Backend
Open-source stack: FastF1 (MIT), OpenF1 API (free public), FastAPI (MIT)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import logging
from contextlib import asynccontextmanager

from f1_data import F1DataService
from probability import ProbabilityEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting F1 Tracker backend...")
    app.state.f1 = F1DataService()
    app.state.prob = ProbabilityEngine()
    task = asyncio.create_task(live_poll_loop(app))
    yield
    task.cancel()
    logger.info("Shutdown complete.")


app = FastAPI(title="F1 Tracker API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket Connection Manager ──────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


# ── Background live polling ───────────────────────────────────────────────────
async def live_poll_loop(app: FastAPI):
    """Poll OpenF1 every 4s during live session, broadcast to all WS clients."""
    while True:
        try:
            if manager.active:
                state = await app.state.f1.get_live_state()
                if state:
                    state["probabilities"] = app.state.prob.compute(state)
                    await manager.broadcast({"type": "live_update", "data": state})
        except Exception as e:
            logger.warning(f"Poll loop error: {e}")
        await asyncio.sleep(4)


# ── REST Endpoints ────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "F1 Tracker API running", "docs": "/docs"}


@app.get("/api/session/current")
async def current_session():
    return await app.state.f1.get_current_session()


@app.get("/api/live")
async def live_state():
    state = await app.state.f1.get_live_state()
    if state:
        state["probabilities"] = app.state.prob.compute(state)
    return JSONResponse(state or {"error": "No active session"})


@app.get("/api/drivers")
async def get_drivers():
    return await app.state.f1.get_drivers()


@app.get("/api/driver/{driver_number}/insights")
async def driver_insights(driver_number: str):
    state = await app.state.f1.get_live_state()
    if not state:
        return {"error": "No active session"}
    probs = app.state.prob.compute(state)
    return app.state.prob.driver_insights(driver_number, state, probs)


@app.get("/api/standings/drivers")
async def driver_standings():
    return await app.state.f1.get_driver_standings()


@app.get("/api/standings/constructors")
async def constructor_standings():
    return await app.state.f1.get_constructor_standings()


@app.get("/api/schedule")
async def race_schedule():
    return await app.state.f1.get_schedule()


@app.get("/api/session/{year}/{round_num}/lap_times")
async def lap_times(year: int, round_num: int):
    return await app.state.f1.get_lap_times(year, round_num)


@app.get("/api/session/{year}/{round_num}/telemetry/{driver}")
async def telemetry(year: int, round_num: int, driver: str):
    return await app.state.f1.get_telemetry(year, round_num, driver)


@app.get("/api/session/{year}/{round_num}/tyre_strategy")
async def tyre_strategy(year: int, round_num: int):
    return await app.state.f1.get_tyre_strategy(year, round_num)


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await manager.connect(ws)
    try:
        # Send current snapshot immediately on connect
        state = await app.state.f1.get_live_state()
        if state:
            state["probabilities"] = app.state.prob.compute(state)
            await ws.send_json({"type": "live_update", "data": state})
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(ws)
