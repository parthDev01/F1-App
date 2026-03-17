"""
F1 2026 Calendar + Live Results
- Fetches from Jolpica API (free, no key)
- Falls back to hardcoded data if API unreachable
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
import httpx

log = logging.getLogger("f1.calendar")
JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"

TEAM_COLORS = {
    "Red Bull": "#3671C6", "Red Bull Racing": "#3671C6",
    "Mercedes": "#27F4D2",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Aston Martin": "#358C75",
    "Alpine": "#0093CC", "Alpine F1 Team": "#0093CC",
    "Williams": "#005AFF",
    "RB": "#5E8FAA", "AlphaTauri": "#5E8FAA", "Racing Bulls": "#5E8FAA",
    "Kick Sauber": "#52E252", "Sauber": "#52E252", "Audi": "#C6C6C6",
    "Haas": "#B6BABD", "Haas F1 Team": "#B6BABD",
}

CALENDAR_2026: List[Dict] = [
    {"round":1,  "name":"Australian Grand Prix",    "circuit":"albert_park",   "circuit_name":"Albert Park Circuit",            "country":"Australia",   "city":"Melbourne",    "race_date":"2026-03-08T05:00:00Z","sprint":False},
    {"round":2,  "name":"Chinese Grand Prix",       "circuit":"shanghai",      "circuit_name":"Shanghai International Circuit", "country":"China",       "city":"Shanghai",     "race_date":"2026-03-15T07:00:00Z","sprint":True},
    {"round":3,  "name":"Japanese Grand Prix",      "circuit":"suzuka",        "circuit_name":"Suzuka International Racing Course","country":"Japan",    "city":"Suzuka",       "race_date":"2026-03-29T05:00:00Z","sprint":False},
    {"round":4,  "name":"Miami Grand Prix",         "circuit":"miami",         "circuit_name":"Miami International Autodrome",  "country":"USA",         "city":"Miami",        "race_date":"2026-05-03T19:00:00Z","sprint":True},
    {"round":5,  "name":"Canadian Grand Prix",      "circuit":"montreal",      "circuit_name":"Circuit Gilles Villeneuve",      "country":"Canada",      "city":"Montreal",     "race_date":"2026-05-24T18:00:00Z","sprint":True},
    {"round":6,  "name":"Monaco Grand Prix",        "circuit":"monaco",        "circuit_name":"Circuit de Monaco",              "country":"Monaco",      "city":"Monte Carlo",  "race_date":"2026-06-07T13:00:00Z","sprint":False},
    {"round":7,  "name":"Spanish Grand Prix",       "circuit":"barcelona",     "circuit_name":"Circuit de Barcelona-Catalunya", "country":"Spain",       "city":"Barcelona",    "race_date":"2026-06-14T13:00:00Z","sprint":False},
    {"round":8,  "name":"Austrian Grand Prix",      "circuit":"red_bull_ring", "circuit_name":"Red Bull Ring",                  "country":"Austria",     "city":"Spielberg",    "race_date":"2026-06-28T13:00:00Z","sprint":False},
    {"round":9,  "name":"British Grand Prix",       "circuit":"silverstone",   "circuit_name":"Silverstone Circuit",            "country":"UK",          "city":"Silverstone",  "race_date":"2026-07-05T14:00:00Z","sprint":True},
    {"round":10, "name":"Belgian Grand Prix",       "circuit":"spa",           "circuit_name":"Circuit de Spa-Francorchamps",   "country":"Belgium",     "city":"Spa",          "race_date":"2026-07-19T13:00:00Z","sprint":False},
    {"round":11, "name":"Hungarian Grand Prix",     "circuit":"hungaroring",   "circuit_name":"Hungaroring",                    "country":"Hungary",     "city":"Budapest",     "race_date":"2026-07-26T13:00:00Z","sprint":False},
    {"round":12, "name":"Dutch Grand Prix",         "circuit":"zandvoort",     "circuit_name":"Circuit Zandvoort",              "country":"Netherlands", "city":"Zandvoort",    "race_date":"2026-08-23T13:00:00Z","sprint":True},
    {"round":13, "name":"Italian Grand Prix",       "circuit":"monza",         "circuit_name":"Autodromo Nazionale Monza",      "country":"Italy",       "city":"Monza",        "race_date":"2026-09-06T13:00:00Z","sprint":False},
    {"round":14, "name":"Madrid Grand Prix",        "circuit":"madrid",        "circuit_name":"Madring Street Circuit",          "country":"Spain",       "city":"Madrid",       "race_date":"2026-09-13T13:00:00Z","sprint":False},
    {"round":15, "name":"Azerbaijan Grand Prix",    "circuit":"baku",          "circuit_name":"Baku City Circuit",              "country":"Azerbaijan",  "city":"Baku",         "race_date":"2026-09-26T11:00:00Z","sprint":False},
    {"round":16, "name":"Singapore Grand Prix",     "circuit":"singapore",     "circuit_name":"Marina Bay Street Circuit",      "country":"Singapore",   "city":"Singapore",    "race_date":"2026-10-11T12:00:00Z","sprint":True},
    {"round":17, "name":"United States Grand Prix", "circuit":"austin",        "circuit_name":"Circuit of the Americas",        "country":"USA",         "city":"Austin",       "race_date":"2026-10-25T19:00:00Z","sprint":False},
    {"round":18, "name":"Mexico City Grand Prix",   "circuit":"mexico_city",   "circuit_name":"Autodromo Hermanos Rodriguez",   "country":"Mexico",      "city":"Mexico City",  "race_date":"2026-11-01T20:00:00Z","sprint":False},
    {"round":19, "name":"São Paulo Grand Prix",     "circuit":"interlagos",    "circuit_name":"Autodromo Jose Carlos Pace",     "country":"Brazil",      "city":"São Paulo",    "race_date":"2026-11-08T17:00:00Z","sprint":False},
    {"round":20, "name":"Las Vegas Grand Prix",     "circuit":"las_vegas",     "circuit_name":"Las Vegas Strip Circuit",        "country":"USA",         "city":"Las Vegas",    "race_date":"2026-11-21T06:00:00Z","sprint":False},
    {"round":21, "name":"Qatar Grand Prix",         "circuit":"losail",        "circuit_name":"Lusail International Circuit",   "country":"Qatar",       "city":"Lusail",       "race_date":"2026-11-29T17:00:00Z","sprint":False},
    {"round":22, "name":"Abu Dhabi Grand Prix",     "circuit":"yas_marina",    "circuit_name":"Yas Marina Circuit",             "country":"UAE",         "city":"Abu Dhabi",    "race_date":"2026-12-06T13:00:00Z","sprint":False},
]

# Track historical data: last 5 winners + lap record
TRACK_HISTORY = {
    "albert_park":  {"lap_record":{"driver":"Charles Leclerc","team":"Ferrari","time":"1:19.813","year":2022},"past_winners":[{"year":2025,"driver":"Lando Norris","team":"McLaren"},{"year":2024,"driver":"Carlos Sainz","team":"Ferrari"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Charles Leclerc","team":"Ferrari"},{"year":2019,"driver":"Valtteri Bottas","team":"Mercedes"}]},
    "shanghai":     {"lap_record":{"driver":"Michael Schumacher","team":"Ferrari","time":"1:32.238","year":2004},"past_winners":[{"year":2025,"driver":"Lando Norris","team":"McLaren"},{"year":2024,"driver":"Max Verstappen","team":"Red Bull"},{"year":2019,"driver":"Lewis Hamilton","team":"Mercedes"},{"year":2018,"driver":"Daniel Ricciardo","team":"Red Bull"},{"year":2017,"driver":"Lewis Hamilton","team":"Mercedes"}]},
    "suzuka":       {"lap_record":{"driver":"Kimi Räikkönen","team":"Ferrari","time":"1:31.540","year":2005},"past_winners":[{"year":2025,"driver":"Max Verstappen","team":"Red Bull"},{"year":2024,"driver":"Max Verstappen","team":"Red Bull"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2019,"driver":"Valtteri Bottas","team":"Mercedes"}]},
    "miami":        {"lap_record":{"driver":"Max Verstappen","team":"Red Bull","time":"1:29.708","year":2023},"past_winners":[{"year":2025,"driver":"Max Verstappen","team":"Red Bull"},{"year":2024,"driver":"Lando Norris","team":"McLaren"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"N/A","team":"N/A"}]},
    "montreal":     {"lap_record":{"driver":"Valtteri Bottas","team":"Mercedes","time":"1:13.078","year":2019},"past_winners":[{"year":2025,"driver":"Max Verstappen","team":"Red Bull"},{"year":2024,"driver":"Max Verstappen","team":"Red Bull"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2019,"driver":"Lewis Hamilton","team":"Mercedes"}]},
    "monaco":       {"lap_record":{"driver":"Lando Norris","team":"McLaren","time":"1:10.342","year":2024},"past_winners":[{"year":2025,"driver":"Charles Leclerc","team":"Ferrari"},{"year":2024,"driver":"Charles Leclerc","team":"Ferrari"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Sergio Perez","team":"Red Bull"},{"year":2021,"driver":"Max Verstappen","team":"Red Bull"}]},
    "barcelona":    {"lap_record":{"driver":"Max Verstappen","team":"Red Bull","time":"1:12.876","year":2023},"past_winners":[{"year":2025,"driver":"George Russell","team":"Mercedes"},{"year":2024,"driver":"Max Verstappen","team":"Red Bull"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Lewis Hamilton","team":"Mercedes"}]},
    "red_bull_ring":{"lap_record":{"driver":"Carlos Sainz","team":"Ferrari","time":"1:05.619","year":2020},"past_winners":[{"year":2025,"driver":"Max Verstappen","team":"Red Bull"},{"year":2024,"driver":"Max Verstappen","team":"Red Bull"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Charles Leclerc","team":"Ferrari"},{"year":2021,"driver":"Max Verstappen","team":"Red Bull"}]},
    "silverstone":  {"lap_record":{"driver":"Max Verstappen","team":"Red Bull","time":"1:27.097","year":2020},"past_winners":[{"year":2025,"driver":"Lando Norris","team":"McLaren"},{"year":2024,"driver":"Lewis Hamilton","team":"Mercedes"},{"year":2023,"driver":"Lewis Hamilton","team":"Mercedes"},{"year":2022,"driver":"Carlos Sainz","team":"Ferrari"},{"year":2021,"driver":"Lewis Hamilton","team":"Mercedes"}]},
    "spa":          {"lap_record":{"driver":"Valtteri Bottas","team":"Mercedes","time":"1:46.286","year":2018},"past_winners":[{"year":2025,"driver":"George Russell","team":"Mercedes"},{"year":2024,"driver":"Lewis Hamilton","team":"Mercedes"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Max Verstappen","team":"Red Bull"}]},
    "hungaroring":  {"lap_record":{"driver":"Lewis Hamilton","team":"Mercedes","time":"1:16.627","year":2020},"past_winners":[{"year":2025,"driver":"Oscar Piastri","team":"McLaren"},{"year":2024,"driver":"Oscar Piastri","team":"McLaren"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Esteban Ocon","team":"Alpine"}]},
    "zandvoort":    {"lap_record":{"driver":"Max Verstappen","team":"Red Bull","time":"1:11.097","year":2021},"past_winners":[{"year":2025,"driver":"Lando Norris","team":"McLaren"},{"year":2024,"driver":"Lando Norris","team":"McLaren"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Max Verstappen","team":"Red Bull"}]},
    "monza":        {"lap_record":{"driver":"Rubens Barrichello","team":"Ferrari","time":"1:21.046","year":2004},"past_winners":[{"year":2025,"driver":"Charles Leclerc","team":"Ferrari"},{"year":2024,"driver":"Charles Leclerc","team":"Ferrari"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Daniel Ricciardo","team":"McLaren"}]},
    "madrid":       {"lap_record":{"driver":"TBD","team":"TBD","time":"TBD","year":2026},"past_winners":[{"year":2026,"driver":"First ever race","team":"—"}]},
    "baku":         {"lap_record":{"driver":"Charles Leclerc","team":"Ferrari","time":"1:43.009","year":2019},"past_winners":[{"year":2025,"driver":"Charles Leclerc","team":"Ferrari"},{"year":2024,"driver":"Oscar Piastri","team":"McLaren"},{"year":2023,"driver":"Sergio Perez","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Sergio Perez","team":"Red Bull"}]},
    "singapore":    {"lap_record":{"driver":"Lewis Hamilton","team":"Mercedes","time":"1:35.867","year":2023},"past_winners":[{"year":2025,"driver":"Lando Norris","team":"McLaren"},{"year":2024,"driver":"Lando Norris","team":"McLaren"},{"year":2023,"driver":"Carlos Sainz","team":"Ferrari"},{"year":2022,"driver":"Sergio Perez","team":"Red Bull"},{"year":2021,"driver":"Sergio Perez","team":"Red Bull"}]},
    "austin":       {"lap_record":{"driver":"Charles Leclerc","team":"Ferrari","time":"1:36.169","year":2019},"past_winners":[{"year":2025,"driver":"Carlos Sainz","team":"Ferrari"},{"year":2024,"driver":"Max Verstappen","team":"Red Bull"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Max Verstappen","team":"Red Bull"}]},
    "mexico_city":  {"lap_record":{"driver":"Valtteri Bottas","team":"Mercedes","time":"1:17.774","year":2021},"past_winners":[{"year":2025,"driver":"Carlos Sainz","team":"Ferrari"},{"year":2024,"driver":"Carlos Sainz","team":"Ferrari"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Max Verstappen","team":"Red Bull"}]},
    "interlagos":   {"lap_record":{"driver":"Valtteri Bottas","team":"Mercedes","time":"1:10.540","year":2018},"past_winners":[{"year":2025,"driver":"Max Verstappen","team":"Red Bull"},{"year":2024,"driver":"Max Verstappen","team":"Red Bull"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"George Russell","team":"Mercedes"},{"year":2021,"driver":"Lewis Hamilton","team":"Mercedes"}]},
    "las_vegas":    {"lap_record":{"driver":"Oscar Piastri","team":"McLaren","time":"1:31.270","year":2024},"past_winners":[{"year":2025,"driver":"Carlos Sainz","team":"Ferrari"},{"year":2024,"driver":"Carlos Sainz","team":"Ferrari"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"N/A","team":"N/A"},{"year":2021,"driver":"N/A","team":"N/A"}]},
    "losail":       {"lap_record":{"driver":"Max Verstappen","team":"Red Bull","time":"1:24.319","year":2023},"past_winners":[{"year":2025,"driver":"Max Verstappen","team":"Red Bull"},{"year":2024,"driver":"Max Verstappen","team":"Red Bull"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Lewis Hamilton","team":"Mercedes"},{"year":2020,"driver":"N/A","team":"N/A"}]},
    "yas_marina":   {"lap_record":{"driver":"Max Verstappen","team":"Red Bull","time":"1:26.103","year":2021},"past_winners":[{"year":2025,"driver":"Lando Norris","team":"McLaren"},{"year":2024,"driver":"Lando Norris","team":"McLaren"},{"year":2023,"driver":"Max Verstappen","team":"Red Bull"},{"year":2022,"driver":"Max Verstappen","team":"Red Bull"},{"year":2021,"driver":"Max Verstappen","team":"Red Bull"}]},
}

# Fallback data
FALLBACK_LAST_RACE = {
    "round":2,"name":"Chinese Grand Prix","circuit":"shanghai",
    "circuit_name":"Shanghai International Circuit","date":"2026-03-15",
    "total_laps":56,"weather":"dry",
    "podium":[
        {"pos":1,"driver":"ANT","full_name":"Kimi Antonelli","team":"Mercedes","team_color":"#27F4D2","time":"1:33:15.607","points":25},
        {"pos":2,"driver":"RUS","full_name":"George Russell","team":"Mercedes","team_color":"#27F4D2","time":"+5.515","points":18},
        {"pos":3,"driver":"HAM","full_name":"Lewis Hamilton","team":"Ferrari","team_color":"#E8002D","time":"+15.519","points":15},
    ],
    "results":[
        {"pos":1,"driver":"ANT","full_name":"Kimi Antonelli","team":"Mercedes","team_color":"#27F4D2","points":25,"time":"1:33:15.607"},
        {"pos":2,"driver":"RUS","full_name":"George Russell","team":"Mercedes","team_color":"#27F4D2","points":18,"time":"+5.515"},
        {"pos":3,"driver":"HAM","full_name":"Lewis Hamilton","team":"Ferrari","team_color":"#E8002D","points":15,"time":"+15.519"},
        {"pos":4,"driver":"NOR","full_name":"Lando Norris","team":"McLaren","team_color":"#FF8000","points":12,"time":"+28.341"},
        {"pos":5,"driver":"LEC","full_name":"Charles Leclerc","team":"Ferrari","team_color":"#E8002D","points":10,"time":"+35.742"},
        {"pos":6,"driver":"PIA","full_name":"Oscar Piastri","team":"McLaren","team_color":"#FF8000","points":8,"time":"+48.203"},
        {"pos":7,"driver":"VER","full_name":"Max Verstappen","team":"Red Bull Racing","team_color":"#3671C6","points":6,"time":"+55.112"},
        {"pos":8,"driver":"ALO","full_name":"Fernando Alonso","team":"Aston Martin","team_color":"#358C75","points":4,"time":"+68.445"},
        {"pos":9,"driver":"GAS","full_name":"Pierre Gasly","team":"Alpine","team_color":"#0093CC","points":2,"time":"+75.221"},
        {"pos":10,"driver":"STR","full_name":"Lance Stroll","team":"Aston Martin","team_color":"#358C75","points":1,"time":"+82.334"},
        {"pos":11,"driver":"TSU","full_name":"Yuki Tsunoda","team":"Red Bull Racing","team_color":"#3671C6","points":0,"time":"+89.112"},
        {"pos":12,"driver":"ALB","full_name":"Alexander Albon","team":"Williams","team_color":"#005AFF","points":0,"time":"+95.443"},
        {"pos":13,"driver":"HUL","full_name":"Nico Hulkenberg","team":"Audi","team_color":"#C6C6C6","points":0,"time":"+102.221"},
        {"pos":14,"driver":"SAI","full_name":"Carlos Sainz","team":"Williams","team_color":"#005AFF","points":0,"time":"+108.334"},
        {"pos":15,"driver":"OCO","full_name":"Esteban Ocon","team":"Haas","team_color":"#B6BABD","points":0,"time":"DNF"},
    ],
    "fastest_lap":{"driver":"NOR","time":"1:35.412"},
}

FALLBACK_STANDINGS = [
    {"pos":1,"driver":"RUS","full_name":"George Russell","team":"Mercedes","team_color":"#27F4D2","pts":43,"wins":1},
    {"pos":2,"driver":"ANT","full_name":"Kimi Antonelli","team":"Mercedes","team_color":"#27F4D2","pts":37,"wins":1},
    {"pos":3,"driver":"LEC","full_name":"Charles Leclerc","team":"Ferrari","team_color":"#E8002D","pts":30,"wins":0},
    {"pos":4,"driver":"HAM","full_name":"Lewis Hamilton","team":"Ferrari","team_color":"#E8002D","pts":27,"wins":0},
    {"pos":5,"driver":"NOR","full_name":"Lando Norris","team":"McLaren","team_color":"#FF8000","pts":24,"wins":0},
    {"pos":6,"driver":"PIA","full_name":"Oscar Piastri","team":"McLaren","team_color":"#FF8000","pts":16,"wins":0},
    {"pos":7,"driver":"VER","full_name":"Max Verstappen","team":"Red Bull Racing","team_color":"#3671C6","pts":14,"wins":0},
    {"pos":8,"driver":"ALO","full_name":"Fernando Alonso","team":"Aston Martin","team_color":"#358C75","pts":10,"wins":0},
    {"pos":9,"driver":"GAS","full_name":"Pierre Gasly","team":"Alpine","team_color":"#0093CC","pts":6,"wins":0},
    {"pos":10,"driver":"STR","full_name":"Lance Stroll","team":"Aston Martin","team_color":"#358C75","pts":5,"wins":0},
    {"pos":11,"driver":"TSU","full_name":"Yuki Tsunoda","team":"Red Bull Racing","team_color":"#3671C6","pts":4,"wins":0},
    {"pos":12,"driver":"HUL","full_name":"Nico Hulkenberg","team":"Audi","team_color":"#C6C6C6","pts":3,"wins":0},
    {"pos":13,"driver":"ALB","full_name":"Alexander Albon","team":"Williams","team_color":"#005AFF","pts":2,"wins":0},
    {"pos":14,"driver":"SAI","full_name":"Carlos Sainz","team":"Williams","team_color":"#005AFF","pts":1,"wins":0},
]

FALLBACK_CONSTRUCTORS = [
    {"pos":1,"team":"Mercedes","color":"#27F4D2","pts":80},
    {"pos":2,"team":"Ferrari","color":"#E8002D","pts":57},
    {"pos":3,"team":"McLaren","color":"#FF8000","pts":40},
    {"pos":4,"team":"Aston Martin","color":"#358C75","pts":15},
    {"pos":5,"team":"Red Bull Racing","color":"#3671C6","pts":14},
    {"pos":6,"team":"Alpine","color":"#0093CC","pts":8},
    {"pos":7,"team":"Audi","color":"#C6C6C6","pts":4},
    {"pos":8,"team":"Williams","color":"#005AFF","pts":3},
]

_cache: Dict = {"last_race":None,"standings":None,"constructors":None,"fetched_at":0}
CACHE_TTL = 1800

def _circuit_key(name: str) -> str:
    m = {"Australian":"albert_park","Chinese":"shanghai","Japanese":"suzuka","Miami":"miami",
         "Canadian":"montreal","Monaco":"monaco","Spanish":"barcelona","Austrian":"red_bull_ring",
         "British":"silverstone","Belgian":"spa","Hungarian":"hungaroring","Dutch":"zandvoort",
         "Italian":"monza","Madrid":"madrid","Azerbaijan":"baku","Singapore":"singapore",
         "United States":"austin","Mexico City":"mexico_city","São Paulo":"interlagos",
         "Las Vegas":"las_vegas","Qatar":"losail","Abu Dhabi":"yas_marina"}
    for k,v in m.items():
        if k.lower() in name.lower(): return v
    return "unknown"

async def _fetch_last_race() -> Optional[Dict]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Get all 2026 results and take the last one
            r = await client.get(f"{JOLPICA_BASE}/2026/results.json?limit=100")
            r.raise_for_status()
            data  = r.json()
            races = data.get("MRData",{}).get("RaceTable",{}).get("Races",[])
            if not races:
                return None
            race = races[-1]  # Last completed race
            raw  = race.get("Results",[])
            results = []
            for x in raw:
                drv  = x.get("Driver",{})
                con  = x.get("Constructor",{})
                team = con.get("name","")
                code = drv.get("code", drv.get("driverId","???").upper()[:3])
                t    = x.get("Time",{}).get("time") or x.get("status","")
                results.append({
                    "pos":       int(x.get("position",99)),
                    "driver":    code,
                    "full_name": f"{drv.get('givenName','')} {drv.get('familyName','')}".strip(),
                    "team":      team,
                    "team_color":TEAM_COLORS.get(team,"#888"),
                    "points":    int(float(x.get("points",0))),
                    "time":      t,
                    "laps":      int(x.get("laps",0)),
                    "grid":      int(x.get("grid",0)),
                    "status":    x.get("status",""),
                    "nationality": drv.get("nationality",""),
                    "dob":       drv.get("dateOfBirth",""),
                })
            fastest = None
            for x in raw:
                fl = x.get("FastestLap",{})
                if fl.get("rank") == "1":
                    fastest = {"driver": x.get("Driver",{}).get("code","?"), "time": fl.get("Time",{}).get("time","")}
                    break
            podium = [dict(r) for r in results if r["pos"] <= 3]
            return {
                "round":        int(race.get("round",0)),
                "name":         race.get("raceName",""),
                "circuit":      _circuit_key(race.get("raceName","")),
                "circuit_name": race.get("Circuit",{}).get("circuitName",""),
                "date":         race.get("date",""),
                "total_laps":   max((x.get("laps",0) for x in results),default=0),
                "weather":      "dry",
                "podium":       podium,
                "results":      results,
                "fastest_lap":  fastest,
            }
    except Exception as e:
        log.warning(f"Jolpica last race failed: {e}")
        return None

async def _fetch_driver_standings() -> Optional[List]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{JOLPICA_BASE}/2026/driverStandings.json")
            r.raise_for_status()
            sl = r.json().get("MRData",{}).get("StandingsTable",{}).get("StandingsLists",[])
            if not sl: return None
            out = []
            for i,d in enumerate(sl[0].get("DriverStandings",[])):
                drv  = d.get("Driver",{})
                con  = d.get("Constructors",[{}])[0]
                team = con.get("name","")
                code = drv.get("code", drv.get("driverId","???").upper()[:3])
                out.append({
                    "pos":        i+1,
                    "driver":     code,
                    "full_name":  f"{drv.get('givenName','')} {drv.get('familyName','')}".strip(),
                    "team":       team,
                    "team_color": TEAM_COLORS.get(team,"#888"),
                    "pts":        int(float(d.get("points",0))),
                    "wins":       int(d.get("wins",0)),
                    "nationality": drv.get("nationality",""),
                    "dob":        drv.get("dateOfBirth",""),
                })
            return out
    except Exception as e:
        log.warning(f"Jolpica standings failed: {e}")
        return None

async def _fetch_constructor_standings() -> Optional[List]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{JOLPICA_BASE}/2026/constructorStandings.json")
            r.raise_for_status()
            sl = r.json().get("MRData",{}).get("StandingsTable",{}).get("StandingsLists",[])
            if not sl: return None
            out = []
            for i,c in enumerate(sl[0].get("ConstructorStandings",[])):
                con  = c.get("Constructor",{})
                name = con.get("name","")
                out.append({"pos":i+1,"team":name,"color":TEAM_COLORS.get(name,"#888"),
                            "pts":int(float(c.get("points",0))),"wins":int(c.get("wins",0))})
            return out
    except Exception as e:
        log.warning(f"Jolpica constructors failed: {e}")
        return None

async def refresh_live_data():
    import time
    now = time.time()
    if _cache["last_race"] and (now - _cache["fetched_at"]) < CACHE_TTL:
        return
    log.info("Refreshing from Jolpica...")
    lr, st, con = await asyncio.gather(
        _fetch_last_race(), _fetch_driver_standings(), _fetch_constructor_standings(),
        return_exceptions=True
    )
    _cache["last_race"]    = (None if isinstance(lr,Exception)  else lr)  or FALLBACK_LAST_RACE
    _cache["standings"]    = (None if isinstance(st,Exception)  else st)  or FALLBACK_STANDINGS
    _cache["constructors"] = (None if isinstance(con,Exception) else con) or FALLBACK_CONSTRUCTORS
    _cache["fetched_at"]   = now
    log.info(f"Refreshed — last race: Round {_cache['last_race'].get('round','?')} {_cache['last_race'].get('name','')}")

def get_last_race_results() -> Dict:  return _cache["last_race"]    or FALLBACK_LAST_RACE
def get_standings()         -> List:  return _cache["standings"]    or FALLBACK_STANDINGS
def get_constructor_standings() -> List: return _cache["constructors"] or FALLBACK_CONSTRUCTORS
def get_track_history(circuit: str) -> Dict: return TRACK_HISTORY.get(circuit, {})

def get_now() -> datetime: return datetime.now(timezone.utc)

def get_race_status() -> Dict:
    now = get_now()
    last_race = next_race = None
    for race in CALENDAR_2026:
        dt = datetime.fromisoformat(race["race_date"].replace("Z","+00:00"))
        if dt < now: last_race = race
        elif next_race is None: next_race = race
    is_live = is_weekend = False
    if next_race:
        dt = datetime.fromisoformat(next_race["race_date"].replace("Z","+00:00"))
        diff = (dt - now).total_seconds() / 3600
        if -2.0 <= diff <= 1.5: is_live = True
        if -72 <= diff <= 4:    is_weekend = True
    days_until = None
    if next_race and not is_live:
        dt = datetime.fromisoformat(next_race["race_date"].replace("Z","+00:00"))
        days_until = max(0, int((dt - now).total_seconds() / 86400))
    return {"is_live":is_live,"is_weekend":is_weekend,"last_race":last_race,"next_race":next_race,
            "days_until_next":days_until,"season_round":last_race["round"] if last_race else 0,"total_rounds":len(CALENDAR_2026)}


# ── Lap-by-lap replay data ────────────────────────────────────────────────────

_replay_cache: Dict = {"data": None, "round": None, "fetched_at": 0}
REPLAY_TTL = 3600  # 1 hour

async def _fetch_lap_positions(year: int, round_num: int) -> Optional[Dict]:
    """
    Fetch lap-by-lap position for every driver from Jolpica.
    Returns dict: { lap_number: [ {driver, position, code, team_color}, ... ] }
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Fetch all laps (limit 2000 covers ~57 laps × 20 drivers = 1140 rows)
            r = await client.get(
                f"{JOLPICA_BASE}/{year}/{round_num}/laps.json?limit=2000"
            )
            r.raise_for_status()
            data  = r.json()
            races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            if not races:
                return None

            laps_raw = races[0].get("Laps", [])
            if not laps_raw:
                return None

            # Also get driver → team mapping from standings
            standings = get_standings()
            driver_meta = {d["driver"]: d for d in standings}

            lap_map: Dict[int, list] = {}
            for lap_entry in laps_raw:
                lap_num  = int(lap_entry.get("number", 0))
                timings  = lap_entry.get("Timings", [])
                lap_data = []
                for t in timings:
                    code = t.get("driverId", "").upper()[:3]
                    # Jolpica uses full driverId like "max_verstappen"
                    # Convert to 3-letter code
                    did  = t.get("driverId", "")
                    # Try to match against our standings
                    meta = None
                    for s in standings:
                        if s["driver"].lower() == code.lower():
                            meta = s
                            break
                        # Also try matching by last name fragment
                        if did and s["full_name"].lower().replace(" ","_") in did.lower():
                            meta = s
                            break

                    lap_data.append({
                        "driver":     code,
                        "driver_id":  did,
                        "position":   int(t.get("position", 20)),
                        "lap_time":   t.get("time", ""),
                        "team_color": meta["team_color"] if meta else "#888888",
                        "full_name":  meta["full_name"]  if meta else code,
                        "team":       meta["team"]       if meta else "",
                    })
                # Sort by position
                lap_data.sort(key=lambda x: x["position"])
                lap_map[lap_num] = lap_data

            return lap_map

    except Exception as e:
        log.warning(f"Lap position fetch failed: {e}")
        return None


async def get_replay_data() -> Optional[Dict]:
    """Returns cached replay data, refreshing if stale."""
    import time
    last = get_last_race_results()
    round_num = last.get("round", 0)
    now = time.time()

    if (
        _replay_cache["data"] is not None
        and _replay_cache["round"] == round_num
        and (now - _replay_cache["fetched_at"]) < REPLAY_TTL
    ):
        return _replay_cache["data"]

    log.info(f"Fetching lap replay data for Round {round_num}...")
    lap_data = await _fetch_lap_positions(2026, round_num)

    if lap_data:
        _replay_cache["data"]       = lap_data
        _replay_cache["round"]      = round_num
        _replay_cache["fetched_at"] = now
        log.info(f"Replay data: {len(lap_data)} laps loaded")
    else:
        log.warning("Lap data unavailable, replay will use synthetic data")

    return _replay_cache["data"]
