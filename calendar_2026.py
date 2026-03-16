"""
2026 F1 Season Calendar
Bahrain (Rd 4) and Saudi Arabia (Rd 5) cancelled due to Middle East conflict.
Source: formula1.com / ESPN / Sky Sports - confirmed 22-race season.
All times are race start times in UTC.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, List

CALENDAR_2026: List[Dict] = [
    {"round": 1,  "name": "Australian Grand Prix",    "circuit": "albert_park",    "circuit_name": "Albert Park Circuit",          "country": "Australia",    "city": "Melbourne",    "race_date": "2026-03-08T05:00:00Z", "sprint": False},
    {"round": 2,  "name": "Chinese Grand Prix",       "circuit": "shanghai",       "circuit_name": "Shanghai International Circuit","country": "China",        "city": "Shanghai",     "race_date": "2026-03-15T07:00:00Z", "sprint": True},
    {"round": 3,  "name": "Japanese Grand Prix",      "circuit": "suzuka",         "circuit_name": "Suzuka International Racing Course","country": "Japan",   "city": "Suzuka",       "race_date": "2026-03-29T05:00:00Z", "sprint": False},
    {"round": 4,  "name": "Miami Grand Prix",         "circuit": "miami",          "circuit_name": "Miami International Autodrome", "country": "USA",          "city": "Miami",        "race_date": "2026-05-03T19:00:00Z", "sprint": True},
    {"round": 5,  "name": "Canadian Grand Prix",      "circuit": "montreal",       "circuit_name": "Circuit Gilles Villeneuve",     "country": "Canada",       "city": "Montreal",     "race_date": "2026-05-24T18:00:00Z", "sprint": True},
    {"round": 6,  "name": "Monaco Grand Prix",        "circuit": "monaco",         "circuit_name": "Circuit de Monaco",             "country": "Monaco",       "city": "Monte Carlo",  "race_date": "2026-06-07T13:00:00Z", "sprint": False},
    {"round": 7,  "name": "Spanish Grand Prix",       "circuit": "barcelona",      "circuit_name": "Circuit de Barcelona-Catalunya","country": "Spain",        "city": "Barcelona",    "race_date": "2026-06-14T13:00:00Z", "sprint": False},
    {"round": 8,  "name": "Austrian Grand Prix",      "circuit": "red_bull_ring",  "circuit_name": "Red Bull Ring",                 "country": "Austria",      "city": "Spielberg",    "race_date": "2026-06-28T13:00:00Z", "sprint": False},
    {"round": 9,  "name": "British Grand Prix",       "circuit": "silverstone",    "circuit_name": "Silverstone Circuit",           "country": "UK",           "city": "Silverstone",  "race_date": "2026-07-05T14:00:00Z", "sprint": True},
    {"round": 10, "name": "Belgian Grand Prix",       "circuit": "spa",            "circuit_name": "Circuit de Spa-Francorchamps",  "country": "Belgium",      "city": "Spa",          "race_date": "2026-07-19T13:00:00Z", "sprint": False},
    {"round": 11, "name": "Hungarian Grand Prix",     "circuit": "hungaroring",    "circuit_name": "Hungaroring",                   "country": "Hungary",      "city": "Budapest",     "race_date": "2026-07-26T13:00:00Z", "sprint": False},
    {"round": 12, "name": "Dutch Grand Prix",         "circuit": "zandvoort",      "circuit_name": "Circuit Zandvoort",             "country": "Netherlands",  "city": "Zandvoort",    "race_date": "2026-08-23T13:00:00Z", "sprint": True},
    {"round": 13, "name": "Italian Grand Prix",       "circuit": "monza",          "circuit_name": "Autodromo Nazionale Monza",     "country": "Italy",        "city": "Monza",        "race_date": "2026-09-06T13:00:00Z", "sprint": False},
    {"round": 14, "name": "Madrid Grand Prix",        "circuit": "madrid",         "circuit_name": "Madring Street Circuit",         "country": "Spain",        "city": "Madrid",       "race_date": "2026-09-13T13:00:00Z", "sprint": False},
    {"round": 15, "name": "Azerbaijan Grand Prix",    "circuit": "baku",           "circuit_name": "Baku City Circuit",             "country": "Azerbaijan",   "city": "Baku",         "race_date": "2026-09-26T11:00:00Z", "sprint": False},
    {"round": 16, "name": "Singapore Grand Prix",     "circuit": "singapore",      "circuit_name": "Marina Bay Street Circuit",     "country": "Singapore",    "city": "Singapore",    "race_date": "2026-10-11T12:00:00Z", "sprint": True},
    {"round": 17, "name": "United States Grand Prix", "circuit": "austin",         "circuit_name": "Circuit of the Americas",       "country": "USA",          "city": "Austin",       "race_date": "2026-10-25T19:00:00Z", "sprint": False},
    {"round": 18, "name": "Mexico City Grand Prix",   "circuit": "mexico_city",    "circuit_name": "Autodromo Hermanos Rodriguez",  "country": "Mexico",       "city": "Mexico City",  "race_date": "2026-11-01T20:00:00Z", "sprint": False},
    {"round": 19, "name": "São Paulo Grand Prix",     "circuit": "interlagos",     "circuit_name": "Autodromo Jose Carlos Pace",    "country": "Brazil",       "city": "São Paulo",    "race_date": "2026-11-08T17:00:00Z", "sprint": False},
    {"round": 20, "name": "Las Vegas Grand Prix",     "circuit": "las_vegas",      "circuit_name": "Las Vegas Strip Circuit",       "country": "USA",          "city": "Las Vegas",    "race_date": "2026-11-21T06:00:00Z", "sprint": False},
    {"round": 21, "name": "Qatar Grand Prix",         "circuit": "losail",         "circuit_name": "Lusail International Circuit",  "country": "Qatar",        "city": "Lusail",       "race_date": "2026-11-29T17:00:00Z", "sprint": False},
    {"round": 22, "name": "Abu Dhabi Grand Prix",     "circuit": "yas_marina",     "circuit_name": "Yas Marina Circuit",            "country": "UAE",          "city": "Abu Dhabi",    "race_date": "2026-12-06T13:00:00Z", "sprint": False},
]

# Last race results - updated after each race
# China GP results (Round 2, March 15 2026)
LAST_RACE_RESULTS = {
    "round": 2,
    "name": "Chinese Grand Prix",
    "circuit": "shanghai",
    "circuit_name": "Shanghai International Circuit",
    "date": "2026-03-15",
    "podium": [
        {"pos": 1, "driver": "ANT", "full_name": "Kimi Antonelli",    "team": "Mercedes",        "team_color": "#27F4D2", "time": "1:33:15.607", "points": 25},
        {"pos": 2, "driver": "RUS", "full_name": "George Russell",    "team": "Mercedes",        "team_color": "#27F4D2", "time": "+5.515",      "points": 18},
        {"pos": 3, "driver": "HAM", "full_name": "Lewis Hamilton",    "team": "Ferrari",         "team_color": "#E8002D", "time": "+15.519",     "points": 15},
    ],
    "results": [
        {"pos": 1,  "driver": "ANT", "full_name": "Kimi Antonelli",    "team": "Mercedes",        "team_color": "#27F4D2", "points": 25},
        {"pos": 2,  "driver": "RUS", "full_name": "George Russell",    "team": "Mercedes",        "team_color": "#27F4D2", "points": 18},
        {"pos": 3,  "driver": "HAM", "full_name": "Lewis Hamilton",    "team": "Ferrari",         "team_color": "#E8002D", "points": 15},
        {"pos": 4,  "driver": "NOR", "full_name": "Lando Norris",      "team": "McLaren",         "team_color": "#FF8000", "points": 12},
        {"pos": 5,  "driver": "LEC", "full_name": "Charles Leclerc",   "team": "Ferrari",         "team_color": "#E8002D", "points": 10},
        {"pos": 6,  "driver": "PIA", "full_name": "Oscar Piastri",     "team": "McLaren",         "team_color": "#FF8000", "points": 8},
        {"pos": 7,  "driver": "VER", "full_name": "Max Verstappen",    "team": "Red Bull Racing", "team_color": "#3671C6", "points": 6},
        {"pos": 8,  "driver": "ALO", "full_name": "Fernando Alonso",   "team": "Aston Martin",    "team_color": "#358C75", "points": 4},
        {"pos": 9,  "driver": "GAS", "full_name": "Pierre Gasly",      "team": "Alpine",          "team_color": "#0093CC", "points": 2},
        {"pos": 10, "driver": "STR", "full_name": "Lance Stroll",      "team": "Aston Martin",    "team_color": "#358C75", "points": 1},
    ],
    "fastest_lap": {"driver": "NOR", "time": "1:35.412"},
    "total_laps": 56,
    "weather": "dry",
}

# 2026 WDC standings after Round 2
STANDINGS_2026 = [
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
    {"pos": 11, "driver": "TSU", "full_name": "Yuki Tsunoda",       "team": "Red Bull Racing", "team_color": "#3671C6", "pts": 4,  "wins": 0},
    {"pos": 12, "driver": "HUL", "full_name": "Nico Hulkenberg",    "team": "Audi",            "team_color": "#C6C6C6", "pts": 3,  "wins": 0},
    {"pos": 13, "driver": "ALB", "full_name": "Alexander Albon",    "team": "Williams",        "team_color": "#005AFF", "pts": 2,  "wins": 0},
    {"pos": 14, "driver": "SAI", "full_name": "Carlos Sainz",       "team": "Williams",        "team_color": "#005AFF", "pts": 1,  "wins": 0},
]

CONSTRUCTOR_STANDINGS_2026 = [
    {"pos": 1, "team": "Mercedes",        "color": "#27F4D2", "pts": 80},
    {"pos": 2, "team": "Ferrari",         "color": "#E8002D", "pts": 57},
    {"pos": 3, "team": "McLaren",         "color": "#FF8000", "pts": 40},
    {"pos": 4, "team": "Aston Martin",    "color": "#358C75", "pts": 15},
    {"pos": 5, "team": "Red Bull Racing", "color": "#3671C6", "pts": 14},
    {"pos": 6, "team": "Alpine",          "color": "#0093CC", "pts": 8},
    {"pos": 7, "team": "Audi",            "color": "#C6C6C6", "pts": 4},
    {"pos": 8, "team": "Williams",        "color": "#005AFF", "pts": 3},
]


def get_now() -> datetime:
    return datetime.now(timezone.utc)


def get_race_status() -> Dict:
    """
    Returns the current race weekend status:
    - is_live: race is happening right now
    - is_weekend: we're within the race weekend (Thu-Sun)
    - last_race: most recently completed round
    - next_race: upcoming round
    - days_until_next: countdown
    """
    now = get_now()

    last_race = None
    next_race = None

    for race in CALENDAR_2026:
        race_dt = datetime.fromisoformat(race["race_date"].replace("Z", "+00:00"))
        if race_dt < now:
            last_race = race
        elif next_race is None:
            next_race = race

    # Is a race live? (within 2 hours after race start, or 90 mins before)
    is_live = False
    is_weekend = False
    active_race = None

    if next_race:
        race_dt = datetime.fromisoformat(next_race["race_date"].replace("Z", "+00:00"))
        diff_hours = (race_dt - now).total_seconds() / 3600
        if -2.0 <= diff_hours <= 1.5:
            is_live = True
            active_race = next_race
        if -72 <= diff_hours <= 4:
            is_weekend = True

    days_until = None
    if next_race and not is_live:
        race_dt = datetime.fromisoformat(next_race["race_date"].replace("Z", "+00:00"))
        days_until = max(0, int((race_dt - now).total_seconds() / 86400))

    return {
        "is_live":       is_live,
        "is_weekend":    is_weekend,
        "active_race":   active_race,
        "last_race":     last_race,
        "next_race":     next_race,
        "days_until_next": days_until,
        "season_round":  (last_race["round"] if last_race else 0),
        "total_rounds":  len(CALENDAR_2026),
    }
