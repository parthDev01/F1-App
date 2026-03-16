"""
ProbabilityEngine — computes race win probabilities + tactical insights.

Model inputs:
  - Current gap to leader
  - Tyre compound + age (deg model)
  - Pit stop count + pit window estimate
  - Track position × pace
  - Safety car base rate (Bahrain ~23%)
  - Remaining laps

This is a heuristic model designed for real-time fan insight.
Not a full Monte Carlo sim, but produces realistic outputs.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

# Tyre degradation model: compound → (peak_laps, deg_per_lap_after_peak)
TYRE_DEG = {
    "S": {"peak": 15, "cliff": 20, "deg": 0.08},
    "M": {"peak": 25, "cliff": 35, "deg": 0.05},
    "H": {"peak": 40, "cliff": 55, "deg": 0.03},
    "I": {"peak": 30, "cliff": 45, "deg": 0.06},
    "W": {"peak": 35, "cliff": 50, "deg": 0.04},
    "?": {"peak": 20, "cliff": 30, "deg": 0.06},
}

# Average pit stop window for remaining laps heuristic
PIT_WINDOW_BUFFER = 6  # laps before cliff to ideally pit

SC_BASE_PROB = 0.23    # Bahrain historical SC rate per race
RF_BASE_PROB = 0.08    # Red flag
VSC_BASE_PROB = 0.15   # VSC

# Gap in seconds that makes overtaking feasible in open air
DRS_WINDOW = 1.0
ATTACK_WINDOW = 2.5
COMFORTABLE_GAP = 5.0


@dataclass
class DriverState:
    number: str
    position: int
    short_name: str
    full_name: str
    team: str
    gap_raw: Optional[float]        # seconds behind leader, None for leader
    tyre: str
    tyre_age: int
    last_lap_raw: Optional[float]
    pit_stops: int
    current_lap: int


class ProbabilityEngine:

    def compute(self, state: dict) -> dict:
        """Compute all probabilities from live state dict."""
        drivers_raw = state.get("drivers", [])
        total_laps = state.get("total_laps", 57)
        current_lap = state.get("current_lap", 1)
        remaining = max(1, total_laps - current_lap)

        drivers = [self._parse_driver(d) for d in drivers_raw]
        if not drivers:
            return {}

        # Compute relative pace score per driver
        pace_scores = self._pace_scores(drivers)

        # Tyre health scores
        tyre_scores = {d.number: self._tyre_score(d.tyre, d.tyre_age) for d in drivers}

        # Gap scores (closer = harder to win, but also position effect)
        raw_win = {}
        for d in drivers:
            gap_pen = 0.0
            if d.gap_raw is not None:
                # Exponential penalty on gap
                gap_pen = math.exp(-d.gap_raw / 30.0)
            else:
                gap_pen = 1.0  # leader

            pos_factor = math.exp(-0.28 * (d.position - 1))
            pace = pace_scores.get(d.number, 0.5)
            tyre = tyre_scores.get(d.number, 0.5)

            # SC wild-card: adds random-redistribution factor based on SC prob
            sc_uplift = SC_BASE_PROB * (1 / max(d.position, 1)) * 0.3

            score = (gap_pen * 0.45 + pos_factor * 0.30 + pace * 0.15 + tyre * 0.10) + sc_uplift
            raw_win[d.number] = max(0.001, score)

        # Normalise to 100%
        total = sum(raw_win.values())
        win_probs = {k: round(v / total * 100, 1) for k, v in raw_win.items()}

        # Podium probabilities (top-3 chance)
        pod_probs = {}
        for d in drivers:
            pos_factor = math.exp(-0.18 * (d.position - 1))
            pace = pace_scores.get(d.number, 0.5)
            tyre = tyre_scores.get(d.number, 0.5)
            sc_factor = SC_BASE_PROB * (1 / max(d.position - 1, 1)) * 0.15
            raw = pos_factor * 0.55 + pace * 0.25 + tyre * 0.20 + sc_factor
            pod_probs[d.number] = raw

        pod_total = sum(pod_probs.values())
        pod_probs = {k: min(99, round(v / pod_total * 3 * 100, 0)) for k, v in pod_probs.items()}

        # Incident probabilities — modulated by remaining laps
        sc_prob = round(min(65, SC_BASE_PROB * 100 * (1 - current_lap / total_laps * 0.4)), 0)
        rf_prob = round(min(30, RF_BASE_PROB * 100 * (1 - current_lap / total_laps * 0.3)), 0)
        vsc_prob = round(min(40, VSC_BASE_PROB * 100 * (1 - current_lap / total_laps * 0.2)), 0)

        # Fastest-lap contender
        fl_candidates = sorted(drivers, key=lambda d: pace_scores.get(d.number, 0), reverse=True)[:3]

        # Pit windows
        pit_windows = {}
        for d in drivers:
            pw = self._pit_window(d, remaining, total_laps)
            if pw:
                pit_windows[d.number] = pw

        return {
            "win":         win_probs,
            "podium":      pod_probs,
            "sc_prob":     int(sc_prob),
            "rf_prob":     int(rf_prob),
            "vsc_prob":    int(vsc_prob),
            "fl_candidates": [d.short_name for d in fl_candidates],
            "pit_windows": pit_windows,
        }

    def driver_insights(self, driver_number: str, state: dict, probs: dict) -> dict:
        """Generate tactical insight cards for a specific driver."""
        drivers_raw = state.get("drivers", [])
        total_laps = state.get("total_laps", 57)
        current_lap = state.get("current_lap", 1)
        remaining = max(1, total_laps - current_lap)

        drivers = {d["driver_number"]: self._parse_driver(d) for d in drivers_raw}
        driver = drivers.get(driver_number)
        if not driver:
            return {"error": "Driver not found"}

        win_pct = probs.get("win", {}).get(driver_number, 0)
        pod_pct = probs.get("podium", {}).get(driver_number, 0)
        sc_prob = probs.get("sc_prob", 23)
        pit_window = probs.get("pit_windows", {}).get(driver_number)

        # Driver ahead/behind
        ahead = next((d for d in drivers.values() if d.position == driver.position - 1), None)
        behind = next((d for d in drivers.values() if d.position == driver.position + 1), None)

        # Tyre health
        tyre_health = self._tyre_score(driver.tyre, driver.tyre_age)
        deg = TYRE_DEG.get(driver.tyre, TYRE_DEG["?"])
        laps_until_cliff = max(0, deg["cliff"] - driver.tyre_age)

        scenarios = []

        # ── Card 1: Current status ────────────────────────────────────────────
        if driver.position == 1:
            gap_ahead_txt = "Leading the race."
            margin_txt = f"Gap to P2: {abs(behind.gap_raw - (driver.gap_raw or 0)):.1f}s." if behind and behind.gap_raw else ""
            scenarios.append({
                "tag": "STATUS", "type": "info",
                "title": f"Race leader — managing from the front",
                "body": f"{gap_ahead_txt} {margin_txt} Tyre age at {driver.tyre_age} laps on {driver.tyre} compound.",
                "prob": None,
            })
        else:
            gap_s = driver.gap_raw or 0
            gap_txt = f"{gap_s:.1f}s behind leader"
            iv_txt = f", {(driver.gap_raw or 0) - (ahead.gap_raw or 0):.1f}s to P{ahead.position}" if ahead and ahead.gap_raw is not None else ""
            tyre_txt = f"{driver.tyre} tyres at {driver.tyre_age} laps"
            scenarios.append({
                "tag": "STATUS", "type": "info",
                "title": f"P{driver.position} — {gap_txt}",
                "body": f"{gap_txt}{iv_txt}. {tyre_txt}. {remaining} laps remaining.",
                "prob": None,
            })

        # ── Card 2: Tyre / threat ─────────────────────────────────────────────
        if tyre_health < 0.4:
            scenarios.append({
                "tag": "TYRE RISK", "type": "risk",
                "title": f"{driver.tyre} compound approaching cliff",
                "body": f"At {driver.tyre_age} laps, {driver.short_name} is ~{laps_until_cliff} laps from the degradation cliff. Lap times will begin to fall, opening the door for undercut.",
                "prob": f"{min(75, 100 - int(tyre_health * 100))}%",
            })
        elif ahead and laps_until_cliff < 8:
            scenarios.append({
                "tag": "ATTACK", "type": "opportunity",
                "title": f"Tyre delta opens attack window in ~{laps_until_cliff} laps",
                "body": f"{driver.short_name}'s fresher tyres will outpace P{ahead.position} once their compound starts degrading. Gap can close by 0.2–0.4s per lap.",
                "prob": f"{min(55, int((1 - tyre_health) * 80))}%",
            })

        # ── Card 3: Pit stop window ───────────────────────────────────────────
        if pit_window:
            scenarios.append({
                "tag": "PIT WINDOW", "type": "warning",
                "title": f"Optimal stop: Laps {pit_window[0]}–{pit_window[1]}",
                "body": self._pit_narrative(driver, ahead, pit_window),
                "prob": None,
            })

        # ── Card 4: Safety car scenario ───────────────────────────────────────
        sc_pos_gain = max(0, driver.position - 2)  # best realistic gain
        scenarios.append({
            "tag": "SC FACTOR", "type": "opportunity" if driver.position > 3 else "warning",
            "title": "Safety car compresses field to zero",
            "body": f"With {sc_prob}% SC probability, any neutralisation removes {driver.gap_raw:.1f}s gap instantly." if driver.gap_raw else f"SC probability at {sc_prob}%. Would create sprint-to-finish from current P{driver.position}.",
            "prob": f"{sc_prob}%",
        })

        # ── Card 5: Direct threat or opportunity ─────────────────────────────
        if behind:
            gap_behind = abs((driver.gap_raw or 0) - (behind.gap_raw or 0)) if behind.gap_raw else None
            if gap_behind is not None:
                if gap_behind < DRS_WINDOW:
                    behind_tyre = TYRE_DEG.get(behind.tyre, TYRE_DEG["?"])
                    behind_health = self._tyre_score(behind.tyre, behind.tyre_age)
                    scenarios.append({
                        "tag": "THREAT", "type": "risk",
                        "title": f"{behind.short_name} in DRS range — defend required",
                        "body": f"P{behind.position} is {gap_behind:.2f}s behind and within DRS activation. {behind.short_name} on {behind.tyre} tyres ({behind.tyre_age} laps) — {'fresher compound, pace advantage' if behind_health > 0.7 else 'similar tyre age'}.",
                        "prob": f"{min(65, int((1 - gap_behind / DRS_WINDOW) * 60))}%",
                    })
                elif gap_behind < ATTACK_WINDOW:
                    scenarios.append({
                        "tag": "MONITOR", "type": "warning",
                        "title": f"{behind.short_name} closing — {gap_behind:.1f}s back",
                        "body": f"P{behind.position} closing at current pace. Will enter DRS range in ~{max(1, int(gap_behind / 0.3))} laps if pace differential continues.",
                        "prob": None,
                    })

        if ahead:
            gap_ahead = abs((driver.gap_raw or 0) - (ahead.gap_raw or 0)) if ahead.gap_raw is not None and driver.gap_raw is not None else None
            if gap_ahead is not None and gap_ahead < ATTACK_WINDOW:
                ahead_tyre_cliff = max(0, TYRE_DEG.get(ahead.tyre, TYRE_DEG["?"])["cliff"] - ahead.tyre_age)
                scenarios.append({
                    "tag": "OPPORTUNITY", "type": "opportunity",
                    "title": f"{gap_ahead:.1f}s to P{ahead.position} — inside attack window",
                    "body": f"{ahead.short_name} on {ahead.tyre} ({ahead.tyre_age} laps). Their deg cliff arrives in ~{ahead_tyre_cliff} laps. {driver.short_name} can attack into Turn 1 or via undercut at pit window.",
                    "prob": f"{min(55, int(40 * (1 - gap_ahead / ATTACK_WINDOW)))}%",
                })

        # ── Card 6: Win probability card ─────────────────────────────────────
        if driver.position == 1:
            wp_body = f"Full race control. Needs clean pit stop and no mechanical issues to seal victory."
        elif win_pct >= 15:
            wp_body = f"Realistic contender. Strategy + pace delta are the key variables over the next {min(remaining, 20)} laps."
        elif win_pct >= 5:
            wp_body = f"Requires P1/P2 to make errors or have an incident. SC + undercut strategy = best path to podium."
        else:
            wp_body = f"From P{driver.position}, win requires significant chaos ahead. Best focus: protect current position and maximise points."

        scenarios.append({
            "tag": "WIN PATH", "type": "opportunity" if win_pct >= 15 else "risk",
            "title": f"{win_pct}% race win probability",
            "body": wp_body,
            "prob": f"{win_pct}%",
        })

        return {
            "driver_number": driver_number,
            "short_name":    driver.short_name,
            "full_name":     driver.full_name,
            "team":          driver.team,
            "position":      driver.position,
            "win_prob":      win_pct,
            "podium_prob":   int(pod_pct),
            "tyre_health":   round(tyre_health, 2),
            "laps_to_cliff": laps_until_cliff,
            "scenarios":     scenarios[:6],  # max 6 cards
        }

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _parse_driver(self, d: dict) -> DriverState:
        gap_raw = None
        gap_str = d.get("gap", "")
        if gap_str and gap_str not in ("LEADER", "---"):
            try:
                gap_raw = float(gap_str.replace("+", "").replace("LAP", "60"))
            except ValueError:
                pass
        return DriverState(
            number=d.get("driver_number", "?"),
            position=d.get("position", 99),
            short_name=d.get("short_name", "???"),
            full_name=d.get("full_name", ""),
            team=d.get("team", ""),
            gap_raw=gap_raw,
            tyre=d.get("tyre", "?"),
            tyre_age=d.get("tyre_age", 0),
            last_lap_raw=d.get("last_lap_raw"),
            pit_stops=d.get("pit_stops", 0),
            current_lap=d.get("current_lap", 0),
        )

    def _tyre_score(self, compound: str, age: int) -> float:
        """Returns 0 (dead) to 1 (fresh) tyre health score."""
        deg = TYRE_DEG.get(compound, TYRE_DEG["?"])
        if age <= deg["peak"]:
            return 1.0
        if age >= deg["cliff"]:
            return max(0.05, 1.0 - (age - deg["cliff"]) * deg["deg"] * 3)
        ratio = (age - deg["peak"]) / (deg["cliff"] - deg["peak"])
        return max(0.1, 1.0 - ratio * 0.7)

    def _pace_scores(self, drivers: list[DriverState]) -> dict:
        """Normalised pace score based on latest lap time."""
        valid = [(d.number, d.last_lap_raw) for d in drivers if d.last_lap_raw]
        if not valid:
            return {d.number: 0.5 for d in drivers}
        times = [t for _, t in valid]
        best, worst = min(times), max(times)
        spread = max(worst - best, 0.001)
        scores = {num: 1.0 - (t - best) / spread for num, t in valid}
        for d in drivers:
            if d.number not in scores:
                scores[d.number] = 0.3
        return scores

    def _pit_window(self, driver: DriverState, remaining: int, total_laps: int) -> tuple | None:
        """Returns (lap_from, lap_to) for optimal pit window, or None if already pitted optimally."""
        deg = TYRE_DEG.get(driver.tyre, TYRE_DEG["?"])
        laps_to_cliff = max(0, deg["cliff"] - driver.tyre_age)
        current = total_laps - remaining

        if laps_to_cliff <= 0:
            # Should already be pitting
            return (current + 1, current + 3)
        if laps_to_cliff > remaining:
            # Can potentially one-stop
            return None
        ideal_lap = current + max(1, laps_to_cliff - PIT_WINDOW_BUFFER)
        return (ideal_lap, ideal_lap + 4)

    def _pit_narrative(self, driver: DriverState, ahead, pit_window: tuple) -> str:
        lap_from, lap_to = pit_window
        if ahead:
            return (
                f"Best pit window is Laps {lap_from}–{lap_to}. "
                f"If {ahead.short_name} pits 1 lap later, {driver.short_name} can emerge ahead on fresher rubber "
                f"with ~2–3s clear air — classic undercut opportunity."
            )
        return (
            f"Optimal stop between Laps {lap_from}–{lap_to} to take on fresh rubber for the final stint. "
            f"Staying out risks a lap-time cliff dropping pace by 0.3–0.8s per lap."
        )
