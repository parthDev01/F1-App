"""
F1 Race Probability Engine
Exports: RaceState, DriverState, win_probability, podium_probability,
         safety_car_probability, driver_insights
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict

TYRE_LIFE = {"SOFT": 22, "MEDIUM": 36, "HARD": 52, "INTER": 30, "WET": 40}
TYRE_PACE = {"SOFT": 0.0, "MEDIUM": 0.4, "HARD": 0.9, "INTER": 3.5, "WET": 6.0}

CIRCUIT_SC_RATE = {
    "bahrain": 0.22, "jeddah": 0.38, "australia": 0.35, "albert_park": 0.35,
    "baku": 0.45, "miami": 0.28, "monaco": 0.42, "montreal": 0.31,
    "barcelona": 0.18, "red_bull_ring": 0.20, "silverstone": 0.25,
    "hungaroring": 0.19, "spa": 0.30, "zandvoort": 0.20, "monza": 0.24,
    "singapore": 0.50, "suzuka": 0.21, "austin": 0.27, "mexico_city": 0.22,
    "interlagos": 0.35, "las_vegas": 0.32, "losail": 0.24, "yas_marina": 0.18,
    "shanghai": 0.28, "madrid": 0.22, "default": 0.25,
}


@dataclass
class DriverState:
    driver_code: str
    position: int
    gap_to_leader: float = 0.0
    interval: float = 0.0
    tyre_compound: str = "MEDIUM"
    tyre_age: int = 1
    last_lap_time: float = 92.0
    best_lap_time: float = 91.5
    pit_stops: int = 0
    total_laps: int = 57
    laps_completed: int = 1
    team: str = ""
    drs_available: bool = False
    speed: float = 300.0
    throttle: float = 80.0
    brake: float = 0.0
    gear: int = 7
    rpm: int = 11000


@dataclass
class RaceState:
    circuit: str
    total_laps: int
    current_lap: int
    drivers: List[DriverState] = field(default_factory=list)
    weather: str = "dry"
    track_temp: float = 35.0
    air_temp: float = 24.0
    safety_car_active: bool = False
    vsc_active: bool = False


# ── Internal helpers ──────────────────────────────────────────────────────────

def _tyre_deg(compound: str, age: int) -> float:
    max_life = TYRE_LIFE.get(compound, 36)
    base     = TYRE_PACE.get(compound, 0.5)
    ratio    = age / max_life
    if ratio < 0.5:
        return round(base + ratio * 0.3, 3)
    elif ratio < 0.85:
        return round(base + 0.15 + (ratio - 0.5) * 1.2, 3)
    else:
        return round(base + 0.57 + (ratio - 0.85) * 4.0, 3)


def _pit_prob(d: DriverState, state: RaceState) -> float:
    remaining = max(0, TYRE_LIFE.get(d.tyre_compound, 36) - d.tyre_age)
    if remaining <= 0:   return 0.95
    elif remaining <= 3: return 0.75
    elif remaining <= 7: return 0.35
    else:                return 0.05


# ── Public API ────────────────────────────────────────────────────────────────

def win_probability(state: RaceState) -> Dict[str, float]:
    laps_left = state.total_laps - state.current_lap
    if laps_left <= 0:
        leader = min(state.drivers, key=lambda d: d.position, default=None)
        return {d.driver_code: (1.0 if leader and d.driver_code == leader.driver_code else 0.0) for d in state.drivers}

    scores = {}
    for d in state.drivers:
        # Gap penalty
        if d.position == 1:
            gap_score = 1.0
        else:
            laps_to_close = d.gap_to_leader / 0.1 if d.gap_to_leader else 9999
            gap_score = max(0.0, 1.0 - (laps_to_close / max(laps_left, 1)))

        # Pace score
        best_times = [x.best_lap_time for x in state.drivers if x.best_lap_time > 0]
        if best_times:
            field_best = min(best_times)
            pace_score = math.exp(-(d.best_lap_time - field_best) * 1.5)
        else:
            pace_score = 1.0 / max(len(state.drivers), 1)

        # Tyre score
        deg_now = _tyre_deg(d.tyre_compound, d.tyre_age)
        deg_end = _tyre_deg(d.tyre_compound, d.tyre_age + laps_left)
        tyre_score = math.exp(-((deg_now + deg_end) / 2) * 0.4)

        # Position bonus
        pos_score = 1.0 / (d.position ** 0.7)

        # Pit risk
        strategy_score = 1.0 - _pit_prob(d, state) * 0.15

        combined = (gap_score * 0.35 + pace_score * 0.25 +
                    tyre_score * 0.15 + pos_score * 0.15 + strategy_score * 0.10)
        scores[d.driver_code] = max(0.001, combined)

    total = sum(scores.values())
    return {k: round(v / total, 4) for k, v in scores.items()}


def podium_probability(state: RaceState) -> Dict[str, float]:
    win_probs = win_probability(state)
    result = {}
    for d in state.drivers:
        wp = win_probs.get(d.driver_code, 0)
        if   d.position == 1: p = 0.88 + wp * 0.10
        elif d.position == 2: p = 0.72 + wp * 0.10
        elif d.position == 3: p = 0.60 + wp * 0.08
        elif d.position <= 6: p = max(0.02, 0.25 - (d.position - 3) * 0.05 + wp * 0.20)
        else:                 p = max(0.005, wp * 0.15)
        result[d.driver_code] = round(min(p, 0.99), 3)
    return result


def safety_car_probability(state: RaceState) -> Dict[str, float]:
    laps_left    = state.total_laps - state.current_lap
    circuit_rate = CIRCUIT_SC_RATE.get(state.circuit.lower(), CIRCUIT_SC_RATE["default"])
    sc_base      = 1 - (1 - circuit_rate) ** max(laps_left / 10, 0.1)
    if state.weather == "damp": sc_base = min(0.95, sc_base * 1.6)
    elif state.weather == "wet": sc_base = min(0.98, sc_base * 2.2)
    return {
        "safety_car": round(min(sc_base, 0.95), 3),
        "red_flag":   round(min(sc_base * 0.28, 0.55), 3),
        "vsc":        round(min(sc_base * 0.55, 0.75), 3),
    }


def _overtake_scenarios(driver: DriverState, target: DriverState, state: RaceState) -> List[dict]:
    if not target or driver.position >= target.position:
        return []
    laps_left = state.total_laps - state.current_lap
    interval  = driver.interval
    sc_probs  = safety_car_probability(state)
    scenarios = []

    # Tyre delta
    driver_deg = _tyre_deg(driver.tyre_compound, driver.tyre_age)
    target_deg = _tyre_deg(target.tyre_compound, target.tyre_age)
    delta = target_deg - driver_deg
    if delta > 0.1:
        laps_to_close = interval / max(delta, 0.05)
        if laps_to_close <= laps_left:
            scenarios.append({
                "tag": "TYRE DELTA", "type": "opportunity",
                "title": f"{target.driver_code} tyre cliff in ~{max(1,int(laps_to_close))} laps",
                "body": f"{target.driver_code} on {target.tyre_age}-lap {target.tyre_compound.lower()}s losing ~{delta:.2f}s/lap. Gap closes to DRS by Lap {state.current_lap + max(1,int(laps_to_close))}.",
                "probability": round(min(0.78, 0.3 + delta * 0.6), 2),
            })

    # Pit stop
    target_pit = _pit_prob(target, state)
    if target_pit > 0.3:
        underover = "Undercut" if interval < 6 else "Overcut"
        scenarios.append({
            "tag": "PIT WINDOW", "type": "opportunity",
            "title": f"{underover} on {target.driver_code}'s stop",
            "body": f"{target.driver_code} likely stops within 5 laps ({int(target_pit*100)}% probability). A well-timed pit gains track position.",
            "probability": round(target_pit * 0.65, 2),
        })

    # DRS
    if interval < 2.5:
        drs_gain = 0.35 if state.circuit in ["baku","monza","spa","albert_park","shanghai"] else 0.22
        laps_needed = math.ceil(interval / max(drs_gain, 0.01))
        scenarios.append({
            "tag": "DRS ATTACK", "type": "opportunity",
            "title": f"DRS zone — close at 0.{int(drs_gain*100)}s/lap",
            "body": f"Inside DRS window. Speed advantage in detection zone. Overtake completable in ~{laps_needed} lap(s) with clean air into Turn 1.",
            "probability": round(min(0.6, drs_gain * 1.5), 2),
        })

    # SC reset
    if interval > 5:
        scenarios.append({
            "tag": "SC FACTOR", "type": "wildcard",
            "title": f"Safety car resets {interval:.1f}s gap to zero",
            "body": f"SC bunches the field instantly. On restart, {driver.driver_code} on {'fresher' if driver.tyre_age < target.tyre_age else 'comparable'} tyres attacks straight into T1.",
            "probability": round(sc_probs["safety_car"] * 0.55, 2),
        })

    # Threat from behind
    behind = next((x for x in state.drivers if x.position == driver.position + 1), None)
    if behind:
        behind_delta = driver_deg - _tyre_deg(behind.tyre_compound, behind.tyre_age)
        if behind_delta > 0.05:
            scenarios.append({
                "tag": "THREAT", "type": "risk",
                "title": f"{behind.driver_code} closing from P{behind.position} at {behind_delta:.2f}s/lap",
                "body": f"P{behind.position} {behind.driver_code} on {behind.tyre_compound.lower()} tyres is quicker. Defend or pit before the gap disappears.",
                "probability": round(min(0.55, behind_delta * 0.8), 2),
            })

    # Win path
    win_probs = win_probability(state)
    win_p = win_probs.get(driver.driver_code, 0)
    scenarios.append({
        "tag": "WIN PATH",
        "type": "risk" if win_p < 0.1 else "opportunity",
        "title": f"Win probability: {int(win_p*100)}%",
        "body": (f"Realistic ceiling: P{max(1, driver.position-1 if win_p > 0.15 else driver.position)} today. Need {driver.position-1} car(s) ahead to have issues."
                 if win_p < 0.3 else
                 f"Genuine race win contender. Clean strategy and no incidents puts {driver.driver_code} in the fight."),
        "probability": round(win_p, 2),
    })

    return scenarios[:5]


def driver_insights(driver_code: str, state: RaceState) -> dict:
    driver = next((d for d in state.drivers if d.driver_code == driver_code), None)
    if not driver:
        return {"error": f"Driver {driver_code} not found in current race state"}

    target   = next((d for d in state.drivers if d.position == driver.position - 1), None)
    win_probs = win_probability(state)
    pod_probs = podium_probability(state)
    scenarios = _overtake_scenarios(driver, target, state)

    if not scenarios or all(s["type"] not in ("opportunity",) for s in scenarios):
        deg = _tyre_deg(driver.tyre_compound, driver.tyre_age)
        remaining = max(0, TYRE_LIFE.get(driver.tyre_compound, 36) - driver.tyre_age)
        scenarios.insert(0, {
            "tag": "STATUS", "type": "info",
            "title": f"P{driver.position} — {'managing pace' if deg > 0.5 else 'strong pace'}",
            "body": f"{driver.tyre_compound.title()} tyres at {driver.tyre_age} laps. Deg penalty: +{deg:.2f}s/lap. ~{remaining} laps remaining on current compound.",
            "probability": None,
        })

    return {
        "driver_code":        driver_code,
        "win_probability":    round(win_probs.get(driver_code, 0), 4),
        "podium_probability": round(pod_probs.get(driver_code, 0), 4),
        "tyre_deg":           round(_tyre_deg(driver.tyre_compound, driver.tyre_age), 3),
        "laps_on_tyre":       driver.tyre_age,
        "pit_probability_5":  round(_pit_prob(driver, state), 3),
        "scenarios":          scenarios,
    }
