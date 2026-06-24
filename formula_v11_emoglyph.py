"""
Formula V11.1: EmoGlyph × SunTzu × Pratitya 三引擎融合预测引擎
==============================================================

World Cup 2026 完整预测引擎 — 17 维度 × 3 引擎架构

Architecture:
    17 Dimensions (8 External + 9 Internal):
        External (37%):
            D1  rest_recovery         12%  — 休息/恢复 (最高权重)
            D2  extreme_heat           5%  — 极端高温 WBGT
            D3  travel_fatigue         4%  — 旅行疲劳
            D4  home_advantage         5%  — 主场优势
            D5  altitude_effect        3%  — 海拔效应
            D6  luck_factor            2%  — 运气因子 (NEW)
            D7  schedule_density       1%  — 赛程密度 (NEW)
            D8  structural_advantage   3%  — 结构优势 (NEW: 48-team format)
        Internal (63%):
            D9  elo_rating            10%  — Elo 评级
            D10 recent_form            8%  — 近期状态
            D11 squad_depth           10%  — 阵容深度
            D12 coaching_style         8%  — 教练风格
            D13 xfactor_players        8%  — X因子球员
            D14 mental_psychological   5%  — 心理/精神 (NEW)
            D15 squad_value            7%  — 阵容身价
            D16 tournament_experience  5%  — 赛事经验
            D17 tactical_matchup       5%  — 战术对位

    3 EmoGlyphPlay Engines:
        1. LightDarkBalance  — ⊕(Light, Dark)^Ξ × Context - |Light - Dark|
        2. SunTzu Strategy   — (P × R) - G + E^t  (道天地將法)
        3. Pratitya Causal   — (R * K) ^ C - L  (缘起因果)

Tournament Format (2026):
    - 48 teams, 12 groups of 4
    - Top 2 per group + 8 best 3rd-place teams advance to Round of 32
    - Knockout: R32 -> R16 -> QF -> SF -> Final
    - 104 total matches over 39 days

Version: V12
Author: EmoGlyph Formula Thinking Engine
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional numpy import — engine works in pure-Python mode without it
# ---------------------------------------------------------------------------
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

# ---------------------------------------------------------------------------
# Optional venue/recovery data imports — graceful fallback
# ---------------------------------------------------------------------------
try:
    from wc2026_venue_data import (
        VENUES,
        FLIGHT_DISTANCE_MATRIX,
        HEAT_ACCLIMATIZATION,
        get_wbgt_risk,
        get_altitude_effect,
        get_travel_fatigue,
    )
    _HAS_VENUE_DATA = True
except ImportError:
    _HAS_VENUE_DATA = False
    VENUES = {}
    FLIGHT_DISTANCE_MATRIX = {}
    HEAT_ACCLIMATIZATION = {"default": 0.60}
    get_wbgt_risk = None
    get_altitude_effect = None
    get_travel_fatigue = None

try:
    from wc2026_recovery_data import get_team_recovery, calculate_recovery_coefficient
    _HAS_RECOVERY_DATA = True
except ImportError:
    _HAS_RECOVERY_DATA = False
    get_team_recovery = None
    calculate_recovery_coefficient = None

try:
    from odds_data_layer import OddsDataLayer
    _HAS_ODDS_LAYER = True
except ImportError:
    _HAS_ODDS_LAYER = False
    OddsDataLayer = None


__all__ = [
    "DIMENSION_WEIGHTS",
    "WC2026_GROUPS",
    "GROUP_STRENGTH_DATA",
    "HOST_NATIONS",
    "ELO_RATINGS",
    "FIFA_RANKINGS",
    "SQUAD_VALUES",
    "RECENT_FORM",
    "COACH_STYLES_2026",
    "TACTICAL_MATRIX",
    "SQUAD_DEPTH_DATA",
    "MENTAL_DATA",
    "LUCK_DATA",
    "XFACTOR_DATA",
    "TOURNAMENT_EXPERIENCE",
    "TEAM_REGION_MAP",
    "TEAM_STYLE_CLASSIFICATION",
    "FormulaV11Engine",
    "quick_test",
]


# ===================================================================
#  DIMENSION WEIGHTS — must sum to 1.0
# ===================================================================

DIMENSION_WEIGHTS: Dict[str, float] = {
    # EXTERNAL (36%)
    "rest_recovery": 0.12,
    "extreme_heat": 0.05,
    "travel_fatigue": 0.04,
    "home_advantage": 0.04,
    "altitude_effect": 0.03,
    "luck_factor": 0.02,
    "schedule_density": 0.01,
    "structural_advantage": 0.03,
    # INTERNAL (64%)
    "elo_rating": 0.10,
    "recent_form": 0.08,
    "squad_depth": 0.10,
    "coaching_style": 0.08,
    "xfactor_players": 0.08,
    "mental_psychological": 0.05,
    "squad_value": 0.07,
    "tournament_experience": 0.05,
    "tactical_matchup": 0.05,
}


# ===================================================================
#  WC2026 GROUPS — 12 groups × 4 teams
# ===================================================================

WC2026_GROUPS: Dict[str, List[str]] = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["USA", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

HOST_NATIONS = {"USA", "Canada", "Mexico"}

# ===================================================================
#  GROUP STRENGTH — parity score per group (0=balanced, 1=dominant)
#  Higher parity = stronger team can secure early, rest in match 3
# ===================================================================

GROUP_STRENGTH_DATA: Dict[str, Dict[str, Any]] = {
    "A": {"dominant_team": "Mexico", "parity": 0.55, "early_secure_prob": 0.60},
    "B": {"dominant_team": "Switzerland", "parity": 0.50, "early_secure_prob": 0.55},
    "C": {"dominant_team": "Brazil", "parity": 0.80, "early_secure_prob": 0.85},
    "D": {"dominant_team": "USA", "parity": 0.60, "early_secure_prob": 0.65},
    "E": {"dominant_team": "Germany", "parity": 0.75, "early_secure_prob": 0.80},
    "F": {"dominant_team": "Netherlands", "parity": 0.60, "early_secure_prob": 0.65},
    "G": {"dominant_team": "Belgium", "parity": 0.65, "early_secure_prob": 0.70},
    "H": {"dominant_team": "Spain", "parity": 0.75, "early_secure_prob": 0.80},
    "I": {"dominant_team": "France", "parity": 0.80, "early_secure_prob": 0.85},
    "J": {"dominant_team": "Argentina", "parity": 0.80, "early_secure_prob": 0.85},
    "K": {"dominant_team": "Portugal", "parity": 0.70, "early_secure_prob": 0.75},
    "L": {"dominant_team": "England", "parity": 0.55, "early_secure_prob": 0.60},
}


# ===================================================================
#  ELO RATINGS — 48 teams (calibrated from FIFA ranking + historical Elo)
# ===================================================================

ELO_RATINGS: Dict[str, float] = {
    # Tier 1 — Elite
    "Spain": 2050, "France": 2040, "Argentina": 2020, "England": 1990,
    "Brazil": 1975, "Portugal": 1960,
    # Tier 2 — Contenders
    "Germany": 1940, "Netherlands": 1930, "Belgium": 1910, "Croatia": 1900,
    "Uruguay": 1870,
    # Tier 3 — Dark Horses
    "Colombia": 1850, "Switzerland": 1830, "USA": 1810, "Mexico": 1800,
    "Japan": 1790, "Morocco": 1780, "Senegal": 1770, "Australia": 1760,
    "Turkey": 1750, "Austria": 1740, "Sweden": 1730,
    # Tier 4 — Competitive
    "Ecuador": 1710, "Ivory Coast": 1700, "Ghana": 1690,
    "South Korea": 1660, "Paraguay": 1650, "Egypt": 1640, "Algeria": 1630,
    "Scotland": 1620, "Norway": 1610, "Czech Republic": 1600, "Iran": 1590,
    "Tunisia": 1580, "Panama": 1570, "Iraq": 1560,
    # Tier 5 — Debutants / Minnows
    "Bosnia and Herzegovina": 1550, "Qatar": 1540, "Saudi Arabia": 1530,
    "Uzbekistan": 1520, "Jordan": 1510, "New Zealand": 1500, "Haiti": 1490,
    "DR Congo": 1480, "Cape Verde": 1470, "Curacao": 1460,
    # Additional
    "South Africa": 1540, "Canada": 1620,
}


# ===================================================================
#  FIFA RANKINGS — approximate June 2026
# ===================================================================

FIFA_RANKINGS: Dict[str, int] = {
    "Spain": 1, "France": 2, "Argentina": 3, "England": 4,
    "Brazil": 5, "Portugal": 6, "Netherlands": 7, "Germany": 8,
    "Belgium": 9, "Uruguay": 10, "Colombia": 11, "Croatia": 12,
    "Switzerland": 14, "USA": 15, "Mexico": 16, "Morocco": 18,
    "Austria": 19, "Turkey": 20, "Norway": 21, "Scotland": 22,
    "Japan": 23, "South Korea": 24, "Senegal": 25, "Ecuador": 26,
    "Paraguay": 27, "Ghana": 28, "Australia": 29, "Egypt": 30,
    "Ivory Coast": 31, "Sweden": 32, "Tunisia": 33, "Algeria": 34,
    "Iran": 35, "Saudi Arabia": 36, "Qatar": 37,
    "Bosnia and Herzegovina": 38, "Czech Republic": 39, "Iraq": 40,
    "DR Congo": 41, "Panama": 42, "Haiti": 43, "New Zealand": 44,
    "Jordan": 45, "Uzbekistan": 46, "Curacao": 47, "Cape Verde": 48,
    "South Africa": 49, "Canada": 50,
}


# ===================================================================
#  SQUAD VALUES — in millions EUR
# ===================================================================

SQUAD_VALUES: Dict[str, float] = {
    "France": 1050, "England": 1020, "Spain": 950, "Brazil": 920,
    "Portugal": 880, "Germany": 850, "Argentina": 830, "Netherlands": 720,
    "Belgium": 650, "Croatia": 480, "Uruguay": 450, "Colombia": 430,
    "Denmark": 380, "Switzerland": 350, "Turkey": 320, "Austria": 300,
    "USA": 280, "Morocco": 250, "Mexico": 220, "Japan": 200,
    "Senegal": 200, "Canada": 200, "Sweden": 180, "Scotland": 170,
    "Czech Republic": 160, "Ecuador": 150, "Ivory Coast": 140,
    "Ghana": 130, "Norway": 120, "South Korea": 120, "Egypt": 110,
    "Algeria": 100, "Paraguay": 90, "Qatar": 80, "Saudi Arabia": 60,
    "Bosnia and Herzegovina": 60, "Iran": 60, "Tunisia": 70, "Iraq": 40,
    "Uzbekistan": 30, "Panama": 30, "South Africa": 45, "New Zealand": 25,
    "Australia": 100, "DR Congo": 25, "Jordan": 20, "Cape Verde": 20, "Haiti": 15,
    "Curacao": 15,
}


# ===================================================================
#  RECENT FORM — last 10 results as W/D/L counts
# ===================================================================

RECENT_FORM: Dict[str, Dict[str, int]] = {
    # Tier 1
    "Spain": {"W": 8, "D": 1, "L": 1},
    "France": {"W": 7, "D": 2, "L": 1},
    "Argentina": {"W": 7, "D": 2, "L": 1},
    "England": {"W": 7, "D": 1, "L": 2},
    "Brazil": {"W": 6, "D": 2, "L": 2},
    "Portugal": {"W": 7, "D": 1, "L": 2},
    # Tier 2
    "Germany": {"W": 6, "D": 2, "L": 2},
    "Netherlands": {"W": 6, "D": 2, "L": 2},
    "Belgium": {"W": 6, "D": 1, "L": 3},
    "Croatia": {"W": 5, "D": 3, "L": 2},
    "Uruguay": {"W": 5, "D": 2, "L": 3},
    # Tier 3
    "Colombia": {"W": 6, "D": 2, "L": 2},
    "Switzerland": {"W": 5, "D": 3, "L": 2},
    "USA": {"W": 6, "D": 2, "L": 2},
    "Mexico": {"W": 5, "D": 2, "L": 3},
    "Japan": {"W": 5, "D": 3, "L": 2},
    "Morocco": {"W": 5, "D": 3, "L": 2},
    "Senegal": {"W": 5, "D": 2, "L": 3},
    "Australia": {"W": 4, "D": 3, "L": 3},
    "Turkey": {"W": 5, "D": 2, "L": 3},
    "Austria": {"W": 5, "D": 3, "L": 2},
    "Sweden": {"W": 4, "D": 3, "L": 3},
    # Tier 4
    "Ecuador": {"W": 4, "D": 3, "L": 3},
    "Ivory Coast": {"W": 4, "D": 3, "L": 3},
    "Ghana": {"W": 4, "D": 2, "L": 4},
    "South Korea": {"W": 4, "D": 2, "L": 4},
    "Paraguay": {"W": 4, "D": 3, "L": 3},
    "Egypt": {"W": 4, "D": 3, "L": 3},
    "Algeria": {"W": 4, "D": 2, "L": 4},
    "Scotland": {"W": 4, "D": 2, "L": 4},
    "Norway": {"W": 6, "D": 2, "L": 2},
    "Czech Republic": {"W": 4, "D": 3, "L": 3},
    "Iran": {"W": 4, "D": 2, "L": 4},
    "Tunisia": {"W": 4, "D": 2, "L": 4},
    "Panama": {"W": 3, "D": 2, "L": 5},
    "Iraq": {"W": 4, "D": 2, "L": 4},
    # Tier 5
    "Bosnia and Herzegovina": {"W": 3, "D": 3, "L": 4},
    "Qatar": {"W": 3, "D": 3, "L": 4},
    "Saudi Arabia": {"W": 3, "D": 2, "L": 5},
    "Uzbekistan": {"W": 3, "D": 3, "L": 4},
    "Jordan": {"W": 3, "D": 3, "L": 4},
    "New Zealand": {"W": 3, "D": 2, "L": 5},
    "Haiti": {"W": 2, "D": 3, "L": 5},
    "DR Congo": {"W": 3, "D": 2, "L": 5},
    "Cape Verde": {"W": 3, "D": 2, "L": 5},
    "Curacao": {"W": 2, "D": 3, "L": 5},
    # Additional
    "South Africa": {"W": 3, "D": 3, "L": 4},
    "Canada": {"W": 4, "D": 3, "L": 3},
}


# ===================================================================
#  COACH STYLES 2026 — all 48 teams
# ===================================================================

COACH_STYLES_2026: Dict[str, Dict[str, Any]] = {
    # Tier 1 — Elite
    "Spain": {"coach": "Luis de la Fuente", "style": "possession", "experience": 0.70, "stability": 0.80, "tournament_exp": 0.70},
    "France": {"coach": "Didier Deschamps", "style": "pragmatic", "experience": 0.95, "stability": 0.90, "tournament_exp": 0.95},
    "Argentina": {"coach": "Lionel Scaloni", "style": "balanced", "experience": 0.85, "stability": 0.85, "tournament_exp": 0.90},
    "England": {"coach": "Thomas Tuchel", "style": "pragmatic", "experience": 0.85, "stability": 0.45, "tournament_exp": 0.75},
    "Brazil": {"coach": "Carlo Ancelotti", "style": "attacking", "experience": 0.95, "stability": 0.40, "tournament_exp": 0.90},
    "Portugal": {"coach": "Roberto Martinez", "style": "attacking", "experience": 0.75, "stability": 0.70, "tournament_exp": 0.70},
    # Tier 2 — Contenders
    "Germany": {"coach": "Julian Nagelsmann", "style": "attacking", "experience": 0.65, "stability": 0.70, "tournament_exp": 0.55},
    "Netherlands": {"coach": "Ronald Koeman", "style": "balanced", "experience": 0.80, "stability": 0.75, "tournament_exp": 0.70},
    "Belgium": {"coach": "Domenico Tedesco", "style": "attacking", "experience": 0.55, "stability": 0.60, "tournament_exp": 0.45},
    "Croatia": {"coach": "Zlatko Dalic", "style": "balanced", "experience": 0.80, "stability": 0.85, "tournament_exp": 0.85},
    "Uruguay": {"coach": "Marcelo Bielsa", "style": "high_press", "experience": 0.85, "stability": 0.65, "tournament_exp": 0.70},
    # Tier 3 — Dark Horses
    "Colombia": {"coach": "Nestor Lorenzo", "style": "counter_attack", "experience": 0.55, "stability": 0.75, "tournament_exp": 0.50},
    "Switzerland": {"coach": "Murat Yakin", "style": "defensive", "experience": 0.60, "stability": 0.75, "tournament_exp": 0.55},
    "USA": {"coach": "Mauricio Pochettino", "style": "high_press", "experience": 0.75, "stability": 0.50, "tournament_exp": 0.50},
    "Mexico": {"coach": "Javier Aguirre", "style": "counter_attack", "experience": 0.80, "stability": 0.60, "tournament_exp": 0.70},
    "Japan": {"coach": "Hajime Moriyasu", "style": "possession", "experience": 0.65, "stability": 0.80, "tournament_exp": 0.60},
    "Morocco": {"coach": "Walid Regragui", "style": "defensive", "experience": 0.60, "stability": 0.80, "tournament_exp": 0.65},
    "Senegal": {"coach": "Aliou Cisse", "style": "counter_attack", "experience": 0.65, "stability": 0.75, "tournament_exp": 0.60},
    "Australia": {"coach": "Tony Popovic", "style": "defensive", "experience": 0.45, "stability": 0.55, "tournament_exp": 0.40},
    "Turkey": {"coach": "Vincenzo Montella", "style": "attacking", "experience": 0.55, "stability": 0.50, "tournament_exp": 0.40},
    "Austria": {"coach": "Ralf Rangnick", "style": "high_press", "experience": 0.80, "stability": 0.70, "tournament_exp": 0.55},
    "Sweden": {"coach": "Jon Dahl Tomasson", "style": "balanced", "experience": 0.45, "stability": 0.55, "tournament_exp": 0.35},
    # Tier 4 — Competitive
    "Ecuador": {"coach": "Sebastian Beccacece", "style": "counter_attack", "experience": 0.40, "stability": 0.55, "tournament_exp": 0.35},
    "Ivory Coast": {"coach": "Emerse Fae", "style": "counter_attack", "experience": 0.40, "stability": 0.60, "tournament_exp": 0.35},
    "Ghana": {"coach": "Otto Addo", "style": "attacking", "experience": 0.40, "stability": 0.45, "tournament_exp": 0.35},
    "South Korea": {"coach": "Hong Myung-bo", "style": "balanced", "experience": 0.50, "stability": 0.55, "tournament_exp": 0.45},
    "Paraguay": {"coach": "Gustavo Alfaro", "style": "defensive", "experience": 0.55, "stability": 0.65, "tournament_exp": 0.45},
    "Egypt": {"coach": "Rui Vitoria", "style": "counter_attack", "experience": 0.55, "stability": 0.55, "tournament_exp": 0.45},
    "Algeria": {"coach": "Vladimir Petkovic", "style": "balanced", "experience": 0.55, "stability": 0.55, "tournament_exp": 0.45},
    "Scotland": {"coach": "Steve Clarke", "style": "defensive", "experience": 0.55, "stability": 0.70, "tournament_exp": 0.40},
    "Norway": {"coach": "Stale Solbakken", "style": "pragmatic", "experience": 0.60, "stability": 0.65, "tournament_exp": 0.35},
    "Czech Republic": {"coach": "Ivan Hasek", "style": "balanced", "experience": 0.50, "stability": 0.60, "tournament_exp": 0.40},
    "Iran": {"coach": "Amir Ghalenoei", "style": "defensive", "experience": 0.50, "stability": 0.55, "tournament_exp": 0.40},
    "Tunisia": {"coach": "Faouzi Benzarti", "style": "defensive", "experience": 0.60, "stability": 0.50, "tournament_exp": 0.45},
    "Panama": {"coach": "Thomas Christiansen", "style": "defensive", "experience": 0.45, "stability": 0.60, "tournament_exp": 0.35},
    "Iraq": {"coach": "Jesus Casas", "style": "balanced", "experience": 0.40, "stability": 0.50, "tournament_exp": 0.30},
    # Tier 5 — Debutants / Minnows
    "Bosnia and Herzegovina": {"coach": "Sergej Barbarez", "style": "balanced", "experience": 0.30, "stability": 0.40, "tournament_exp": 0.25},
    "Qatar": {"coach": "Tintin Marquez", "style": "possession", "experience": 0.40, "stability": 0.50, "tournament_exp": 0.30},
    "Saudi Arabia": {"coach": "Herve Renard", "style": "defensive", "experience": 0.75, "stability": 0.60, "tournament_exp": 0.60},
    "Uzbekistan": {"coach": "Srecko Katanec", "style": "defensive", "experience": 0.55, "stability": 0.55, "tournament_exp": 0.30},
    "Jordan": {"coach": "Hussein Amotta", "style": "defensive", "experience": 0.40, "stability": 0.50, "tournament_exp": 0.25},
    "New Zealand": {"coach": "Danny Bazeley", "style": "balanced", "experience": 0.30, "stability": 0.45, "tournament_exp": 0.25},
    "Haiti": {"coach": "Gabriel Calderon", "style": "counter_attack", "experience": 0.35, "stability": 0.35, "tournament_exp": 0.20},
    "DR Congo": {"coach": "Sebastien Desabre", "style": "counter_attack", "experience": 0.40, "stability": 0.45, "tournament_exp": 0.30},
    "Cape Verde": {"coach": "Bubista", "style": "balanced", "experience": 0.35, "stability": 0.55, "tournament_exp": 0.25},
    "Curacao": {"coach": "Remko Bicentini", "style": "defensive", "experience": 0.30, "stability": 0.40, "tournament_exp": 0.15},
    # Additional
    "South Africa": {"coach": "Hugo Broos", "style": "defensive", "experience": 0.55, "stability": 0.60, "tournament_exp": 0.35},
    "Canada": {"coach": "Jesse Marsch", "style": "high_press", "experience": 0.55, "stability": 0.55, "tournament_exp": 0.40},
}


# ===================================================================
#  TACTICAL MATRIX — 7×7 style interaction matrix
#  Styles: attacking, possession, defensive, pragmatic,
#          high_press, counter_attack, balanced
#  Cell value = advantage for row style vs column style (0.35–0.65)
# ===================================================================

TACTICAL_MATRIX: Dict[str, Dict[str, float]] = {
    "attacking": {
        "attacking": 0.50, "possession": 0.53, "defensive": 0.45,
        "pragmatic": 0.48, "high_press": 0.47, "counter_attack": 0.42,
        "balanced": 0.52,
    },
    "possession": {
        "attacking": 0.47, "possession": 0.50, "defensive": 0.55,
        "pragmatic": 0.48, "high_press": 0.42, "counter_attack": 0.42,
        "balanced": 0.52,
    },
    "defensive": {
        "attacking": 0.55, "possession": 0.45, "defensive": 0.50,
        "pragmatic": 0.52, "high_press": 0.43, "counter_attack": 0.55,
        "balanced": 0.52,
    },
    "pragmatic": {
        "attacking": 0.52, "possession": 0.52, "defensive": 0.48,
        "pragmatic": 0.50, "high_press": 0.50, "counter_attack": 0.52,
        "balanced": 0.51,
    },
    "high_press": {
        "attacking": 0.53, "possession": 0.58, "defensive": 0.57,
        "pragmatic": 0.50, "high_press": 0.50, "counter_attack": 0.45,
        "balanced": 0.53,
    },
    "counter_attack": {
        "attacking": 0.58, "possession": 0.58, "defensive": 0.45,
        "pragmatic": 0.48, "high_press": 0.55, "counter_attack": 0.50,
        "balanced": 0.52,
    },
    "balanced": {
        "attacking": 0.48, "possession": 0.48, "defensive": 0.48,
        "pragmatic": 0.49, "high_press": 0.47, "counter_attack": 0.48,
        "balanced": 0.50,
    },
}


# ===================================================================
#  SQUAD DEPTH DATA — all 48 teams
# ===================================================================

SQUAD_DEPTH_DATA: Dict[str, Dict[str, Any]] = {
    # Tier 1
    "Spain": {"bench_ratio": 0.82, "sub_teams_available": 3, "position_coverage": 0.90},
    "France": {"bench_ratio": 0.85, "sub_teams_available": 3, "position_coverage": 0.95},
    "Argentina": {"bench_ratio": 0.78, "sub_teams_available": 2, "position_coverage": 0.85},
    "England": {"bench_ratio": 0.82, "sub_teams_available": 3, "position_coverage": 0.90},
    "Brazil": {"bench_ratio": 0.80, "sub_teams_available": 3, "position_coverage": 0.88},
    "Portugal": {"bench_ratio": 0.78, "sub_teams_available": 2, "position_coverage": 0.85},
    # Tier 2
    "Germany": {"bench_ratio": 0.78, "sub_teams_available": 2, "position_coverage": 0.85},
    "Netherlands": {"bench_ratio": 0.72, "sub_teams_available": 2, "position_coverage": 0.80},
    "Belgium": {"bench_ratio": 0.70, "sub_teams_available": 2, "position_coverage": 0.78},
    "Croatia": {"bench_ratio": 0.62, "sub_teams_available": 2, "position_coverage": 0.70},
    "Uruguay": {"bench_ratio": 0.60, "sub_teams_available": 2, "position_coverage": 0.68},
    # Tier 3
    "Colombia": {"bench_ratio": 0.60, "sub_teams_available": 2, "position_coverage": 0.68},
    "Switzerland": {"bench_ratio": 0.58, "sub_teams_available": 2, "position_coverage": 0.65},
    "USA": {"bench_ratio": 0.60, "sub_teams_available": 2, "position_coverage": 0.65},
    "Mexico": {"bench_ratio": 0.55, "sub_teams_available": 2, "position_coverage": 0.60},
    "Japan": {"bench_ratio": 0.58, "sub_teams_available": 2, "position_coverage": 0.65},
    "Morocco": {"bench_ratio": 0.55, "sub_teams_available": 2, "position_coverage": 0.62},
    "Senegal": {"bench_ratio": 0.52, "sub_teams_available": 1, "position_coverage": 0.58},
    "Australia": {"bench_ratio": 0.48, "sub_teams_available": 1, "position_coverage": 0.52},
    "Turkey": {"bench_ratio": 0.55, "sub_teams_available": 2, "position_coverage": 0.60},
    "Austria": {"bench_ratio": 0.55, "sub_teams_available": 2, "position_coverage": 0.60},
    "Sweden": {"bench_ratio": 0.50, "sub_teams_available": 1, "position_coverage": 0.55},
    # Tier 4
    "Ecuador": {"bench_ratio": 0.48, "sub_teams_available": 1, "position_coverage": 0.52},
    "Ivory Coast": {"bench_ratio": 0.50, "sub_teams_available": 1, "position_coverage": 0.55},
    "Ghana": {"bench_ratio": 0.48, "sub_teams_available": 1, "position_coverage": 0.52},
    "South Korea": {"bench_ratio": 0.50, "sub_teams_available": 1, "position_coverage": 0.55},
    "Paraguay": {"bench_ratio": 0.45, "sub_teams_available": 1, "position_coverage": 0.50},
    "Egypt": {"bench_ratio": 0.45, "sub_teams_available": 1, "position_coverage": 0.50},
    "Algeria": {"bench_ratio": 0.45, "sub_teams_available": 1, "position_coverage": 0.50},
    "Scotland": {"bench_ratio": 0.45, "sub_teams_available": 1, "position_coverage": 0.50},
    "Norway": {"bench_ratio": 0.50, "sub_teams_available": 1, "position_coverage": 0.55},
    "Czech Republic": {"bench_ratio": 0.48, "sub_teams_available": 1, "position_coverage": 0.52},
    "Iran": {"bench_ratio": 0.40, "sub_teams_available": 1, "position_coverage": 0.45},
    "Tunisia": {"bench_ratio": 0.42, "sub_teams_available": 1, "position_coverage": 0.48},
    "Panama": {"bench_ratio": 0.35, "sub_teams_available": 1, "position_coverage": 0.38},
    "Iraq": {"bench_ratio": 0.38, "sub_teams_available": 1, "position_coverage": 0.42},
    # Tier 5
    "Bosnia and Herzegovina": {"bench_ratio": 0.40, "sub_teams_available": 1, "position_coverage": 0.45},
    "Qatar": {"bench_ratio": 0.38, "sub_teams_available": 1, "position_coverage": 0.42},
    "Saudi Arabia": {"bench_ratio": 0.42, "sub_teams_available": 1, "position_coverage": 0.48},
    "Uzbekistan": {"bench_ratio": 0.35, "sub_teams_available": 1, "position_coverage": 0.38},
    "Jordan": {"bench_ratio": 0.30, "sub_teams_available": 1, "position_coverage": 0.35},
    "New Zealand": {"bench_ratio": 0.32, "sub_teams_available": 1, "position_coverage": 0.38},
    "Haiti": {"bench_ratio": 0.28, "sub_teams_available": 1, "position_coverage": 0.32},
    "DR Congo": {"bench_ratio": 0.35, "sub_teams_available": 1, "position_coverage": 0.40},
    "Cape Verde": {"bench_ratio": 0.30, "sub_teams_available": 1, "position_coverage": 0.35},
    "Curacao": {"bench_ratio": 0.25, "sub_teams_available": 1, "position_coverage": 0.30},
    # Additional
    "South Africa": {"bench_ratio": 0.38, "sub_teams_available": 1, "position_coverage": 0.42},
    "Canada": {"bench_ratio": 0.48, "sub_teams_available": 1, "position_coverage": 0.52},
}


# ===================================================================
#  MENTAL DATA — psychological factors for all 48 teams
# ===================================================================

MENTAL_DATA: Dict[str, Dict[str, float]] = {
    "knockout_pressure_resistance": {
        "Spain": 0.80, "France": 0.90, "Argentina": 0.88, "England": 0.65,
        "Brazil": 0.70, "Portugal": 0.72, "Germany": 0.82, "Netherlands": 0.75,
        "Belgium": 0.60, "Croatia": 0.85, "Uruguay": 0.78, "Colombia": 0.62,
        "Switzerland": 0.65, "USA": 0.55, "Mexico": 0.50, "Japan": 0.60,
        "Morocco": 0.65, "Senegal": 0.55, "Australia": 0.50, "Turkey": 0.52,
        "Austria": 0.55, "Sweden": 0.55, "Ecuador": 0.45, "Ivory Coast": 0.48,
        "Ghana": 0.50, "South Korea": 0.50, "Paraguay": 0.48, "Egypt": 0.45,
        "Algeria": 0.45, "Scotland": 0.42, "Norway": 0.50, "Czech Republic": 0.48,
        "Iran": 0.45, "Tunisia": 0.42, "Panama": 0.30, "Iraq": 0.38,
        "Bosnia and Herzegovina": 0.38, "Qatar": 0.30, "Saudi Arabia": 0.40,
        "Uzbekistan": 0.32, "Jordan": 0.28, "New Zealand": 0.35,
        "Haiti": 0.25, "DR Congo": 0.30, "Cape Verde": 0.28, "Curacao": 0.22,
        "South Africa": 0.38, "Canada": 0.42,
    },
    "comeback_ability": {
        "Spain": 0.70, "France": 0.80, "Argentina": 0.85, "England": 0.60,
        "Brazil": 0.75, "Portugal": 0.68, "Germany": 0.78, "Netherlands": 0.72,
        "Belgium": 0.55, "Croatia": 0.80, "Uruguay": 0.70, "Colombia": 0.60,
        "Switzerland": 0.55, "USA": 0.52, "Mexico": 0.48, "Japan": 0.55,
        "Morocco": 0.58, "Senegal": 0.50, "Australia": 0.45, "Turkey": 0.50,
        "Austria": 0.50, "Sweden": 0.48, "Ecuador": 0.42, "Ivory Coast": 0.45,
        "Ghana": 0.48, "South Korea": 0.45, "Paraguay": 0.42, "Egypt": 0.40,
        "Algeria": 0.42, "Scotland": 0.38, "Norway": 0.48, "Czech Republic": 0.42,
        "Iran": 0.38, "Tunisia": 0.35, "Panama": 0.25, "Iraq": 0.32,
        "Bosnia and Herzegovina": 0.32, "Qatar": 0.25, "Saudi Arabia": 0.35,
        "Uzbekistan": 0.28, "Jordan": 0.25, "New Zealand": 0.30,
        "Haiti": 0.22, "DR Congo": 0.28, "Cape Verde": 0.25, "Curacao": 0.20,
        "South Africa": 0.35, "Canada": 0.40,
    },
    "national_expectation_pressure": {
        "Spain": 0.60, "France": 0.70, "Argentina": 0.80, "England": 0.75,
        "Brazil": 0.85, "Portugal": 0.55, "Germany": 0.70, "Netherlands": 0.50,
        "Belgium": 0.45, "Croatia": 0.55, "Uruguay": 0.50, "Colombia": 0.45,
        "Switzerland": 0.30, "USA": 0.50, "Mexico": 0.60, "Japan": 0.45,
        "Morocco": 0.50, "Senegal": 0.35, "Australia": 0.30, "Turkey": 0.50,
        "Austria": 0.30, "Sweden": 0.30, "Ecuador": 0.35, "Ivory Coast": 0.30,
        "Ghana": 0.35, "South Korea": 0.55, "Paraguay": 0.25, "Egypt": 0.40,
        "Algeria": 0.35, "Scotland": 0.35, "Norway": 0.25, "Czech Republic": 0.25,
        "Iran": 0.40, "Tunisia": 0.25, "Panama": 0.20, "Iraq": 0.30,
        "Bosnia and Herzegovina": 0.25, "Qatar": 0.35, "Saudi Arabia": 0.45,
        "Uzbekistan": 0.25, "Jordan": 0.30, "New Zealand": 0.20,
        "Haiti": 0.20, "DR Congo": 0.20, "Cape Verde": 0.20, "Curacao": 0.15,
        "South Africa": 0.30, "Canada": 0.35,
    },
    "new_coach_instability": {
        "Spain": 0.15, "France": 0.05, "Argentina": 0.10, "England": 0.40,
        "Brazil": 0.45, "Portugal": 0.20, "Germany": 0.25, "Netherlands": 0.15,
        "Belgium": 0.30, "Croatia": 0.10, "Uruguay": 0.20, "Colombia": 0.25,
        "Switzerland": 0.15, "USA": 0.35, "Mexico": 0.25, "Japan": 0.15,
        "Morocco": 0.15, "Senegal": 0.20, "Australia": 0.35, "Turkey": 0.30,
        "Austria": 0.20, "Sweden": 0.30, "Ecuador": 0.35, "Ivory Coast": 0.30,
        "Ghana": 0.35, "South Korea": 0.25, "Paraguay": 0.20, "Egypt": 0.25,
        "Algeria": 0.25, "Scotland": 0.15, "Norway": 0.20, "Czech Republic": 0.25,
        "Iran": 0.25, "Tunisia": 0.30, "Panama": 0.25, "Iraq": 0.30,
        "Bosnia and Herzegovina": 0.40, "Qatar": 0.25, "Saudi Arabia": 0.15,
        "Uzbekistan": 0.20, "Jordan": 0.25, "New Zealand": 0.35,
        "Haiti": 0.35, "DR Congo": 0.25, "Cape Verde": 0.20, "Curacao": 0.35,
        "South Africa": 0.20, "Canada": 0.30,
    },
}


# ===================================================================
#  LUCK DATA — penalty records, woodwork, VAR
# ===================================================================

LUCK_DATA: Dict[str, Dict[str, Any]] = {
    "penalty_win_rate": {
        "Spain": 0.58, "France": 0.62, "Argentina": 0.65, "England": 0.45,
        "Brazil": 0.55, "Portugal": 0.52, "Germany": 0.70, "Netherlands": 0.55,
        "Belgium": 0.48, "Croatia": 0.60, "Uruguay": 0.52, "Colombia": 0.48,
        "Switzerland": 0.50, "USA": 0.45, "Mexico": 0.42, "Japan": 0.48,
        "Morocco": 0.45, "Senegal": 0.42, "Australia": 0.40, "Turkey": 0.45,
        "Austria": 0.48, "Sweden": 0.50, "Ecuador": 0.42, "Ivory Coast": 0.40,
        "Ghana": 0.38, "South Korea": 0.45, "Paraguay": 0.42, "Egypt": 0.40,
        "Algeria": 0.42, "Scotland": 0.45, "Norway": 0.48, "Czech Republic": 0.45,
        "Iran": 0.38, "Tunisia": 0.40, "Panama": 0.35, "Iraq": 0.38,
        "Bosnia and Herzegovina": 0.42, "Qatar": 0.35, "Saudi Arabia": 0.38,
        "Uzbekistan": 0.35, "Jordan": 0.32, "New Zealand": 0.38,
        "Haiti": 0.30, "DR Congo": 0.35, "Cape Verde": 0.32, "Curacao": 0.28,
        "South Africa": 0.38, "Canada": 0.40,
    },
    "woodwork_hit_rate": {
        # Average rate per tournament (historical)
        "elite": 0.08, "contender": 0.07, "dark_horse": 0.06,
        "competitive": 0.05, "minnow": 0.04,
    },
    "var_overturn_rate": {
        # Approximate VAR overturn rates by confederation
        "uefa": 0.12, "conmebol": 0.10, "concacaf": 0.08,
        "caf": 0.07, "afc": 0.09, "ofc": 0.06,
    },
}


# ===================================================================
#  X-FACTOR DATA — all 48 teams
# ===================================================================

XFACTOR_DATA: Dict[str, Dict[str, Any]] = {
    # Tier 1
    "Spain": {"dribbler_impact": 0.80, "young_talent": 0.85, "set_piece": 0.70, "experience_clutch": 0.80, "key_players": ["Pedri", "Yamal"]},
    "France": {"dribbler_impact": 0.85, "young_talent": 0.80, "set_piece": 0.75, "experience_clutch": 0.90, "key_players": ["Mbappe", "Griezmann"]},
    "Argentina": {"dribbler_impact": 0.80, "young_talent": 0.70, "set_piece": 0.80, "experience_clutch": 0.95, "key_players": ["Messi", "Alvarez"]},
    "England": {"dribbler_impact": 0.75, "young_talent": 0.85, "set_piece": 0.80, "experience_clutch": 0.65, "key_players": ["Bellingham", "Saka"]},
    "Brazil": {"dribbler_impact": 0.90, "young_talent": 0.85, "set_piece": 0.70, "experience_clutch": 0.75, "key_players": ["Vinicius Jr", "Rodrygo"]},
    "Portugal": {"dribbler_impact": 0.78, "young_talent": 0.80, "set_piece": 0.72, "experience_clutch": 0.70, "key_players": ["Leao", "Silva"]},
    # Tier 2
    "Germany": {"dribbler_impact": 0.72, "young_talent": 0.82, "set_piece": 0.75, "experience_clutch": 0.72, "key_players": ["Musiala", "Wirtz"]},
    "Netherlands": {"dribbler_impact": 0.70, "young_talent": 0.75, "set_piece": 0.78, "experience_clutch": 0.68, "key_players": ["Simons", "Gakpo"]},
    "Belgium": {"dribbler_impact": 0.68, "young_talent": 0.60, "set_piece": 0.65, "experience_clutch": 0.62, "key_players": ["De Bruyne", "Doku"]},
    "Croatia": {"dribbler_impact": 0.62, "young_talent": 0.55, "set_piece": 0.72, "experience_clutch": 0.82, "key_players": ["Modric", "Kramaric"]},
    "Uruguay": {"dribbler_impact": 0.68, "young_talent": 0.72, "set_piece": 0.70, "experience_clutch": 0.70, "key_players": ["Nunez", "Valverde"]},
    # Tier 3
    "Colombia": {"dribbler_impact": 0.70, "young_talent": 0.60, "set_piece": 0.62, "experience_clutch": 0.58, "key_players": ["Diaz", "James"]},
    "Switzerland": {"dribbler_impact": 0.55, "young_talent": 0.55, "set_piece": 0.68, "experience_clutch": 0.60, "key_players": ["Xhaka", "Akanji"]},
    "USA": {"dribbler_impact": 0.62, "young_talent": 0.72, "set_piece": 0.58, "experience_clutch": 0.48, "key_players": ["Pulisic", "Reyna"]},
    "Mexico": {"dribbler_impact": 0.58, "young_talent": 0.55, "set_piece": 0.60, "experience_clutch": 0.52, "key_players": ["Jimenez", "Lozano"]},
    "Japan": {"dribbler_impact": 0.60, "young_talent": 0.68, "set_piece": 0.55, "experience_clutch": 0.50, "key_players": ["Kubo", "Mitoma"]},
    "Morocco": {"dribbler_impact": 0.58, "young_talent": 0.60, "set_piece": 0.55, "experience_clutch": 0.62, "key_players": ["Hakimi", "Ziyech"]},
    "Senegal": {"dribbler_impact": 0.60, "young_talent": 0.55, "set_piece": 0.52, "experience_clutch": 0.50, "key_players": ["Mane", "Sarr"]},
    "Australia": {"dribbler_impact": 0.45, "young_talent": 0.48, "set_piece": 0.55, "experience_clutch": 0.45, "key_players": ["Kewell Jr", "Irvine"]},
    "Turkey": {"dribbler_impact": 0.62, "young_talent": 0.60, "set_piece": 0.55, "experience_clutch": 0.48, "key_players": ["Calhanoglu", "Guler"]},
    "Austria": {"dribbler_impact": 0.58, "young_talent": 0.62, "set_piece": 0.58, "experience_clutch": 0.50, "key_players": ["Sabitzer", "Arnautovic"]},
    "Sweden": {"dribbler_impact": 0.48, "young_talent": 0.50, "set_piece": 0.60, "experience_clutch": 0.48, "key_players": ["Isak", "Kulusevski"]},
    # Tier 4
    "Ecuador": {"dribbler_impact": 0.50, "young_talent": 0.48, "set_piece": 0.50, "experience_clutch": 0.42, "key_players": ["Valencia", "Caicedo"]},
    "Ivory Coast": {"dribbler_impact": 0.55, "young_talent": 0.52, "set_piece": 0.48, "experience_clutch": 0.42, "key_players": ["Kessie", "Pepe"]},
    "Ghana": {"dribbler_impact": 0.55, "young_talent": 0.50, "set_piece": 0.45, "experience_clutch": 0.40, "key_players": ["Kudus", "Partey"]},
    "South Korea": {"dribbler_impact": 0.55, "young_talent": 0.52, "set_piece": 0.55, "experience_clutch": 0.45, "key_players": ["Son", "Lee"]},
    "Paraguay": {"dribbler_impact": 0.45, "young_talent": 0.42, "set_piece": 0.52, "experience_clutch": 0.40, "key_players": ["Almiron", "Enciso"]},
    "Egypt": {"dribbler_impact": 0.52, "young_talent": 0.45, "set_piece": 0.48, "experience_clutch": 0.42, "key_players": ["Salah", "Trezeguet"]},
    "Algeria": {"dribbler_impact": 0.50, "young_talent": 0.45, "set_piece": 0.48, "experience_clutch": 0.40, "key_players": ["Mahrez", "Brahimi"]},
    "Scotland": {"dribbler_impact": 0.40, "young_talent": 0.42, "set_piece": 0.55, "experience_clutch": 0.38, "key_players": ["Robertson", "McTominay"]},
    "Norway": {"dribbler_impact": 0.55, "young_talent": 0.58, "set_piece": 0.52, "experience_clutch": 0.42, "key_players": ["Haaland", "Odegaard"]},
    "Czech Republic": {"dribbler_impact": 0.42, "young_talent": 0.42, "set_piece": 0.55, "experience_clutch": 0.42, "key_players": ["Soucek", "Schick"]},
    "Iran": {"dribbler_impact": 0.42, "young_talent": 0.38, "set_piece": 0.45, "experience_clutch": 0.35, "key_players": ["Taremi", "Azmoun"]},
    "Tunisia": {"dribbler_impact": 0.40, "young_talent": 0.38, "set_piece": 0.45, "experience_clutch": 0.38, "key_players": ["Khazri", "Brahimi"]},
    "Panama": {"dribbler_impact": 0.30, "young_talent": 0.28, "set_piece": 0.35, "experience_clutch": 0.22, "key_players": ["Torres", "Davis"]},
    "Iraq": {"dribbler_impact": 0.38, "young_talent": 0.35, "set_piece": 0.40, "experience_clutch": 0.32, "key_players": ["Hussein", "Ali"]},
    # Tier 5
    "Bosnia and Herzegovina": {"dribbler_impact": 0.38, "young_talent": 0.32, "set_piece": 0.42, "experience_clutch": 0.35, "key_players": ["Dzeko", "Pjanic"]},
    "Qatar": {"dribbler_impact": 0.35, "young_talent": 0.35, "set_piece": 0.38, "experience_clutch": 0.25, "key_players": ["Almoez", "Afif"]},
    "Saudi Arabia": {"dribbler_impact": 0.42, "young_talent": 0.38, "set_piece": 0.42, "experience_clutch": 0.35, "key_players": ["Al-Dawsari", "Al-Shehri"]},
    "Uzbekistan": {"dribbler_impact": 0.35, "young_talent": 0.35, "set_piece": 0.38, "experience_clutch": 0.28, "key_players": ["Shomurodov", "Masharipov"]},
    "Jordan": {"dribbler_impact": 0.30, "young_talent": 0.28, "set_piece": 0.35, "experience_clutch": 0.25, "key_players": ["Al-Naimat", "Al-Rashdan"]},
    "New Zealand": {"dribbler_impact": 0.30, "young_talent": 0.28, "set_piece": 0.38, "experience_clutch": 0.28, "key_players": ["Wood", "Boxall"]},
    "Haiti": {"dribbler_impact": 0.28, "young_talent": 0.25, "set_piece": 0.30, "experience_clutch": 0.20, "key_players": ["Duckens Nazon", "Joseph"]},
    "DR Congo": {"dribbler_impact": 0.40, "young_talent": 0.38, "set_piece": 0.35, "experience_clutch": 0.28, "key_players": ["Bakambu", "Kakuta"]},
    "Cape Verde": {"dribbler_impact": 0.38, "young_talent": 0.32, "set_piece": 0.35, "experience_clutch": 0.25, "key_players": ["Mendes", "Soares"]},
    "Curacao": {"dribbler_impact": 0.28, "young_talent": 0.22, "set_piece": 0.30, "experience_clutch": 0.18, "key_players": ["Bacuna", "Martina"]},
    # Additional
    "South Africa": {"dribbler_impact": 0.38, "young_talent": 0.35, "set_piece": 0.38, "experience_clutch": 0.30, "key_players": ["Modise", "Zungu"]},
    "Canada": {"dribbler_impact": 0.52, "young_talent": 0.55, "set_piece": 0.48, "experience_clutch": 0.38, "key_players": ["Davies", "David"]},
}


# ===================================================================
#  TOURNAMENT EXPERIENCE — all 48 teams
# ===================================================================

TOURNAMENT_EXPERIENCE: Dict[str, float] = {
    # Based on historical WC appearances and performance
    "Brazil": 0.95, "Germany": 0.95, "Argentina": 0.90, "France": 0.90,
    "Spain": 0.85, "England": 0.80, "Uruguay": 0.80,
    "Netherlands": 0.75, "Portugal": 0.75, "Croatia": 0.80, "Belgium": 0.70,
    "Mexico": 0.70, "USA": 0.60, "Japan": 0.60, "South Korea": 0.55,
    "Switzerland": 0.55, "Colombia": 0.55, "Sweden": 0.55,
    "Australia": 0.50, "Ecuador": 0.45, "Ghana": 0.50, "Ivory Coast": 0.45,
    "Morocco": 0.55, "Senegal": 0.45, "Turkey": 0.45, "Paraguay": 0.45,
    "Egypt": 0.40, "Algeria": 0.40, "Scotland": 0.40, "Norway": 0.40,
    "Austria": 0.40, "Czech Republic": 0.45, "Iran": 0.40, "Tunisia": 0.35,
    "Panama": 0.20, "Iraq": 0.35,
    "Bosnia and Herzegovina": 0.30, "Qatar": 0.25, "Saudi Arabia": 0.40,
    "Uzbekistan": 0.20, "Jordan": 0.15, "New Zealand": 0.30,
    "Haiti": 0.15, "DR Congo": 0.20, "Cape Verde": 0.10, "Curacao": 0.10,
    "South Africa": 0.30, "Canada": 0.25,
}


# ===================================================================
#  TEAM REGION MAP — for heat acclimatization lookup
# ===================================================================

TEAM_REGION_MAP: Dict[str, str] = {
    # South America
    "Brazil": "south_america", "Argentina": "south_america", "Colombia": "south_america",
    "Uruguay": "south_america", "Ecuador": "south_america", "Paraguay": "south_america",
    # Africa
    "Morocco": "africa", "Senegal": "africa", "Egypt": "africa", "Algeria": "africa",
    "Ghana": "africa", "Ivory Coast": "africa", "Tunisia": "africa", "South Africa": "africa",
    "DR Congo": "africa", "Cape Verde": "africa",
    # Middle East
    "Iran": "middle_east", "Saudi Arabia": "middle_east", "Qatar": "middle_east",
    "Iraq": "middle_east", "Jordan": "middle_east",
    # Central America / Caribbean
    "Mexico": "central_america_caribbean", "USA": "central_america_caribbean",
    "Canada": "northern_europe", "Panama": "central_america_caribbean",
    "Haiti": "central_america_caribbean", "Curacao": "central_america_caribbean",
    # East Asia
    "Japan": "east_asia", "South Korea": "east_asia", "Uzbekistan": "east_asia",
    # Southern Europe
    "Spain": "southern_europe", "Portugal": "southern_europe", "France": "southern_europe",
    "Italy": "southern_europe", "Turkey": "southern_europe", "Croatia": "southern_europe",
    # Northern Europe
    "England": "northern_europe", "Germany": "northern_europe",
    "Netherlands": "northern_europe", "Belgium": "northern_europe",
    "Sweden": "northern_europe", "Norway": "northern_europe",
    "Scotland": "northern_europe", "Austria": "northern_europe",
    "Switzerland": "northern_europe", "Czech Republic": "northern_europe",
    "Bosnia and Herzegovina": "northern_europe",
    # Oceania
    "Australia": "southern_europe", "New Zealand": "southern_europe",
}


# ===================================================================
#  TEAM STYLE CLASSIFICATION — defensive_counter / attacking_possession / balanced
# ===================================================================

TEAM_STYLE_CLASSIFICATION: Dict[str, str] = {
    # Defensive counter-attack specialists
    "Morocco": "defensive_counter", "Uruguay": "defensive_counter",
    "Switzerland": "defensive_counter", "Croatia": "defensive_counter",
    "Mexico": "defensive_counter", "Japan": "defensive_counter",
    "South Korea": "defensive_counter", "Saudi Arabia": "defensive_counter",
    "Colombia": "defensive_counter", "Senegal": "defensive_counter",
    "Egypt": "defensive_counter", "Paraguay": "defensive_counter",
    "Scotland": "defensive_counter", "Iran": "defensive_counter",
    "Tunisia": "defensive_counter", "Panama": "defensive_counter",
    "Uzbekistan": "defensive_counter", "Jordan": "defensive_counter",
    "Australia": "defensive_counter", "Haiti": "defensive_counter",
    "DR Congo": "defensive_counter", "Curacao": "defensive_counter",
    "South Africa": "defensive_counter",
    # Attacking possession teams
    "Brazil": "attacking_possession", "Spain": "attacking_possession",
    "Argentina": "attacking_possession", "Portugal": "attacking_possession",
    "Netherlands": "attacking_possession", "Germany": "attacking_possession",
    "Belgium": "attacking_possession", "Turkey": "attacking_possession",
    "Ghana": "attacking_possession", "Qatar": "attacking_possession",
    # Balanced teams
    "France": "balanced", "England": "balanced", "Italy": "balanced",
    "USA": "balanced", "Norway": "balanced", "Austria": "balanced",
    "Sweden": "balanced", "Ivory Coast": "balanced", "Algeria": "balanced",
    "Czech Republic": "balanced", "Iraq": "balanced",
    "Bosnia and Herzegovina": "balanced", "New Zealand": "balanced",
    "Cape Verde": "balanced", "Canada": "balanced",
    "Ecuador": "balanced",
}


# ===================================================================
#  FORMULA V11 ENGINE
# ===================================================================

class FormulaV11Engine:
    """Formula V11.1: EmoGlyph × SunTzu × Pratitya 三引擎融合"""

    def __init__(self):
        self.weights = DIMENSION_WEIGHTS
        self._venue_data_available = _HAS_VENUE_DATA
        self._recovery_data_available = _HAS_RECOVERY_DATA
        self._odds_layer = None
        self._has_odds_layer = _HAS_ODDS_LAYER
        self._market_alpha = 0.15

    def _get_odds_layer(self):
        if self._odds_layer is None and self._has_odds_layer:
            try:
                self._odds_layer = OddsDataLayer(cache_duration_hours=6, jurisdiction="other")
            except Exception:
                self._has_odds_layer = False
                self._odds_layer = None
        return self._odds_layer

    def _blend_with_market_consensus(self, team_a: str, team_b: str,
                                     prob_a_win: float, draw_prob: float,
                                     prob_b_win: float) -> Tuple[float, float, float]:
        odds_layer = self._get_odds_layer()
        if odds_layer is None:
            return prob_a_win, draw_prob, prob_b_win
        try:
            market = odds_layer.get_market_weight_for_v11(team_a, team_b)
            m_a = getattr(market, "home_win_probability", prob_a_win)
            m_d = getattr(market, "draw_probability", draw_prob)
            m_b = getattr(market, "away_win_probability", prob_b_win)
            alpha = self._market_alpha
            f_a = alpha * m_a + (1 - alpha) * prob_a_win
            f_d = alpha * m_d + (1 - alpha) * draw_prob
            f_b = alpha * m_b + (1 - alpha) * prob_b_win
            total = f_a + f_d + f_b
            if total > 0:
                return f_a / total, f_d / total, f_b / total
            return prob_a_win, draw_prob, prob_b_win
        except Exception:
            return prob_a_win, draw_prob, prob_b_win

    # ================================================================
    #  16 Dimension Scoring Functions
    #  Each returns float 0.0–1.0
    # ================================================================

    def score_rest_recovery(self, team: str, match_context: dict) -> float:
        """D1: Rest/Recovery (12%) — uses wc2026_recovery_data when available"""
        if self._recovery_data_available and calculate_recovery_coefficient is not None:
            recovery = calculate_recovery_coefficient(team)
        else:
            # Fallback: estimate from squad depth and tournament experience
            depth = SQUAD_DEPTH_DATA.get(team, {"bench_ratio": 0.50})
            exp = TOURNAMENT_EXPERIENCE.get(team, 0.30)
            recovery = depth["bench_ratio"] * 0.5 + exp * 0.3 + 0.2

        days_rest = match_context.get("days_since_last_match", 4)
        match_recovery = min(1.0, days_rest / 4.0)
        return max(0.1, min(1.0, recovery * 0.6 + match_recovery * 0.4))

    def score_extreme_heat(self, team: str, match_context: dict) -> float:
        """D2: Extreme Heat WBGT (5%)"""
        if self._venue_data_available and get_wbgt_risk is not None:
            venue_id = match_context.get("venue_id", "nyc")
            match_time = match_context.get("match_time", "afternoon")
            wbgt_risk = get_wbgt_risk(venue_id, match_time)
            team_region = self._get_team_region(team)
            acclimatization = HEAT_ACCLIMATIZATION.get(team_region, 0.60)
            heat_penalty = max(0, (wbgt_risk["wbgt_adjusted"] - 28) / 10)
            return max(0.3, 1.0 - heat_penalty * (1 - acclimatization))
        else:
            # Fallback: estimate from team region
            team_region = self._get_team_region(team)
            acclimatization = HEAT_ACCLIMATIZATION.get(team_region, 0.60)
            return max(0.3, 0.5 + acclimatization * 0.4)

    def score_travel_fatigue(self, team: str, match_context: dict) -> float:
        """D3: Travel Fatigue (4%)"""
        if self._venue_data_available and get_travel_fatigue is not None:
            venue_from = match_context.get("previous_venue", "nyc")
            venue_to = match_context.get("venue_id", "nyc")
            travel = get_travel_fatigue(venue_from, venue_to)
            return max(0.3, 1.0 - travel["fatigue_score"])
        else:
            # Fallback: neutral score
            return 0.70

    def score_home_advantage(self, team: str, match_context: dict) -> float:
        """D4: Home Advantage (5%)"""
        if team in HOST_NATIONS:
            venue_id = match_context.get("venue_id", "")
            host_country_map = {"USA": "USA", "Canada": "Canada", "Mexico": "Mexico"}
            if self._venue_data_available and VENUES:
                venue = VENUES.get(venue_id, {})
                if venue.get("country") == host_country_map.get(team):
                    return 0.90  # True home
            return 0.70  # Host nation but not home city
        return 0.50

    def score_altitude_effect(self, team: str, match_context: dict) -> float:
        """D5: Altitude Effect (3%)"""
        if self._venue_data_available and get_altitude_effect is not None:
            venue_id = match_context.get("venue_id", "nyc")
            team_region = self._get_team_region(team)
            effect = get_altitude_effect(venue_id, team_region)
            return max(0.3, 1.0 - effect)
        else:
            # Fallback: estimate from team region
            team_region = self._get_team_region(team)
            if team_region in ("mexico", "andean", "middle_east", "africa"):
                return 0.85
            return 0.70

    def score_luck_factor(self, team: str, match_context: dict) -> float:
        """D6: Luck Factor (3%)"""
        penalty_luck = LUCK_DATA["penalty_win_rate"].get(team, 0.50)
        return 0.5 + (penalty_luck - 0.5) * 0.3

    def score_schedule_density(self, team: str, match_context: dict) -> float:
        """D7: Match Schedule Density (2%)"""
        match_num = match_context.get("match_number", 1)
        if match_num <= 3:
            base = 0.85  # Group stage 3-4 day intervals
        elif match_num <= 6:
            base = 0.75  # R32/R16 4-5 day intervals
        else:
            base = 0.65  # QF+ more rest but more fatigue
        return base

    def score_elo_rating(self, team: str, match_context: dict) -> float:
        """D8: Elo Rating (10%)"""
        elo = ELO_RATINGS.get(team, 1500)
        return min(1.0, max(0.1, (elo - 1400) / 700))  # Normalize 1400-2100 to 0-1

    def score_recent_form(self, team: str, match_context: dict) -> float:
        """D9: Recent Form (8%)"""
        form = RECENT_FORM.get(team, {"W": 4, "D": 3, "L": 3})
        total = form["W"] + form["D"] + form["L"]
        if total == 0:
            return 0.5
        return (form["W"] * 3 + form["D"]) / (total * 3)

    def score_squad_depth(self, team: str, match_context: dict) -> float:
        """D10: Squad Depth Index (10%)"""
        depth = SQUAD_DEPTH_DATA.get(team, {"bench_ratio": 0.50, "sub_teams_available": 1, "position_coverage": 0.50})
        return (
            depth["bench_ratio"] * 0.40
            + min(1.0, depth["sub_teams_available"] / 3.0) * 0.35
            + depth["position_coverage"] * 0.25
        )

    def score_coaching_style(self, team: str, match_context: dict) -> float:
        """D11: Coaching Style 2026 (8%)"""
        coach = COACH_STYLES_2026.get(team, {"experience": 0.50, "stability": 0.50, "tournament_exp": 0.50})
        return (
            coach["experience"] * 0.35
            + coach["stability"] * 0.35
            + coach["tournament_exp"] * 0.30
        )

    def score_xfactor_players(self, team: str, match_context: dict) -> float:
        """D12: X-Factor Players (8%)"""
        xfactor = XFACTOR_DATA.get(team, {"dribbler_impact": 0.50, "young_talent": 0.50, "set_piece": 0.50, "experience_clutch": 0.50})
        return (
            xfactor["dribbler_impact"] * 0.40
            + xfactor["young_talent"] * 0.25
            + xfactor["set_piece"] * 0.20
            + xfactor["experience_clutch"] * 0.15
        )

    def score_mental_psychological(self, team: str, match_context: dict) -> float:
        """D13: Mental/Psychological (5%)"""
        mental = MENTAL_DATA["knockout_pressure_resistance"].get(team, 0.50)
        comeback = MENTAL_DATA["comeback_ability"].get(team, 0.50)
        expectation = MENTAL_DATA["national_expectation_pressure"].get(team, 0.40)
        coach_inst = MENTAL_DATA["new_coach_instability"].get(team, 0.20)
        stage = match_context.get("stage", "group")

        base = (mental * 0.30 + comeback * 0.25 + (1 - expectation * 0.5) * 0.20 + (1 - coach_inst) * 0.25)
        if stage in ("r32", "r16"):
            base *= 1.2
        elif stage in ("qf", "sf", "final"):
            base *= 1.5
        return min(1.0, max(0.1, base))

    def score_squad_value(self, team: str, match_context: dict) -> float:
        """D14: Squad Value (7%)"""
        value = SQUAD_VALUES.get(team, 50)
        return min(1.0, max(0.05, value / 1100))

    def score_tournament_experience(self, team: str, match_context: dict) -> float:
        """D15: Tournament Experience (5%)"""
        return TOURNAMENT_EXPERIENCE.get(team, 0.30)

    def score_tactical_matchup(self, team: str, opponent: str, match_context: dict) -> float:
        """D17: Tactical Matchup (5%)"""
        team_style = COACH_STYLES_2026.get(team, {"style": "balanced"})["style"]
        opp_style = COACH_STYLES_2026.get(opponent, {"style": "balanced"})["style"]
        styles = ["attacking", "possession", "defensive", "pragmatic", "high_press", "counter_attack", "balanced"]
        if team_style in styles and opp_style in styles:
            return TACTICAL_MATRIX.get(team_style, {}).get(opp_style, 0.50)
        return 0.50

    def score_structural_advantage(self, team: str, match_context: dict) -> float:
        """D17: Structural Advantage (3%) — 48-team format: early secure + rest + bracket position"""
        # Find which group this team is in
        team_group = None
        for group_name, teams in WC2026_GROUPS.items():
            if team in teams:
                team_group = group_name
                break

        if team_group is None:
            return 0.30

        group_data = GROUP_STRENGTH_DATA.get(team_group, {"parity": 0.50, "early_secure_prob": 0.50, "dominant_team": ""})

        # Is this team the dominant team in the group?
        is_dominant = group_data.get("dominant_team") == team

        # early_secure_bonus: can this team win first 2 matches and secure top-2?
        if is_dominant:
            early_secure_bonus = group_data["early_secure_prob"]
        else:
            # Non-dominant teams have lower early-secure probability
            team_elo = ELO_RATINGS.get(team, 1500)
            group_elos = [ELO_RATINGS.get(t, 1500) for t in WC2026_GROUPS[team_group]]
            avg_elo = sum(group_elos) / len(group_elos)
            if team_elo > avg_elo:
                early_secure_bonus = 0.40 + (team_elo - avg_elo) / 500 * 0.30
            else:
                early_secure_bonus = 0.20

        # rest_advantage: if team can rest in match 3, they gain recovery for R32
        squad_depth = SQUAD_DEPTH_DATA.get(team, {"sub_teams_available": 1})
        sub_teams = squad_depth.get("sub_teams_available", 1) if isinstance(squad_depth, dict) else 1
        if is_dominant and sub_teams >= 2:
            rest_advantage = 0.85  # Can rotate squad effectively
        elif is_dominant:
            rest_advantage = 0.70  # Can rest but limited rotation
        else:
            rest_advantage = 0.40  # Must fight all 3 matches

        # bracket_position_value: 1st place gets easier R32 draw
        if is_dominant:
            bracket_position_value = 0.85  # 1st place = favorable draw
        else:
            team_elo = ELO_RATINGS.get(team, 1500)
            group_elos = [ELO_RATINGS.get(t, 1500) for t in WC2026_GROUPS[team_group]]
            sorted_elos = sorted(group_elos, reverse=True)
            if team_elo >= sorted_elos[1]:  # Likely 2nd place
                bracket_position_value = 0.60
            elif team_elo >= sorted_elos[2]:  # Likely 3rd place
                bracket_position_value = 0.40  # 3rd place = harder draw
            else:
                bracket_position_value = 0.25  # 4th place = unlikely to advance

        score = (
            early_secure_bonus * 0.40
            + rest_advantage * 0.35
            + bracket_position_value * 0.25
        )
        return min(1.0, max(0.05, score))

    # ================================================================
    #  Defensive Counter-Attack Advantage
    # ================================================================

    def score_defensive_counter_advantage(self, team: str, opponent: str, match_context: dict) -> float:
        """Defensive counter-attack advantage in extreme conditions.

        Defensive-counter teams gain a bonus in extreme heat and at altitude,
        while attacking-possession teams suffer a penalty. When a
        defensive_counter team faces an attacking_possession team in extreme
        conditions, the net swing is doubled (both bonuses/penalties apply).

        Returns:
            float: bonus/penalty to multiply final probability by (1 + bonus).
        """
        team_style = TEAM_STYLE_CLASSIFICATION.get(team, "balanced")
        opponent_style = TEAM_STYLE_CLASSIFICATION.get(opponent, "balanced")

        wbgt = match_context.get("venue_wbgt", 0.0)
        altitude = match_context.get("venue_altitude", 0.0)

        extreme_heat = wbgt > 28.0
        at_altitude = altitude > 1500.0

        bonus = 0.0

        if extreme_heat:
            if team_style == "defensive_counter":
                bonus += 0.05
            elif team_style == "attacking_possession":
                bonus -= 0.05

        if at_altitude:
            if team_style == "defensive_counter":
                bonus += 0.03
            elif team_style == "attacking_possession":
                bonus -= 0.03

        # Double the net swing when defensive_counter faces attacking_possession
        # in extreme conditions (both teams get their respective bonuses/penalties)
        if extreme_heat or at_altitude:
            if (team_style == "defensive_counter" and opponent_style == "attacking_possession") or \
               (team_style == "attacking_possession" and opponent_style == "defensive_counter"):
                bonus *= 2.0

        return bonus

    # ================================================================
    #  Helper: Calculate all 17 dimensions for one team
    # ================================================================

    def _calculate_all_dimensions(self, team: str, opponent: str, ctx: dict) -> dict:
        """Calculate all 17 dimension scores for a team"""
        return {
            "rest_recovery": self.score_rest_recovery(team, ctx),
            "extreme_heat": self.score_extreme_heat(team, ctx),
            "travel_fatigue": self.score_travel_fatigue(team, ctx),
            "home_advantage": self.score_home_advantage(team, ctx),
            "altitude_effect": self.score_altitude_effect(team, ctx),
            "luck_factor": self.score_luck_factor(team, ctx),
            "schedule_density": self.score_schedule_density(team, ctx),
            "structural_advantage": self.score_structural_advantage(team, ctx),
            "elo_rating": self.score_elo_rating(team, ctx),
            "recent_form": self.score_recent_form(team, ctx),
            "squad_depth": self.score_squad_depth(team, ctx),
            "coaching_style": self.score_coaching_style(team, ctx),
            "xfactor_players": self.score_xfactor_players(team, ctx),
            "mental_psychological": self.score_mental_psychological(team, ctx),
            "squad_value": self.score_squad_value(team, ctx),
            "tournament_experience": self.score_tournament_experience(team, ctx),
            "tactical_matchup": self.score_tactical_matchup(team, opponent, ctx),
        }

    # ================================================================
    #  Helper: Team region lookup
    # ================================================================

    def _get_team_region(self, team: str) -> str:
        """Map team to region for heat acclimatization"""
        return TEAM_REGION_MAP.get(team, "default")

    # ================================================================
    #  EmoGlyphPlay Engine 1: LightDarkBalance
    # ================================================================

    def calculate_light_dark_balance(self, team: str, opponent: str, match_context: dict) -> dict:
        """
        LightDarkBalance = ⊕(Light, Dark)^Ξ × Context - |Light - Dark|

        Returns: {"ldb": float, "light": float, "dark": float, "confidence": str, "upset_alert": bool}
        """
        # Calculate Light (positive) factors
        light_factors = {
            "recovery": self.score_rest_recovery(team, match_context),
            "depth": self.score_squad_depth(team, match_context),
            "coach_stability": COACH_STYLES_2026.get(team, {}).get("stability", 0.5),
            "experience": self.score_tournament_experience(team, match_context),
            "mental": self.score_mental_psychological(team, match_context),
        }
        light = sum(light_factors.values()) / len(light_factors)

        # Calculate Dark (risk) factors
        dark_factors = {
            "heat_risk": 1 - self.score_extreme_heat(team, match_context),
            "travel_risk": 1 - self.score_travel_fatigue(team, match_context),
            "thin_squad": 1 - self.score_squad_depth(team, match_context),
            "coach_instability": MENTAL_DATA["new_coach_instability"].get(team, 0.2),
            "pressure": MENTAL_DATA["national_expectation_pressure"].get(team, 0.4),
        }
        dark = sum(dark_factors.values()) / len(dark_factors)

        # ⊕(Light, Dark) — Superposition (weighted average)
        superposition = (light + (1 - dark)) / 2

        # Ξ — Emergence detection (non-linear interaction)
        emergence = 1 + 0.3 * (light * (1 - dark) - 0.5)

        # Context factor
        stage = match_context.get("stage", "group")
        context_mult = {"group": 0.8, "r32": 0.9, "r16": 1.0, "qf": 1.1, "sf": 1.2, "final": 1.3}.get(stage, 0.8)

        # Balance
        ldb = superposition * emergence * context_mult - abs(light - (1 - dark))
        ldb = max(-1.0, min(1.0, ldb))

        confidence = "high" if ldb > 0.3 else ("medium" if ldb > -0.1 else "low")
        upset_alert = ldb < -0.2

        return {
            "ldb": round(ldb, 4),
            "light": round(light, 4),
            "dark": round(dark, 4),
            "confidence": confidence,
            "upset_alert": upset_alert,
        }

    # ================================================================
    #  EmoGlyphPlay Engine 2: SunTzu Strategy
    # ================================================================

    def calculate_suntzu_strategy(self, team: str, opponent: str, match_context: dict) -> dict:
        """
        SunTzu = (P × R) - G + E^t
        P=戰力, R=資源, G=衝突成本, E^t=演化優勢
        """
        # 道 (Purpose) — national motivation
        dao = MENTAL_DATA["national_expectation_pressure"].get(team, 0.4) * 0.7 + 0.3

        # 天 (Weather) — environmental conditions
        tian = self.score_extreme_heat(team, match_context) * 0.6 + self.score_altitude_effect(team, match_context) * 0.4

        # 地 (Terrain) — venue/travel
        di = (
            self.score_home_advantage(team, match_context) * 0.5
            + (1 - self.score_travel_fatigue(team, match_context)) * 0.3
            + self.score_schedule_density(team, match_context) * 0.2
        )

        # 將 (Commander) — coaching
        jiang = self.score_coaching_style(team, match_context)

        # 法 (Method) — tactical system
        fa = self.score_tactical_matchup(team, opponent, match_context) * 0.6 + self.score_squad_depth(team, match_context) * 0.4

        # SunTzu formula
        P = (dao + tian + di + jiang + fa) / 5  # Overall power
        R = self.score_squad_depth(team, match_context) * self.score_squad_value(team, match_context)  # Resources
        G = (1 - self.score_extreme_heat(team, match_context)) + (1 - self.score_travel_fatigue(team, match_context))  # Conflict cost
        t = match_context.get("tournament_round", 1)
        E_t = jiang * (1 + 0.05 * t)  # Evolutionary advantage grows with rounds

        suntzu_raw = (P * R) - (G * 0.3) + (E_t * 0.2)
        suntzu_normalized = 1 / (1 + math.exp(-5 * (suntzu_raw - 0.5)))  # Sigmoid
        suntzu_normalized = max(0.3, min(1.0, suntzu_normalized))

        return {
            "suntzu": round(suntzu_normalized, 4),
            "dao": round(dao, 4),
            "tian": round(tian, 4),
            "di": round(di, 4),
            "jiang": round(jiang, 4),
            "fa": round(fa, 4),
        }

    # ================================================================
    #  EmoGlyphPlay Engine 3: Pratitya Causal
    # ================================================================

    def calculate_pratitya_causal(self, team: str, opponent: str, match_context: dict) -> dict:
        """
        Pratitya = (R * K) ^ C - L
        R=推理, K=知識, C=上下文, L=線性偏見
        Returns context-dependent weight adjustments for each dimension
        """
        R = 0.7  # Reasoning from historical data
        K = 0.8  # Knowledge from factor data

        # Context amplification based on match situation
        stage = match_context.get("stage", "group")
        C = {"group": 0.8, "r32": 0.9, "r16": 1.0, "qf": 1.1, "sf": 1.15, "final": 1.2}.get(stage, 0.8)

        # Heat + schedule context amplifies recovery importance
        heat_context = False
        if self._venue_data_available and get_wbgt_risk is not None:
            venue_id = match_context.get("venue_id", "nyc")
            heat_context = get_wbgt_risk(venue_id, "afternoon")["wbgt_adjusted"] > 30
        if heat_context:
            C *= 1.1

        # Linear bias (over-reliance on Elo)
        L = 0.15

        pratitya_value = (R * K) ** C - L

        # Generate context-dependent weight adjustments
        adjustments = {}
        if heat_context:
            adjustments["rest_recovery"] = 0.03
            adjustments["extreme_heat"] = 0.02
            adjustments["squad_depth"] = 0.02
        if stage in ("qf", "sf", "final"):
            adjustments["mental_psychological"] = 0.02
            adjustments["xfactor_players"] = 0.02
            adjustments["coaching_style"] = 0.01
        if COACH_STYLES_2026.get(team, {}).get("stability", 0.5) < 0.5:
            adjustments["coaching_style"] = adjustments.get("coaching_style", 0) + 0.02
        if SQUAD_DEPTH_DATA.get(team, {}).get("sub_teams_available", 1) < 2:
            adjustments["squad_depth"] = adjustments.get("squad_depth", 0) + 0.02

        return {"pratitya": round(pratitya_value, 4), "adjustments": adjustments}

    # ================================================================
    #  Core Prediction: predict_match
    # ================================================================

    def predict_match(self, team_a: str, team_b: str, match_context: dict = None) -> dict:
        """Predict match outcome with all 16 dimensions + 3 engines"""
        if match_context is None:
            match_context = {
                "venue_id": "nyc",
                "match_time": "afternoon",
                "stage": "group",
                "match_number": 1,
            }

        # Calculate all 16 dimension scores for both teams
        scores_a = self._calculate_all_dimensions(team_a, team_b, match_context)
        scores_b = self._calculate_all_dimensions(team_b, team_a, match_context)

        # Apply Pratitya context adjustments
        pratitya_a = self.calculate_pratitya_causal(team_a, team_b, match_context)
        pratitya_b = self.calculate_pratitya_causal(team_b, team_a, match_context)

        # Adjusted weights
        weights_a = dict(self.weights)
        weights_b = dict(self.weights)
        for dim, adj in pratitya_a["adjustments"].items():
            weights_a[dim] = weights_a.get(dim, 0) + adj
        for dim, adj in pratitya_b["adjustments"].items():
            weights_b[dim] = weights_b.get(dim, 0) + adj
        # Renormalize
        total_a = sum(weights_a.values())
        total_b = sum(weights_b.values())
        weights_a = {k: v / total_a for k, v in weights_a.items()}
        weights_b = {k: v / total_b for k, v in weights_b.items()}

        # P_base
        p_base_a = sum(weights_a.get(dim, 0) * score for dim, score in scores_a.items())
        p_base_b = sum(weights_b.get(dim, 0) * score for dim, score in scores_b.items())

        # LightDarkBalance
        ldb_a = self.calculate_light_dark_balance(team_a, team_b, match_context)
        ldb_b = self.calculate_light_dark_balance(team_b, team_a, match_context)

        # SunTzu
        suntzu_a = self.calculate_suntzu_strategy(team_a, team_b, match_context)
        suntzu_b = self.calculate_suntzu_strategy(team_b, team_a, match_context)

        # Final probability
        alpha_ldb = 0.15
        p_final_a = p_base_a * (1 + ldb_a["ldb"] * alpha_ldb) * suntzu_a["suntzu"]
        p_final_b = p_base_b * (1 + ldb_b["ldb"] * alpha_ldb) * suntzu_b["suntzu"]

        # Defensive counter-attack advantage modifier
        defensive_bonus_a = self.score_defensive_counter_advantage(team_a, team_b, match_context)
        defensive_bonus_b = self.score_defensive_counter_advantage(team_b, team_a, match_context)
        p_final_a *= (1 + defensive_bonus_a)
        p_final_b *= (1 + defensive_bonus_b)

        # Normalize to probabilities
        total = p_final_a + p_final_b
        prob_a = p_final_a / total if total > 0 else 0.5
        prob_b = p_final_b / total if total > 0 else 0.5

        # Draw probability (approximation)
        draw_prob = max(0.05, 0.30 - abs(prob_a - prob_b) * 0.5)
        draw_prob = min(draw_prob, 0.30)

        # Adjust for draw
        remaining = 1.0 - draw_prob
        prob_a_win = remaining * prob_a / (prob_a + prob_b) if (prob_a + prob_b) > 0 else 0.35
        prob_b_win = remaining * prob_b / (prob_a + prob_b) if (prob_a + prob_b) > 0 else 0.35

        # Backend-only market consensus blend (α=0.15) — never exposed on frontend
        prob_a_win, draw_prob, prob_b_win = self._blend_with_market_consensus(
            team_a, team_b, prob_a_win, draw_prob, prob_b_win
        )

        return {
            "team_a": team_a,
            "team_b": team_b,
            "prob_a_win": round(prob_a_win, 4),
            "prob_draw": round(draw_prob, 4),
            "prob_b_win": round(prob_b_win, 4),
            "scores_a": {k: round(v, 4) for k, v in scores_a.items()},
            "scores_b": {k: round(v, 4) for k, v in scores_b.items()},
            "ldb_a": ldb_a,
            "ldb_b": ldb_b,
            "suntzu_a": suntzu_a,
            "suntzu_b": suntzu_b,
            "pratitya_a": pratitya_a,
            "pratitya_b": pratitya_b,
            "upset_alert": ldb_a["upset_alert"] or ldb_b["upset_alert"],
        }

    # ================================================================
    #  Monte Carlo Tournament Simulation
    # ================================================================

    def simulate_tournament(self, n_simulations: int = 1000, match_context: dict = None) -> dict:
        """Full 48-team tournament Monte Carlo simulation"""
        results = {
            team: {"wins": 0, "finals": 0, "semis": 0, "quarters": 0, "r16": 0, "group_advance": 0}
            for team in ELO_RATINGS
        }

        for sim in range(n_simulations):
            # Simulate group stage
            group_results = self._simulate_group_stage(match_context)

            # Determine advancing teams
            advancing = self._determine_advancing_teams(group_results)

            # Track group advancement
            for team in advancing:
                if team in results:
                    results[team]["group_advance"] += 1

            # Simulate knockout rounds
            self._simulate_knockout(advancing, results, match_context)

        # Calculate probabilities
        total = n_simulations
        predictions = {}
        for team, res in results.items():
            predictions[team] = {
                "win_probability": round(res["wins"] / total, 4),
                "final_probability": round(res["finals"] / total, 4),
                "semi_probability": round(res["semis"] / total, 4),
                "quarter_probability": round(res["quarters"] / total, 4),
                "r16_probability": round(res["r16"] / total, 4),
                "group_advance_probability": round(res["group_advance"] / total, 4),
            }

        # Sort by win probability
        sorted_predictions = dict(
            sorted(predictions.items(), key=lambda x: x[1]["win_probability"], reverse=True)
        )

        return {"n_simulations": total, "predictions": sorted_predictions}

    def _simulate_group_stage(self, base_context: dict) -> dict:
        """Simulate all group stage matches with rotation modeling"""
        group_results = {}
        for group_name, teams in WC2026_GROUPS.items():
            group_results[group_name] = {t: {"points": 0, "gf": 0, "ga": 0, "wins": 0} for t in teams}
            match_order = [
                (0, 1), (2, 3),  # Match day 1
                (0, 2), (1, 3),  # Match day 2
                (0, 3), (1, 2),  # Match day 3
            ]
            for idx_a, idx_b in match_order:
                team_a, team_b = teams[idx_a], teams[idx_b]
                ctx = dict(base_context or {})
                ctx["stage"] = "group"

                # Check if team has already secured advancement (6 points = 2 wins)
                a_secured = group_results[group_name][team_a]["wins"] >= 2
                b_secured = group_results[group_name][team_b]["wins"] >= 2

                result = self.predict_match(team_a, team_b, ctx)

                # Apply rotation penalty for teams that have already secured
                if a_secured:
                    result["prob_a_win"] *= 0.80  # 20% reduction for rotation
                    result["prob_draw"] *= 1.10   # More likely to draw
                if b_secured:
                    result["prob_b_win"] *= 0.80
                    result["prob_draw"] *= 1.10

                # Normalize probabilities
                total = result["prob_a_win"] + result["prob_draw"] + result["prob_b_win"]
                result["prob_a_win"] /= total
                result["prob_draw"] /= total
                result["prob_b_win"] /= total

                # Determine outcome
                rand = random.random()
                if rand < result["prob_a_win"]:
                    group_results[group_name][team_a]["points"] += 3
                    group_results[group_name][team_a]["wins"] += 1
                elif rand < result["prob_a_win"] + result["prob_draw"]:
                    group_results[group_name][team_a]["points"] += 1
                    group_results[group_name][team_b]["points"] += 1
                else:
                    group_results[group_name][team_b]["points"] += 3
                    group_results[group_name][team_b]["wins"] += 1
        return group_results

    def _determine_advancing_teams(self, group_results: dict) -> list:
        """Top 2 per group + 8 best 3rd place teams"""
        advancing = []
        third_place_teams = []

        for group_name, teams_data in group_results.items():
            sorted_teams = sorted(
                teams_data.items(),
                key=lambda x: (x[1]["points"], x[1]["gf"] - x[1]["ga"]),
                reverse=True,
            )
            advancing.extend([sorted_teams[0][0], sorted_teams[1][0]])
            third_place_teams.append((sorted_teams[2][0], sorted_teams[2][1]["points"]))

        # Best 8 third-place teams
        third_place_teams.sort(key=lambda x: x[1], reverse=True)
        advancing.extend([t[0] for t in third_place_teams[:8]])

        return advancing

    def _simulate_knockout(self, advancing: list, results: dict, base_context: dict):
        """Simulate R32 → R16 → QF → SF → Final"""
        # R32: 16 matches
        r32_winners = self._simulate_knockout_round(advancing, results, "r32", base_context, "r16")
        # R16: 8 matches
        r16_winners = self._simulate_knockout_round(r32_winners, results, "r16", base_context, "quarters")
        # QF: 4 matches
        qf_winners = self._simulate_knockout_round(r16_winners, results, "qf", base_context, "semis")
        # SF: 2 matches
        sf_winners = self._simulate_knockout_round(qf_winners, results, "sf", base_context, "finals")
        # Final: 1 match
        if len(sf_winners) >= 2:
            ctx = dict(base_context or {})
            ctx["stage"] = "final"
            result = self.predict_match(sf_winners[0], sf_winners[1], ctx)
            rand = random.random()
            prob_a = result["prob_a_win"] / (result["prob_a_win"] + result["prob_b_win"])
            winner = sf_winners[0] if rand < prob_a else sf_winners[1]
            results[winner]["wins"] += 1
            results[sf_winners[0]]["finals"] += 1
            results[sf_winners[1]]["finals"] += 1

    def _simulate_knockout_round(
        self, teams: list, results: dict, stage: str, base_context: dict, result_key: str
    ) -> list:
        """Simulate one knockout round"""
        winners = []
        for i in range(0, len(teams) - 1, 2):
            team_a, team_b = teams[i], teams[i + 1]
            ctx = dict(base_context or {})
            ctx["stage"] = stage
            result = self.predict_match(team_a, team_b, ctx)
            rand = random.random()
            # In knockout, no draw — use win probabilities normalized
            prob_a = result["prob_a_win"] / (result["prob_a_win"] + result["prob_b_win"])
            winner = team_a if rand < prob_a else team_b
            winners.append(winner)
            if team_a in results:
                results[team_a][result_key] += 1
            if team_b in results:
                results[team_b][result_key] += 1
        return winners

    # ================================================================
    #  Monte Carlo Convergence Testing
    # ================================================================

    def simulate_tournament_convergence(self, n_max: int = 10000, match_context: dict = None) -> dict:
        """Run Monte Carlo simulations at checkpoints and measure convergence.

        Runs simulations at 4 checkpoints (1K/2K/5K/10K by default), records
        top-10 win probabilities at each, and computes stability metrics,
        95% confidence intervals, and upset detections.

        Args:
            n_max: Maximum number of simulations (default 10000).
            match_context: Optional context dict passed to predict_match.

        Returns:
            Convergence report dict with checkpoints, convergence_status,
            confidence_intervals, and upset_detection.
        """
        # Default checkpoints at 10%/20%/50%/100% of n_max
        default_checkpoints = [1000, 2000, 5000, 10000]
        if n_max >= 10000:
            checkpoints_config = default_checkpoints
        else:
            # Scale checkpoints proportionally: 10%/20%/50%/100% of n_max
            checkpoints_config = [
                max(1, n_max // 10),
                max(1, n_max // 5),
                max(1, n_max // 2),
                n_max,
            ]
            # Remove duplicates while preserving order
            seen = set()
            unique = []
            for cp in checkpoints_config:
                if cp not in seen:
                    seen.add(cp)
                    unique.append(cp)
            checkpoints_config = unique

        # Accumulate results across all simulations
        results = {
            team: {"wins": 0, "finals": 0, "semis": 0, "quarters": 0, "r16": 0, "group_advance": 0}
            for team in ELO_RATINGS
        }

        # Track match-level model vs Elo probabilities for upset detection
        # We sample a fixed set of key matchups to compare
        key_matchups = self._get_key_matchups_for_upset_detection()
        upset_tracking = {
            f"{a} vs {b}": {"model_probs": [], "elo_probs": []}
            for a, b in key_matchups
        }

        checkpoints_data = {}
        prev_top5_probs = None
        sim_count = 0

        for target_n in checkpoints_config:
            # Run simulations from current count to target
            while sim_count < target_n:
                group_results = self._simulate_group_stage(match_context)
                advancing = self._determine_advancing_teams(group_results)
                for team in advancing:
                    if team in results:
                        results[team]["group_advance"] += 1
                self._simulate_knockout(advancing, results, match_context)
                sim_count += 1

            # Record predictions at this checkpoint
            predictions = {}
            for team, res in results.items():
                predictions[team] = {
                    "win_probability": round(res["wins"] / sim_count, 4),
                    "final_probability": round(res["finals"] / sim_count, 4),
                    "semi_probability": round(res["semis"] / sim_count, 4),
                    "quarter_probability": round(res["quarters"] / sim_count, 4),
                    "r16_probability": round(res["r16"] / sim_count, 4),
                    "group_advance_probability": round(res["group_advance"] / sim_count, 4),
                }

            sorted_preds = dict(
                sorted(predictions.items(), key=lambda x: x[1]["win_probability"], reverse=True)
            )

            # Top 10 teams at this checkpoint
            top10 = dict(list(sorted_preds.items())[:10])

            # Calculate top-5 stability
            top5_probs = {team: sorted_preds[team]["win_probability"] for team in list(sorted_preds.keys())[:5]}

            if prev_top5_probs is not None:
                # Max % change among top-5 teams present in both checkpoints
                max_pct_change = 0.0
                for team in top5_probs:
                    if team in prev_top5_probs and prev_top5_probs[team] > 0:
                        pct_change = abs(top5_probs[team] - prev_top5_probs[team]) / prev_top5_probs[team] * 100
                        max_pct_change = max(max_pct_change, pct_change)
                stability = round(max_pct_change, 4)
            else:
                stability = None  # No previous checkpoint to compare

            checkpoints_data[str(target_n)] = {
                "predictions": top10,
                "top5_stability": stability,
            }

            prev_top5_probs = top5_probs

        # Determine convergence status
        # Check stability between last two checkpoints
        checkpoint_keys = list(checkpoints_data.keys())
        convergence_status = "Not converged"
        convergence_detail = ""
        if len(checkpoint_keys) >= 2:
            last_stability = checkpoints_data[checkpoint_keys[-1]]["top5_stability"]
            second_last_key = checkpoint_keys[-2]
            last_key = checkpoint_keys[-1]
            if last_stability is not None:
                if last_stability < 1.0:
                    convergence_status = "Converged"
                convergence_detail = f"Change from {second_last_key} to {last_key}: {last_stability:.4f}%"

        # 95% confidence intervals for top team
        final_preds = checkpoints_data[checkpoint_keys[-1]]["predictions"]
        top_team_name = list(final_preds.keys())[0]
        top_team_prob = final_preds[top_team_name]["win_probability"]
        n_final = int(checkpoint_keys[-1])
        ci_half = 1.96 * math.sqrt(top_team_prob * (1 - top_team_prob) / n_final)
        ci_lower = round(max(0.0, top_team_prob - ci_half), 4)
        ci_upper = round(min(1.0, top_team_prob + ci_half), 4)

        confidence_intervals = {
            "top_team": {
                "team": top_team_name,
                "win_prob": top_team_prob,
                "ci_95": (ci_lower, ci_upper),
            }
        }

        # Upset detection: compare model probability vs Elo-only probability
        upset_detection = []
        for a, b in key_matchups:
            ctx = dict(match_context or {})
            ctx["stage"] = "group"
            model_result = self.predict_match(a, b, ctx)
            model_prob_a = model_result["prob_a_win"]

            # Elo-only probability (standard Elo formula)
            elo_a = ELO_RATINGS.get(a, 1500)
            elo_b = ELO_RATINGS.get(b, 1500)
            elo_prob_a = 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))

            divergence = abs(model_prob_a - elo_prob_a) * 100  # as percentage
            if divergence > 15:
                upset_detection.append({
                    "match": f"{a} vs {b}",
                    "model_prob": round(model_prob_a, 4),
                    "elo_prob": round(elo_prob_a, 4),
                    "divergence": round(divergence, 2),
                })

        return {
            "checkpoints": checkpoints_data,
            "convergence_status": convergence_status,
            "convergence_detail": convergence_detail,
            "confidence_intervals": confidence_intervals,
            "upset_detection": upset_detection,
        }

    def _get_key_matchups_for_upset_detection(self) -> list:
        """Return a curated list of key matchups for upset detection.

        Covers cross-tier games where the model's multi-dimensional
        assessment is most likely to diverge from pure Elo.
        """
        return [
            ("France", "Brazil"),
            ("Spain", "Germany"),
            ("England", "Argentina"),
            ("Portugal", "Netherlands"),
            ("USA", "Germany"),
            ("Mexico", "Uruguay"),
            ("Morocco", "Spain"),
            ("Japan", "Croatia"),
            ("South Korea", "Portugal"),
            ("Australia", "France"),
            ("Turkey", "Netherlands"),
            ("Senegal", "England"),
            ("Canada", "Belgium"),
            ("Ecuador", "Brazil"),
            ("Ivory Coast", "Portugal"),
            ("Ghana", "Uruguay"),
            ("Norway", "Argentina"),
            ("Colombia", "France"),
            ("Switzerland", "Italy"),
            ("Austria", "Spain"),
        ]

    # ================================================================
    #  Utility: Get team profile
    # ================================================================

    def get_team_profile(self, team: str) -> dict:
        """Get a comprehensive profile for a team across all dimensions"""
        ctx = {"stage": "group", "venue_id": "nyc", "match_time": "afternoon"}
        scores = self._calculate_all_dimensions(team, "balanced_opponent", ctx)

        return {
            "team": team,
            "elo": ELO_RATINGS.get(team, 1500),
            "fifa_ranking": FIFA_RANKINGS.get(team, 99),
            "squad_value_m": SQUAD_VALUES.get(team, 0),
            "coach": COACH_STYLES_2026.get(team, {}).get("coach", "Unknown"),
            "style": COACH_STYLES_2026.get(team, {}).get("style", "balanced"),
            "tournament_experience": TOURNAMENT_EXPERIENCE.get(team, 0.30),
            "dimension_scores": {k: round(v, 4) for k, v in scores.items()},
            "weighted_total": round(
                sum(self.weights.get(dim, 0) * score for dim, score in scores.items()), 4
            ),
        }

    # ================================================================
    #  Utility: Compare two teams head-to-head
    # ================================================================

    def compare_teams(self, team_a: str, team_b: str, match_context: dict = None) -> dict:
        """Detailed head-to-head comparison"""
        if match_context is None:
            match_context = {"venue_id": "nyc", "match_time": "afternoon", "stage": "group"}

        prediction = self.predict_match(team_a, team_b, match_context)

        # Dimension-by-dimension comparison
        dimension_advantage = {}
        for dim in self.weights:
            score_a = prediction["scores_a"].get(dim, 0.5)
            score_b = prediction["scores_b"].get(dim, 0.5)
            dimension_advantage[dim] = {
                "team_a": score_a,
                "team_b": score_b,
                "advantage": team_a if score_a > score_b else (team_b if score_b > score_a else "even"),
                "margin": round(abs(score_a - score_b), 4),
            }

        return {
            "prediction": prediction,
            "dimension_advantage": dimension_advantage,
            "key_factors": self._identify_key_factors(prediction),
        }

    def _identify_key_factors(self, prediction: dict) -> list:
        """Identify the most impactful dimension differences"""
        factors = []
        for dim in self.weights:
            score_a = prediction["scores_a"].get(dim, 0.5)
            score_b = prediction["scores_b"].get(dim, 0.5)
            diff = score_a - score_b
            weight = self.weights[dim]
            impact = abs(diff) * weight
            factors.append({
                "dimension": dim,
                "weight": weight,
                "difference": round(diff, 4),
                "weighted_impact": round(impact, 4),
            })
        factors.sort(key=lambda x: x["weighted_impact"], reverse=True)
        return factors[:5]

    # ================================================================
    #  Utility: Group stage predictions
    # ================================================================

    def predict_group_stage(self, match_context: dict = None) -> dict:
        """Predict all group stage matches and standings"""
        if match_context is None:
            match_context = {"stage": "group", "venue_id": "nyc", "match_time": "afternoon"}

        group_predictions = {}
        for group_name, teams in WC2026_GROUPS.items():
            standings = {t: {"points": 0, "wins": 0, "draws": 0, "losses": 0, "predicted_points": 0.0} for t in teams}
            matches = []

            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    team_a, team_b = teams[i], teams[j]
                    result = self.predict_match(team_a, team_b, match_context)
                    matches.append({
                        "team_a": team_a,
                        "team_b": team_b,
                        "prob_a_win": result["prob_a_win"],
                        "prob_draw": result["prob_draw"],
                        "prob_b_win": result["prob_b_win"],
                    })

                    # Expected points
                    standings[team_a]["predicted_points"] += result["prob_a_win"] * 3 + result["prob_draw"] * 1
                    standings[team_b]["predicted_points"] += result["prob_b_win"] * 3 + result["prob_draw"] * 1

            sorted_standings = sorted(
                standings.items(), key=lambda x: x[1]["predicted_points"], reverse=True
            )
            group_predictions[group_name] = {
                "standings": [(t, round(s["predicted_points"], 2)) for t, s in sorted_standings],
                "matches": matches,
            }

        return group_predictions

    # ================================================================
    #  Utility: Top N predictions
    # ================================================================

    def predict_top_n(self, n: int = 10, n_simulations: int = 500) -> dict:
        """Quick tournament simulation returning top N teams"""
        result = self.simulate_tournament(n_simulations=n_simulations)
        top_n = dict(list(result["predictions"].items())[:n])
        return {"n_simulations": result["n_simulations"], "top_n": top_n}


# ===================================================================
#  QUICK TEST
# ===================================================================

def quick_test():
    """Run a sample prediction and print results"""
    engine = FormulaV11Engine()

    print("=" * 70)
    print("Formula V11.1 — EmoGlyph × SunTzu × Pratitya 三引擎融合")
    print("=" * 70)

    # Test 1: Single match prediction
    print("\n--- Test 1: Match Prediction ---")
    result = engine.predict_match("France", "Brazil")
    print(f"  {result['team_a']} vs {result['team_b']}")
    print(f"  {result['team_a']} win: {result['prob_a_win']:.1%}")
    print(f"  Draw:             {result['prob_draw']:.1%}")
    print(f"  {result['team_b']} win: {result['prob_b_win']:.1%}")
    print(f"  Upset alert:      {result['upset_alert']}")

    # Test 2: LightDarkBalance
    print(f"\n  LightDarkBalance ({result['team_a']}): LDB={result['ldb_a']['ldb']}, "
          f"Light={result['ldb_a']['light']}, Dark={result['ldb_a']['dark']}, "
          f"Confidence={result['ldb_a']['confidence']}")

    # Test 3: SunTzu
    print(f"  SunTzu ({result['team_a']}): {result['suntzu_a']['suntzu']} "
          f"(道={result['suntzu_a']['dao']}, 天={result['suntzu_a']['tian']}, "
          f"地={result['suntzu_a']['di']}, 將={result['suntzu_a']['jiang']}, 法={result['suntzu_a']['fa']})")

    # Test 4: Pratitya
    print(f"  Pratitya ({result['team_a']}): {result['pratitya_a']['pratitya']} "
          f"Adjustments: {result['pratitya_a']['adjustments']}")

    # Test 5: Dimension scores
    print(f"\n  Dimension Scores ({result['team_a']}):")
    for dim, score in sorted(result["scores_a"].items(), key=lambda x: x[1], reverse=True):
        weight = DIMENSION_WEIGHTS.get(dim, 0)
        print(f"    {dim:25s}: {score:.4f}  (weight: {weight:.0%})")

    # Test 6: Team profile
    print("\n--- Test 2: Team Profile ---")
    profile = engine.get_team_profile("Argentina")
    print(f"  Team: {profile['team']}")
    print(f"  Elo: {profile['elo']}, FIFA Ranking: {profile['fifa_ranking']}")
    print(f"  Coach: {profile['coach']} ({profile['style']})")
    print(f"  Squad Value: €{profile['squad_value_m']}M")
    print(f"  Weighted Total: {profile['weighted_total']}")

    # Test 7: Head-to-head comparison
    print("\n--- Test 3: Head-to-Head Comparison ---")
    comparison = engine.compare_teams("England", "Germany")
    print(f"  {comparison['prediction']['team_a']} vs {comparison['prediction']['team_b']}")
    print(f"  Key Factors:")
    for factor in comparison["key_factors"]:
        print(f"    {factor['dimension']:25s}: diff={factor['difference']:+.4f}, "
              f"impact={factor['weighted_impact']:.4f}")

    # Test 8: Group stage predictions
    print("\n--- Test 4: Group Stage Predictions (Group C) ---")
    groups = engine.predict_group_stage()
    group_c = groups.get("C", {})
    print(f"  Group C Standings:")
    for team, pts in group_c.get("standings", []):
        print(f"    {team:20s}: {pts:.1f} expected pts")

    # Test 9: Quick tournament simulation
    print("\n--- Test 5: Quick Tournament Simulation (100 iterations) ---")
    top = engine.predict_top_n(n=10, n_simulations=100)
    print(f"  Top 10 teams (win probability):")
    for team, probs in top["top_n"].items():
        print(f"    {team:20s}: Win={probs['win_probability']:.1%}, "
              f"Final={probs['final_probability']:.1%}, "
              f"Semi={probs['semi_probability']:.1%}")

    # Test 10: Monte Carlo Convergence Testing
    print("\n--- Test 10: Monte Carlo Convergence (100/200/500/1000 iterations) ---")
    convergence = engine.simulate_tournament_convergence(n_max=1000)
    print(f"  Convergence status: {convergence['convergence_status']}")
    print(f"  Detail: {convergence['convergence_detail']}")
    for cp_key, cp_data in convergence["checkpoints"].items():
        stability = cp_data["top5_stability"]
        stability_str = f"{stability:.4f}%" if stability is not None else "N/A (first checkpoint)"
        top3 = list(cp_data["predictions"].items())[:3]
        top3_str = ", ".join(f"{t}={d['win_probability']:.2%}" for t, d in top3)
        print(f"  Checkpoint {cp_key:>5s}: stability={stability_str}, top3=[{top3_str}]")
    ci = convergence["confidence_intervals"]["top_team"]
    print(f"  Top team: {ci['team']} — win_prob={ci['win_prob']:.2%}, "
          f"95% CI=({ci['ci_95'][0]:.2%}, {ci['ci_95'][1]:.2%})")
    if convergence["upset_detection"]:
        print(f"  Upset detections ({len(convergence['upset_detection'])}):")
        for upset in convergence["upset_detection"][:5]:
            print(f"    {upset['match']}: model={upset['model_prob']:.2%}, "
                  f"elo={upset['elo_prob']:.2%}, divergence={upset['divergence']:.1f}%")
    else:
        print("  No upsets detected (>15% divergence from Elo)")

    # Test 11: Host nation advantage
    print("\n--- Test 6: Host Nation Advantage ---")
    for host in ["USA", "Canada", "Mexico"]:
        home_ctx = {"venue_id": "nyc" if host == "USA" else ("toronto" if host == "Canada" else "mexicocity"), "stage": "group"}
        away_ctx = {"venue_id": "nyc", "stage": "group"}
        home_score = engine.score_home_advantage(host, home_ctx)
        away_score = engine.score_home_advantage(host, away_ctx)
        print(f"  {host}: Home={home_score:.2f}, Away-city={away_score:.2f}")

    # Test 11: Verify weight sum
    print("\n--- Test 7: Weight Verification ---")
    total_weight = sum(DIMENSION_WEIGHTS.values())
    print(f"  Total weight: {total_weight:.4f} (should be 1.0000)")
    ext_weight = sum(v for k, v in DIMENSION_WEIGHTS.items() if k in [
        "rest_recovery", "extreme_heat", "travel_fatigue", "home_advantage",
        "altitude_effect", "luck_factor", "schedule_density"
    ])
    int_weight = sum(v for k, v in DIMENSION_WEIGHTS.items() if k in [
        "elo_rating", "recent_form", "squad_depth", "coaching_style",
        "xfactor_players", "mental_psychological", "squad_value",
        "tournament_experience", "tactical_matchup"
    ])
    print(f"  External: {ext_weight:.2%}, Internal: {int_weight:.2%}")

    # Test 12: Verify all 48 teams have data
    print("\n--- Test 8: Data Completeness Check ---")
    all_teams = set()
    for group_teams in WC2026_GROUPS.values():
        all_teams.update(group_teams)

    data_dicts = {
        "ELO_RATINGS": ELO_RATINGS,
        "SQUAD_VALUES": SQUAD_VALUES,
        "RECENT_FORM": RECENT_FORM,
        "COACH_STYLES_2026": COACH_STYLES_2026,
        "SQUAD_DEPTH_DATA": SQUAD_DEPTH_DATA,
        "XFACTOR_DATA": XFACTOR_DATA,
        "TOURNAMENT_EXPERIENCE": TOURNAMENT_EXPERIENCE,
    }
    for name, data in data_dicts.items():
        missing = all_teams - set(data.keys())
        status = "OK" if not missing else f"MISSING: {missing}"
        print(f"  {name:25s}: {len(set(data.keys()) & all_teams)}/{len(all_teams)} teams — {status}")

    print("\n" + "=" * 70)
    print("Quick test complete!")
    print("=" * 70)

    # Test 13: Defensive counter-attack advantage
    print("\n--- Test 9: Defensive Counter-Attack Advantage ---")
    # Morocco (defensive_counter) vs Spain (attacking_possession) in Houston (WBGT > 30°C)
    houston_ctx = {"venue_id": "houston", "stage": "group", "venue_wbgt": 31.0, "venue_altitude": 0.0}
    neutral_ctx = {"venue_id": "nyc", "stage": "group", "venue_wbgt": 22.0, "venue_altitude": 0.0}

    bonus_morocco_houston = engine.score_defensive_counter_advantage("Morocco", "Spain", houston_ctx)
    bonus_spain_houston = engine.score_defensive_counter_advantage("Spain", "Morocco", houston_ctx)
    net_swing_houston = bonus_morocco_houston - bonus_spain_houston

    bonus_morocco_neutral = engine.score_defensive_counter_advantage("Morocco", "Spain", neutral_ctx)
    bonus_spain_neutral = engine.score_defensive_counter_advantage("Spain", "Morocco", neutral_ctx)

    print(f"  Morocco vs Spain in Houston (WBGT=31°C):")
    print(f"    Morocco bonus: {bonus_morocco_houston:+.2%} (expected ~+10%)")
    print(f"    Spain penalty: {bonus_spain_houston:+.2%} (expected ~-10%)")
    print(f"    Net swing:     {net_swing_houston:+.2%} (expected ~20%)")
    print(f"  Morocco vs Spain in neutral conditions (WBGT=22°C):")
    print(f"    Morocco bonus: {bonus_morocco_neutral:+.2%} (expected 0%)")
    print(f"    Spain penalty: {bonus_spain_neutral:+.2%} (expected 0%)")

    # Verify the bonus values
    assert abs(bonus_morocco_houston - 0.10) < 0.001, f"Morocco bonus should be ~10%, got {bonus_morocco_houston}"
    assert abs(bonus_spain_houston - (-0.10)) < 0.001, f"Spain penalty should be ~-10%, got {bonus_spain_houston}"
    assert abs(net_swing_houston - 0.20) < 0.001, f"Net swing should be ~20%, got {net_swing_houston}"
    assert bonus_morocco_neutral == 0.0, f"Morocco neutral bonus should be 0, got {bonus_morocco_neutral}"
    assert bonus_spain_neutral == 0.0, f"Spain neutral penalty should be 0, got {bonus_spain_neutral}"
    print("  All assertions passed!")


if __name__ == "__main__":
    quick_test()
