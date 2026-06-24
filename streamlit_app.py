import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from datetime import datetime
from formula_v9_ultimate import FormulaV9
from odds_data_layer import OddsIntegratedPredictor
from tournament_model import TournamentModel

try:
    from formula_v11_emoglyph import FormulaV11Engine
    _V11_AVAILABLE = True
except ImportError:
    _V11_AVAILABLE = False

try:
    from odds_data_layer import OddsDataLayer
    _ODDS_AVAILABLE = True
except ImportError:
    _ODDS_AVAILABLE = False

try:
    from wc2026_team_path_generator import TeamPathGenerator
    _PATH_GEN_AVAILABLE = True
except ImportError:
    _PATH_GEN_AVAILABLE = False

try:
    from wc2026_social_media_generator import SocialMediaGenerator
    _SOCIAL_GEN_AVAILABLE = True
except ImportError:
    _SOCIAL_GEN_AVAILABLE = False

try:
    from wc2026_group_combinations import GroupCombinationEngine
    _GROUP_COMBO_AVAILABLE = True
except ImportError:
    _GROUP_COMBO_AVAILABLE = False

try:
    from wc2026_deep_research import get_research_summary, apply_research_to_engine
    _DEEP_RESEARCH_AVAILABLE = True
except ImportError:
    _DEEP_RESEARCH_AVAILABLE = False

try:
    from wc2026_team_profiles import get_team_profile, get_team_coach, get_team_formation, get_team_strategy, get_team_main_player, get_team_strengths, get_team_weaknesses
    _TEAM_PROFILES_AVAILABLE = True
except ImportError:
    _TEAM_PROFILES_AVAILABLE = False

try:
    from wc2026_anime_card_renderer import generate_player_card_html, generate_team_cards_html
    _ANIME_CARDS_AVAILABLE = True
except ImportError:
    _ANIME_CARDS_AVAILABLE = False

try:
    from wc2026_venue_map import create_venue_map_3d, get_team_venues
    _VENUE_MAP_AVAILABLE = True
except ImportError:
    _VENUE_MAP_AVAILABLE = False

try:
    from wc2026_market_consensus import MarketConsensus, TOURNAMENT_WINNER_ODDS, GROUP_CONSENSUS_BASELINE
    _MARKET_CONSENSUS_AVAILABLE = True
except ImportError:
    _MARKET_CONSENSUS_AVAILABLE = False

try:
    from wc2026_portfolio_optimizer import PortfolioOptimizer, KellyCriterion, ROICalculator, ExplanationGenerator
    _PORTFOLIO_OPTIMIZER_AVAILABLE = True
except ImportError:
    _PORTFOLIO_OPTIMIZER_AVAILABLE = False

from languages import LANGUAGES, LANGUAGE_NAMES, get_text, get_language_name, get_available_languages, get_default_language
from player_translations import get_player_name, get_team_name
from user_registration_db import save_registration, get_registration_count

try:
    from compliance_language_map import compliant_text, check_compliance
    from jurisdiction_detector import JurisdictionDetector
    from disclaimer_engine import DisclaimerEngine
    from revenue_models import RevenueManager
    _COMPLIANCE_AVAILABLE = True
except ImportError:
    _COMPLIANCE_AVAILABLE = False

SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_PATH = SCRIPT_DIR / 'data' / 'wc2026_player_database.json'

def _get_app_version():
    try:
        from version_config import APP_VERSION as vc_version
        return vc_version
    except ImportError:
        pass
    try:
        if 'APP_VERSION' in st.secrets:
            return st.secrets['APP_VERSION']
    except Exception:
        pass
    return os.environ.get('APP_VERSION', 'international')

APP_VERSION = _get_app_version()

if _COMPLIANCE_AVAILABLE:
    jurisdiction_detector = JurisdictionDetector()
    disclaimer_engine = DisclaimerEngine()
    revenue_manager = RevenueManager()
else:
    jurisdiction_detector = None
    disclaimer_engine = None
    revenue_manager = None

COUNTRY_CODES = [
    ('+1', '🇺🇸 USA/Canada'),
    ('+44', '🇬🇧 UK'),
    ('+852', '🇭🇰 Hong Kong'),
    ('+86', '🇨🇳 中国'),
    ('+886', '🇹🇼 台灣'),
    ('+81', '🇯🇵 Japan'),
    ('+82', '🇰🇷 South Korea'),
    ('+65', '🇸🇬 Singapore'),
    ('+60', '🇲🇾 Malaysia'),
    ('+61', '🇦🇺 Australia'),
    ('+49', '🇩🇪 Germany'),
    ('+33', '🇫🇷 France'),
    ('+34', '🇪🇸 Spain'),
    ('+39', '🇮🇹 Italy'),
    ('+31', '🇳🇱 Netherlands'),
    ('+46', '🇸🇪 Sweden'),
    ('+47', '🇳🇴 Norway'),
    ('+351', '🇵🇹 Portugal'),
    ('+55', '🇧🇷 Brazil'),
    ('+52', '🇲🇽 Mexico'),
    ('+54', '🇦🇷 Argentina'),
    ('+56', '🇨🇱 Chile'),
    ('+57', '🇨🇴 Colombia'),
    ('+91', '🇮🇳 India'),
    ('+92', '🇵🇰 Pakistan'),
    ('+62', '🇮🇩 Indonesia'),
    ('+66', '🇹🇭 Thailand'),
    ('+84', '🇻🇳 Vietnam'),
    ('+63', '🇵🇭 Philippines'),
    ('+234', '🇳🇬 Nigeria'),
    ('+27', '🇿🇦 South Africa'),
    ('+971', '🇦🇪 UAE'),
    ('+966', '🇸🇦 Saudi Arabia'),
    ('+965', '🇰🇼 Kuwait'),
    ('+20', '🇪🇬 Egypt'),
]

st.set_page_config(
    page_title="World Cup 2026 Predictor",
    layout="wide",
    initial_sidebar_state="expanded"
)

DESIGN_TOKENS = {
    'primary_color': '#2E7D32',
    'primary_color_cn': '#FFB300',
    'primary_light': '#4CAF50',
    'secondary': '#F57F17',
    'background': '#FAFAFA',
    'card_bg': '#FFFFFF',
    'surface_variant': '#F5F5F5',
    'text_primary': '#1B1B1F',
    'text_secondary': '#49454F',
    'success': '#66BB6A',
    'warning': '#FFA726',
    'error': '#EF5350',
    'info': '#29B6F6',
    'border_radius': '8px',
    'shadow': '0 2px 4px rgba(0,0,0,0.1)',
    'font_size_body': '16px',
    'font_size_title': '24px',
}

DARK_TOKENS = {
    'primary_color': '#4CAF50',
    'primary_color_cn': '#FFB300',
    'primary_light': '#81C784',
    'secondary': '#FFB300',
    'background': '#121212',
    'card_bg': '#1E1E1E',
    'surface_variant': '#2C2C2C',
    'text_primary': '#ECEFF1',
    'text_secondary': '#B0BEC5',
    'success': '#66BB6A',
    'warning': '#FFA726',
    'error': '#EF5350',
    'info': '#29B6F6',
    'border_radius': '8px',
    'shadow': '0 2px 4px rgba(0,0,0,0.3)',
    'font_size_body': '16px',
    'font_size_title': '24px',
}

def get_design_tokens(lang: str, theme: str = 'dark') -> dict:
    tokens = DARK_TOKENS.copy() if theme == 'dark' else DESIGN_TOKENS.copy()
    if lang in ['zh_hant', 'zh_hans']:
        tokens['primary_color'] = tokens['primary_color_cn']
    return tokens

def premium_badge():
    return st.markdown('<span style="background:linear-gradient(135deg,#FFD700,#FFA000);color:#000;padding:2px 8px;border-radius:4px;font-size:0.75em;font-weight:bold;">⭐ PREMIUM</span>', unsafe_allow_html=True)

def premium_gate(feature_name: str):
    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']
    if revenue_manager:
        jurisdiction = st.session_state.get('user_jurisdiction', 'other')
        tiers = revenue_manager.get_pricing_tiers(jurisdiction)
        st.markdown(f"""
        <div style="border:2px dashed #FFB300;border-radius:8px;padding:1.5rem;text-align:center;background:rgba(255,179,0,0.05);">
            <p style="font-size:1.2rem;margin:0;">⭐ {feature_name}</p>
            <p style="color:#FFB300;margin:0.5rem 0 0 0;">{'升級至 Premium 解鎖' if is_cn else 'Upgrade to unlock'}</p>
        </div>
        """, unsafe_allow_html=True)
        tier_cols = st.columns(len(tiers))
        for col, tier in zip(tier_cols, tiers):
            with col:
                st.markdown(f"**{tier['name']}** — {tier['price']}")
                if tier.get('stripe_link'):
                    st.link_button(
                        '🛒 ' + ('訂閱' if is_cn else 'Subscribe'),
                        tier['stripe_link'],
                    )
    else:
        st.markdown(f"""
        <div style="border:2px dashed #FFB300;border-radius:8px;padding:1.5rem;text-align:center;background:rgba(255,179,0,0.05);">
            <p style="font-size:1.2rem;margin:0;">⭐ {feature_name}</p>
            <p style="color:#FFB300;margin:0.5rem 0 0 0;">{'升級至 Premium 解鎖' if is_cn else 'Upgrade to Premium to unlock'}</p>
        </div>
        """, unsafe_allow_html=True)

def apply_custom_css(lang: str, theme: str = 'dark'):
    tokens = get_design_tokens(lang, theme)
    if theme == 'dark':
        st.markdown(f"""
        <style>
            .main {{
                background-color: {tokens['background']};
                color: {tokens['text_primary']};
            }}
            .stApp {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                color: {tokens['text_primary']};
            }}
            h1 {{
                font-size: {tokens['font_size_title']};
                color: {tokens['text_primary']};
                font-weight: 600;
            }}
            h2, h3 {{
                color: {tokens['text_primary']};
            }}
            p, span, label {{
                color: {tokens['text_primary']};
            }}
            .stMetric {{
                background-color: {tokens['card_bg']};
                border-radius: {tokens['border_radius']};
                box-shadow: {tokens['shadow']};
                padding: 1rem;
                color: {tokens['text_primary']};
            }}
            .stMetric > div > div > div {{
                color: {tokens['text_primary']};
            }}
            .stButton > button {{
                background-color: {tokens['primary_color']};
                color: white;
                border-radius: {tokens['border_radius']};
                font-weight: 500;
                transition: all 0.2s ease;
            }}
            .stButton > button:hover {{
                background-color: {tokens['secondary']};
                color: #121212;
            }}
            .stSelectbox, .stMultiSelect {{
                border-radius: {tokens['border_radius']};
            }}
            [data-testid="stSidebar"] {{
                background-color: {tokens['surface_variant']};
            }}
            .stTab {{
                background-color: {tokens['surface_variant']};
            }}
            .stSuccess {{
                background-color: #1B3A1B;
                border-left: 4px solid {tokens['success']};
                color: #C8E6C9;
            }}
            .stInfo {{
                background-color: #0D2744;
                border-left: 4px solid {tokens['info']};
                color: #B3E5FC;
            }}
            .stWarning {{
                background-color: #3E2723;
                border-left: 4px solid {tokens['warning']};
                color: #FFE0B2;
            }}
            .stError {{
                background-color: #3B1010;
                border-left: 4px solid {tokens['error']};
                color: #FFCDD2;
            }}
            .card {{
                background-color: {tokens['card_bg']};
                border-radius: {tokens['border_radius']};
                box-shadow: {tokens['shadow']};
                padding: 1.5rem;
                margin-bottom: 1rem;
                color: {tokens['text_primary']};
            }}
            .stDataFrame {{
                color: {tokens['text_primary']};
            }}
            .stTextInput > div > div > input {{
                background-color: {tokens['card_bg']};
                color: {tokens['text_primary']};
            }}
            .stNumberInput > div > div > input {{
                background-color: {tokens['card_bg']};
                color: {tokens['text_primary']};
            }}
            .stRadio > div {{
                color: {tokens['text_primary']};
            }}
            .stCheckbox {{
                color: {tokens['text_primary']};
            }}
            .stCaption {{
                color: {tokens['text_secondary']};
            }}
            .news-card {{
                background-color: {tokens['card_bg']};
                border-radius: {tokens['border_radius']};
                box-shadow: {tokens['shadow']};
                padding: 1rem;
                margin-bottom: 1rem;
                color: {tokens['text_primary']};
            }}
            .news-card .source {{
                font-weight: bold;
                color: {tokens['primary_color']};
            }}
            .news-card .timestamp {{
                color: {tokens['text_secondary']};
                font-size: 0.85rem;
            }}
            .news-card .content {{
                margin-top: 0.5rem;
                color: {tokens['text_primary']};
            }}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <style>
            .main {{
                background-color: {tokens['background']};
            }}
            .stApp {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }}
            h1 {{
                font-size: {tokens['font_size_title']};
                color: {tokens['text_primary']};
                font-weight: 600;
            }}
            h2, h3 {{
                color: {tokens['text_primary']};
            }}
            .stMetric {{
                background-color: {tokens['card_bg']};
                border-radius: {tokens['border_radius']};
                box-shadow: {tokens['shadow']};
                padding: 1rem;
            }}
            .stButton > button {{
                background-color: {tokens['primary_color']};
                color: white;
                border-radius: {tokens['border_radius']};
                font-weight: 500;
                transition: all 0.2s ease;
            }}
            .stButton > button:hover {{
                background-color: {tokens['primary_light']};
                color: white;
            }}
            .stSelectbox, .stMultiSelect {{
                border-radius: {tokens['border_radius']};
            }}
            [data-testid="stSidebar"] {{
                background-color: {tokens['surface_variant']};
            }}
            .stTab {{
                background-color: {tokens['surface_variant']};
            }}
            .stSuccess {{
                background-color: #E8F5E9;
                border-left: 4px solid {tokens['success']};
            }}
            .stInfo {{
                background-color: #E1F5FE;
                border-left: 4px solid {tokens['info']};
            }}
            .stWarning {{
                background-color: #FFF3E0;
                border-left: 4px solid {tokens['warning']};
            }}
            .stError {{
                background-color: #FFEBEE;
                border-left: 4px solid {tokens['error']};
            }}
            .card {{
                background-color: {tokens['card_bg']};
                border-radius: {tokens['border_radius']};
                box-shadow: {tokens['shadow']};
                padding: 1.5rem;
                margin-bottom: 1rem;
            }}
            .news-card {{
                background-color: {tokens['card_bg']};
                border-radius: {tokens['border_radius']};
                box-shadow: {tokens['shadow']};
                padding: 1rem;
                margin-bottom: 1rem;
            }}
            .news-card .source {{
                font-weight: bold;
                color: {tokens['primary_color']};
            }}
            .news-card .timestamp {{
                color: {tokens['text_secondary']};
                font-size: 0.85rem;
            }}
            .news-card .content {{
                margin-top: 0.5rem;
                color: {tokens['text_primary']};
            }}
        </style>
        """, unsafe_allow_html=True)

def init_language():
    if 'language' not in st.session_state:
        st.session_state.language = get_default_language(APP_VERSION)
    return st.session_state.language

def set_language(lang: str):
    st.session_state.language = lang
    st.rerun()

def init_theme():
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    return st.session_state.theme

@st.cache_resource
def load_engine():
    try:
        engine = FormulaV9(str(DATA_PATH))
        if len(engine.players) == 0:
            return None
        return engine
    except Exception as e:
        return None

@st.cache_resource
def load_tournament():
    try:
        return TournamentModel(str(DATA_PATH))
    except Exception as e:
        return None

engine = load_engine()
tournament = load_tournament()

@st.cache_resource
def load_odds_predictor():
    return OddsIntegratedPredictor(alpha=0.6)

odds_predictor = load_odds_predictor()

@st.cache_resource
def load_v11_engine():
    if not _V11_AVAILABLE:
        return None
    try:
        return FormulaV11Engine()
    except Exception:
        return None

v11_engine = load_v11_engine()

def t(key: str) -> str:
    return get_text(key, st.session_state.language)

def show_disclaimers():
    if not disclaimer_engine:
        return
    jurisdiction = st.session_state.get('user_jurisdiction', 'other')
    disclaimers = disclaimer_engine.get_all_disclaimers(jurisdiction, APP_VERSION)
    for d in disclaimers:
        label_map = {
            'prediction': '⚠️ Prediction Disclaimer',
            'anti_gambling': '🚫 Anti-Gambling Notice',
            'data_privacy': '🔒 Data Privacy',
            'ai_transparency': '🤖 AI Transparency',
        }
        label = label_map.get(d['type'], d['type'].replace('_', ' ').title())
        with st.sidebar.expander(label):
            st.caption(d['text'])

def show_affiliate_section():
    tokens = get_design_tokens(st.session_state.language, init_theme())
    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']

    if revenue_manager:
        jurisdiction = st.session_state.get('user_jurisdiction', 'other')
        products = revenue_manager.get_compliant_affiliate_products(jurisdiction)
    else:
        if is_cn:
            products = [
                {"name": "⚽ 世界盃正版球衣", "url": "https://s.click.taobao.com/wc2026_jersey", "description": "官方授權球衣，支持你嘅球隊"},
                {"name": "🎫 世界盃門票", "url": "https://s.click.taobao.com/wc2026_tickets", "description": "2026 美加墨世界盃現場門票"},
                {"name": "✈️ 世界盃旅行套餐", "url": "https://s.click.taobao.com/wc2026_travel", "description": "機票+酒店+門票一站式服務"},
            ]
        else:
            products = [
                {"name": "⚽ Official WC Jersey", "url": "https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup/canadamexicousa2026/shop/jerseys", "description": "Official licensed jerseys"},
                {"name": "🎫 Match Tickets", "url": "https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup/canadamexicousa2026/tickets", "description": "FIFA World Cup 2026 tickets"},
                {"name": "✈️ Travel Packages", "url": "https://www.booking.com/searchresults.html?ss=world+cup+2026", "description": "Flight + Hotel + Ticket bundles"},
            ]

    st.markdown(f"### 🛒 {'世界盃周邊推薦' if is_cn else 'World Cup Shop'}")
    cols = st.columns(len(products))
    for col, product in zip(cols, products):
        with col:
            name = product.get('name', '')
            url = product.get('url', '')
            desc = product.get('description', '')
            st.markdown(f"""
            <div style="background:{tokens['card_bg']};border-radius:8px;padding:1rem;text-align:center;border:1px solid {tokens.get('surface_variant', '#333')};">
                <h4>{name}</h4>
                <p style="font-size:0.85rem;color:{tokens['text_secondary']};">{desc}</p>
                <a href="{url}" target="_blank" style="background:{tokens['primary_color']};color:white;padding:8px 16px;border-radius:4px;text-decoration:none;display:inline-block;">{'查看詳情' if is_cn else 'Shop Now'}</a>
            </div>
            """, unsafe_allow_html=True)

def show_admin_page():
    lang = init_language()
    theme = init_theme()
    apply_custom_css(lang, theme)
    tokens = get_design_tokens(lang, theme)

    if 'admin_authed' not in st.session_state:
        st.session_state.admin_authed = False

    if not st.session_state.admin_authed:
        admin_pw = st.secrets.get('ADMIN_PASSWORD', 'beeverse2026') if hasattr(st, 'secrets') else 'beeverse2026'
        pw = st.text_input('🔒 Admin Password', type='password')
        if st.button('Login'):
            if pw == admin_pw:
                st.session_state.admin_authed = True
                st.rerun()
            else:
                st.error('Wrong password')
        return

    from user_registration_db import get_all_registrations, get_registration_stats
    import io

    stats = get_registration_stats()

    st.markdown(f"""
    <div style="text-align: center; padding: 2rem;">
        <h1>🔐 Admin Panel</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Registrations", stats['total'])
    with col2:
        st.metric("🇨🇳 China Version", stats['china'])
    with col3:
        st.metric("🌍 International Version", stats['international'])
    with col4:
        st.metric("📅 Today", stats['today'])

    st.divider()

    rows = get_all_registrations()
    if rows:
        df = pd.DataFrame(rows, columns=['ID', 'Name', 'Email', 'Phone', 'Language', 'Version', 'Registered At'])
        st.dataframe(df, width='stretch', hide_index=True)

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="📥 Export CSV",
            data=csv_data,
            file_name=f"registrations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            width='stretch'
        )
    else:
        st.info("No registrations yet")

    if st.button("🚪 Logout"):
        st.session_state.admin_authed = False
        st.rerun()

def show_engagement_gate():
    """Like-Share-Subscribe gate — replaces registration form.

    Honor-based: clicking any button in a category marks that step complete.
    After all 3 steps are complete, the "Enter the App" button becomes active.
    """
    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']
    theme = init_theme()
    apply_custom_css(lang, theme)
    tokens = get_design_tokens(lang, theme)

    if 'engagement_like' not in st.session_state:
        st.session_state.engagement_like = False
    if 'engagement_share' not in st.session_state:
        st.session_state.engagement_share = False
    if 'engagement_subscribe' not in st.session_state:
        st.session_state.engagement_subscribe = False

    is_china = APP_VERSION == 'china'

    app_url = "https://beeverseworldcup2026.streamlit.app/"
    share_text_en = "🏆 Check out this AI World Cup 2026 Predictor! 17 factors, 5000+ simulations, every team's path analyzed. Free to use! 🔮⚽ #WorldCup2026 #AIPrediction"
    share_text_hans = "🏆 2026世界杯AI预测器！17个因素、5000+次模拟、每支球队路径分析。免费使用！🔮⚽ #世界杯2026 #AI预测"
    share_text_hant = "🏆 2026世界盃AI預測器！17個因素、5000+次模擬、每支球隊路徑分析。免費使用！🔮⚽ #世界盃2026 #AI預測"
    if lang == 'zh_hans':
        share_text = share_text_hans
    elif lang == 'zh_hant':
        share_text = share_text_hant
    else:
        share_text = share_text_en
    import urllib.parse
    share_text_encoded = urllib.parse.quote(share_text)
    url_encoded = urllib.parse.quote(app_url)

    st.markdown(f"""
    <div style="text-align:center;padding:2rem 1rem 1rem 1rem;">
        <h1>🏆 {"2026 世界盃 AI 預測" if is_cn else "World Cup 2026 AI Predictor"}</h1>
        <p style="font-size:1.1rem;color:{tokens['text_secondary']};">
            {"免費使用 — 只需支持我哋！" if is_cn else "Free access — just support us!"}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Step 1: Like ─────────────────────────────────────────────────
    like_done = st.session_state.engagement_like
    step1_label = ("步驟 1：👍 讚好" if is_cn else "Step 1: 👍 Like") + (" ✅" if like_done else "")
    st.markdown(f"### {step1_label}")
    st.caption(("點擊以下任何一個平台讚好" if is_cn else "Click Like on any platform below"))

    like_cols = st.columns(4)
    if is_china:
        like_buttons = [
            ("微博", "https://weibo.com/", "#E6162D"),
            ("抖音", "https://www.douyin.com/", "#010101"),
            ("微信", "https://weixin.qq.com/", "#07C160"),
            ("B站", "https://www.bilibili.com/", "#FB7299"),
        ]
    else:
        like_buttons = [
            ("Twitter/X", "https://twitter.com/", "#1DA1F2"),
            ("Facebook", "https://www.facebook.com/", "#1877F2"),
            ("Weibo", "https://weibo.com/", "#E6162D"),
            ("Douyin", "https://www.douyin.com/", "#010101"),
        ]
    for col, (name, url, color) in zip(like_cols, like_buttons):
        with col:
            st.markdown(
                f'<a href="{url}" target="_blank" style="display:block;text-align:center;text-decoration:none;'
                f'padding:10px 4px;background:{color};color:white;border-radius:6px;font-size:0.85rem;">'
                f'👍 {name}</a>',
                unsafe_allow_html=True,
            )
    if st.button(("我已讚好 ✓" if is_cn else "I Liked ✓"), key="confirm_like", use_container_width=True):
        st.session_state.engagement_like = True
        st.rerun()

    st.markdown("---")

    # ── Step 2: Share ────────────────────────────────────────────────
    share_done = st.session_state.engagement_share
    step2_label = ("步驟 2：📤 分享" if is_cn else "Step 2: 📤 Share") + (" ✅" if share_done else "")
    st.markdown(f"### {step2_label}")
    st.caption(("分享到任何平台" if is_cn else "Share with your friends"))

    share_cols = st.columns(4)
    if is_china:
        share_buttons = [
            ("微博", f"https://service.weibo.com/share/share.php?url={url_encoded}&title={share_text_encoded}", "#E6162D"),
            ("微信\n(複製)", f"javascript:void(0)", "#07C160"),
            ("抖音", "https://www.douyin.com/", "#010101"),
            ("QQ", f"https://connect.qq.com/widget/shareqq/index.html?url={url_encoded}&title={share_text_encoded}", "#12B7F5"),
        ]
    else:
        share_buttons = [
            ("Twitter/X", f"https://twitter.com/intent/tweet?url={url_encoded}&text={share_text_encoded}", "#1DA1F2"),
            ("Facebook", f"https://www.facebook.com/sharer/sharer.php?u={url_encoded}", "#1877F2"),
            ("WhatsApp", f"https://wa.me/?text={share_text_encoded}%20{url_encoded}", "#25D366"),
            ("WeChat\n(複製)", "javascript:void(0)", "#07C160"),
        ]
    for col, (name, url, color) in zip(share_cols, share_buttons):
        with col:
            display_name = name.replace("\n", "<br>")
            st.markdown(
                f'<a href="{url}" target="_blank" style="display:block;text-align:center;text-decoration:none;'
                f'padding:10px 4px;background:{color};color:white;border-radius:6px;font-size:0.85rem;">'
                f'📤 {display_name}</a>',
                unsafe_allow_html=True,
            )
    st.caption(f"📋 {share_text}")
    if st.button(("我已分享 ✓" if is_cn else "I Shared ✓"), key="confirm_share", use_container_width=True):
        st.session_state.engagement_share = True
        st.rerun()

    st.markdown("---")

    # ── Step 3: Subscribe ────────────────────────────────────────────
    sub_done = st.session_state.engagement_subscribe
    step3_label = ("步驟 3：🔔 訂閱/關注" if is_cn else "Step 3: 🔔 Subscribe/Follow") + (" ✅" if sub_done else "")
    st.markdown(f"### {step3_label}")
    st.caption(("訂閱或關注任何平台" if is_cn else "Subscribe or Follow on any platform"))

    sub_cols = st.columns(4)
    if is_china:
        sub_buttons = [
            ("微博", "https://weibo.com/", "#E6162D"),
            ("微信", "https://weixin.qq.com/", "#07C160"),
            ("抖音", "https://www.douyin.com/", "#010101"),
            ("B站", "https://www.bilibili.com/", "#FB7299"),
        ]
    else:
        sub_buttons = [
            ("Twitter/X", "https://twitter.com/", "#1DA1F2"),
            ("YouTube", "https://www.youtube.com/", "#FF0000"),
            ("WeChat", "https://weixin.qq.com/", "#07C160"),
            ("Douyin", "https://www.douyin.com/", "#010101"),
        ]
    for col, (name, url, color) in zip(sub_cols, sub_buttons):
        with col:
            st.markdown(
                f'<a href="{url}" target="_blank" style="display:block;text-align:center;text-decoration:none;'
                f'padding:10px 4px;background:{color};color:white;border-radius:6px;font-size:0.85rem;">'
                f'🔔 {name}</a>',
                unsafe_allow_html=True,
            )
    if st.button(("我已訂閱 ✓" if is_cn else "I Subscribed ✓"), key="confirm_subscribe", use_container_width=True):
        st.session_state.engagement_subscribe = True
        st.rerun()

    st.markdown("---")

    # ── Enter button ─────────────────────────────────────────────────
    all_done = st.session_state.engagement_like and st.session_state.engagement_share and st.session_state.engagement_subscribe
    if all_done:
        st.success("🎉 " + ("多謝支持！現在可以進入應用。" if is_cn else "Thank you for your support! You can now enter the app."))
        if st.button("✅ " + ("進入應用" if is_cn else "Enter the App"), key="enter_app", use_container_width=True, type="primary"):
            st.session_state.registered = True
            st.rerun()
    else:
        remaining = 3 - sum([st.session_state.engagement_like, st.session_state.engagement_share, st.session_state.engagement_subscribe])
        st.info(("請完成所有 3 個步驟以進入應用" if is_cn else "Please complete all 3 steps to enter")
                + f" ({remaining} " + ("步剩餘" if is_cn else "remaining") + ")")
        st.button("✅ " + ("進入應用" if is_cn else "Enter the App"), key="enter_app_disabled", disabled=True, use_container_width=True)


def main():
    if st.session_state.get('show_admin', False):
        show_admin_page()
        return

    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']
    theme = init_theme()

    if 'registered' not in st.session_state:
        st.session_state.registered = False

    if 'is_premium' not in st.session_state:
        st.session_state.is_premium = False

    if 'user_jurisdiction' not in st.session_state:
        st.session_state.user_jurisdiction = 'other'

    # Engagement gate: user must complete Like/Share/Subscribe before entering
    if not st.session_state.registered:
        show_engagement_gate()
        return

    apply_custom_css(lang, theme)

    show_disclaimer_banner()

    if APP_VERSION == 'international' and 'cookie_consent' not in st.session_state:
        st.markdown("""
        <div style="position:fixed;bottom:0;left:0;right:0;background:#1E1E1E;padding:12px 24px;
        z-index:9999;display:flex;align-items:center;justify-content:space-between;border-top:1px solid #4CAF50;">
            <span style="color:#ECEFF1;font-size:14px;">🍪 We use cookies to improve your experience. 
            <a href="#" style="color:#4CAF50;">Learn more</a></span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Accept Cookies", key="cookie_accept"):
            st.session_state.cookie_consent = True
            st.rerun()

    with st.sidebar:
        st.markdown(f"### {t('theme_toggle')}")
        theme_options = [t('theme_dark'), t('theme_light')]
        theme_values = ['dark', 'light']
        current_theme_idx = theme_values.index(st.session_state.get('theme', 'dark'))
        selected_theme_label = st.radio(
            t('theme_toggle'),
            theme_options,
            index=current_theme_idx,
            horizontal=True,
            label_visibility="collapsed"
        )
        selected_theme = theme_values[theme_options.index(selected_theme_label)]
        st.session_state.theme = selected_theme

        st.markdown("---")
        st.markdown(f"### {t('language')}")
        available_langs = get_available_languages(APP_VERSION)
        lang_options = list(available_langs.keys())
        lang_labels = [available_langs[l] for l in lang_options]
        current_idx = lang_options.index(lang) if lang in lang_options else 0
        selected_lang_label = st.selectbox(
            t('select_language'),
            lang_labels,
            index=current_idx,
            label_visibility="collapsed"
        )
        selected_lang = lang_options[lang_labels.index(selected_lang_label)]
        if selected_lang != lang:
            set_language(selected_lang)

        st.markdown("---")
        st.title(f"🏆 {t('sidebar_title')}")
        st.markdown("---")

        if engine is None:
            st.error(f"❌ {t('engine_load_error')}")
            st.info(t('data_file_missing'))
            return

        pages = [
            t('home'),
            t('match_prediction'),
            t('team_comparison'),
            t('player_database'),
            t('tournament_simulation'),
            t('model_analysis'),
            '🔬 ' + ('運作原理' if is_cn else 'How It Works'),
            t('news_page'),
            t('xfactor_page'),
            t('team_profiles_page'),
            '🗺️ ' + ('球隊路徑策略' if is_cn else 'Team Path Strategy'),
            '🧩 ' + ('小組組合分析' if is_cn else 'Group Combinations'),
            '💼 ' + ('投資組合' if is_cn else 'Investment Portfolio'),
        ]
        page = st.radio(t('navigation'), pages)

        st.markdown("---")
        st.markdown("### 📤 Share")
        if APP_VERSION == 'china':
            st.markdown("""
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <a href="https://service.weibo.com/share/share.php?url=https://beeverseworldcup2026.streamlit.app/&title=2026世界杯预测" target="_blank" style="text-decoration:none;padding:4px 12px;background:#E6162D;color:white;border-radius:4px;font-size:12px;">微博</a>
                <a href="javascript:void(0)" onclick="copyToClipboard('https://beeverseworldcup2026.streamlit.app/')" style="text-decoration:none;padding:4px 12px;background:#07C160;color:white;border-radius:4px;font-size:12px;">微信</a>
                <a href="https://www.douyin.com/" target="_blank" style="text-decoration:none;padding:4px 12px;background:#010101;color:white;border-radius:4px;font-size:12px;">抖音</a>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <a href="https://twitter.com/intent/tweet?url=https://beeverseworldcup2026.streamlit.app/&text=2026%20World%20Cup%20Predictor" target="_blank" style="text-decoration:none;padding:4px 12px;background:#1DA1F2;color:white;border-radius:4px;font-size:12px;">Twitter/X</a>
                <a href="https://www.facebook.com/sharer/sharer.php?u=https://beeverseworldcup2026.streamlit.app/" target="_blank" style="text-decoration:none;padding:4px 12px;background:#1877F2;color:white;border-radius:4px;font-size:12px;">Facebook</a>
                <a href="https://wa.me/?text=2026%20World%20Cup%20Predictor%20https://beeverseworldcup2026.streamlit.app/" target="_blank" style="text-decoration:none;padding:4px 12px;background:#25D366;color:white;border-radius:4px;font-size:12px;">WhatsApp</a>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        show_affiliate_section()

        st.divider()
        show_disclaimers()

        if disclaimer_engine:
            jurisdiction = st.session_state.get('user_jurisdiction', 'other')
            anti_gambling = disclaimer_engine.get_anti_gambling_notice(jurisdiction)
            if anti_gambling:
                st.sidebar.markdown(f"""
                <div style="background:#3B1010;border:1px solid #EF5350;border-radius:8px;padding:0.75rem;margin-top:0.5rem;">
                    <p style="color:#FFCDD2;font-size:0.8rem;margin:0;">🚫 {anti_gambling}</p>
                </div>
                """, unsafe_allow_html=True)

        st.divider()
        if st.button("🔒", key="admin_lock"):
            st.session_state.show_admin = not st.session_state.get('show_admin', False)

    try:
        if page == t('home'):
            show_home()
        elif page == t('match_prediction'):
            show_match_prediction()
        elif page == t('team_comparison'):
            show_team_comparison()
        elif page == t('player_database'):
            show_player_database()
        elif page == t('tournament_simulation'):
            show_tournament_simulation()
        elif page == t('model_analysis'):
            show_model_analysis()
        elif page == '🔬 ' + ('運作原理' if is_cn else 'How It Works'):
            show_methodology()
        elif page == t('news_page'):
            show_news()
        elif page == t('xfactor_page'):
            show_xfactor()
        elif page == t('team_profiles_page'):
            show_team_profiles()
        elif page == '🗺️ ' + ('球隊路徑策略' if is_cn else 'Team Path Strategy'):
            show_team_path_strategy()
        elif page == '🧩 ' + ('小組組合分析' if is_cn else 'Group Combinations'):
            show_group_combinations()
        elif page == '💼 ' + ('投資組合' if is_cn else 'Investment Portfolio'):
            show_investment_portfolio()
    except Exception as e:
        st.error(f"❌ {t('page_error')}: {str(e)}")
        st.info(t('try_refresh'))

def show_disclaimer_banner():
    """Show big-data projection disclaimer banner on every page"""
    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']
    if 'disclaimer_dismissed' not in st.session_state:
        st.session_state.disclaimer_dismissed = False
    
    if not st.session_state.disclaimer_dismissed:
        if is_cn:
            warning_text = "⚠️ 这是基于大数据分析的AI统计概率推算，并非博彩建议。结果为概率估算，不构成任何保证。"
        else:
            warning_text = "⚠️ This is an AI statistical projection based on big data analysis. It is NOT gambling advice. Results are probabilistic estimates, not guarantees."
        
        st.markdown(f"""
        <div style="background:rgba(255,179,0,0.15);border:1px solid #FFB300;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
            <p style="margin:0;color:#FFB300;font-size:0.9rem;">{warning_text}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✓ " + ("我已知晓" if is_cn else "I understand"), key="dismiss_disclaimer"):
            st.session_state.disclaimer_dismissed = True
            st.rerun()

def show_methodology():
    """How It Works — methodology explanation page"""
    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']

    st.title("🔬 " + ("運作原理" if is_cn else "How Our AI Predicts the World Cup"))

    st.markdown(("我們的模型分析 **17+1 個因素**，分為 2 大類別，預測比賽結果。\n每次預測運行 **5,000+ 次** 蒙特卡洛模擬。"
                 if is_cn else
                 "Our model analyzes **17+1 factors** across 2 categories to predict match outcomes.\nWe run **5,000+ Monte Carlo simulations** for each prediction."))

    st.divider()

    # WHAT WE ANALYZE
    st.header("📊 " + ("我們分析什麼" if is_cn else "WHAT WE ANALYZE"))

    st.subheader(("球隊實力（佔預測 64%）" if is_cn else "Team Strength (64% of prediction)"))
    team_factors = [
        ("📊", ("歷史評級 (10%)" if is_cn else "Historical Rating (10%)"), ("球隊長期實力如何？" if is_cn else "How strong is this team over time?")),
        ("📈", ("近期狀態 (8%)" if is_cn else "Recent Form (8%)"), ("最近贏球了嗎？" if is_cn else "Are they winning lately?")),
        ("👥", ("陣容深度 (10%)" if is_cn else "Squad Depth (10%)"), ("替補席能頂上嗎？" if is_cn else "Can their bench deliver?")),
        ("🧠", ("教練水平 (8%)" if is_cn else "Coaching (8%)"), ("戰術佈置如何？" if is_cn else "How good is the tactical setup?")),
        ("⭐", ("X因子球員 (8%)" if is_cn else "X-Factor Players (8%)"), ("誰能改變比賽？" if is_cn else "Who can change the game?")),
        ("💪", ("心理素質 (5%)" if is_cn else "Mental Strength (5%)"), ("能扛住壓力嗎？" if is_cn else "Can they handle pressure?")),
        ("💰", ("陣容身價 (7%)" if is_cn else "Squad Value (7%)"), ("天賦有多高？" if is_cn else "How talented is the roster?")),
        ("🏅", ("大賽經驗 (5%)" if is_cn else "Big-Game Experience (5%)"), ("以前來過嗎？" if is_cn else "Have they been here before?")),
        ("⚔️", ("風格對位 (5%)" if is_cn else "Style Matchup (5%)"), ("風格相剋嗎？" if is_cn else "Does their style counter the opponent?")),
    ]
    for emoji, name, desc in team_factors:
        st.markdown(f"  {emoji} **{name}** — {desc}")

    st.subheader(("比賽條件（佔預測 36%）" if is_cn else "Match Conditions (36% of prediction)"))
    match_factors = [
        ("🔋", ("休息恢復 (12%)" if is_cn else "Recovery Time (12%)"), ("球員有多新鮮？" if is_cn else "How fresh are the players?")),
        ("🌡️", ("極端高溫 (5%)" if is_cn else "Extreme Heat (5%)"), ("能扛住酷熱嗎？" if is_cn else "Can they handle the summer?")),
        ("✈️", ("旅途距離 (4%)" if is_cn else "Travel Distance (4%)"), ("飛了多遠？" if is_cn else "How far did they fly?")),
        ("🏟️", ("主場優勢 (4%)" if is_cn else "Home Advantage (4%)"), ("主場作戰？" if is_cn else "Playing at home?")),
        ("⛰️", ("海拔效應 (3%)" if is_cn else "Altitude (3%)"), ("墨西哥城空氣稀薄" if is_cn else "Mexico City's thin air")),
        ("🍀", ("運氣因子 (2%)" if is_cn else "Luck Factor (2%)"), ("隨機事件" if is_cn else "Random events")),
        ("📅", ("賽程密度 (1%)" if is_cn else "Schedule (1%)"), ("比賽有多密集？" if is_cn else "How tight are the games?")),
        ("🏗️", ("小組策略 (3%)" if is_cn else "Group Strategy (3%)"), ("新！第三場能否輪換休息？" if is_cn else "NEW: Can they rest in match 3?")),
    ]
    for emoji, name, desc in match_factors:
        st.markdown(f"  {emoji} **{name}** — {desc}")

    st.divider()

    # MARKET INTELLIGENCE
    st.header("🎰 " + ("市場情報" if is_cn else "MARKET INTELLIGENCE"))

    st.markdown(("我們還整合全球市場信號作為「現實檢驗」。\n全球數千名專業分析師根據內幕消息、傷情報告和實時信息設定價格。\n\n我們的模型混合：**AI 預測 (85%) + 市場信號 (15%)**\n市場權重隨着比賽臨近而增加（更多信息 = 更大權重）。\n\n⚠️ 市場數據僅作為統計輸入使用。\n前端絕不顯示任何博彩信息。"
                 if is_cn else
                 "We also incorporate global market signals as a \"reality check\".\nThousands of professional analysts worldwide set prices based on\ninsider knowledge, injury reports, and real-time information.\n\nOur model blends: **AI Prediction (85%) + Market Signal (15%)**\nThe market weight increases as kickoff approaches (more info = more weight).\n\n⚠️ Market data is used ONLY as a statistical input.\nNo gambling information is ever displayed."))

    st.divider()

    # HOW SIMULATIONS WORK
    st.header("🔄 " + ("模擬如何運作" if is_cn else "HOW SIMULATIONS WORK"))

    if is_cn:
        st.markdown("""對於每場比賽，我們：
1. 為兩支球隊評分所有 17+1 個因素
2. 運行 5,000 次模擬比賽
3. 計算每支球隊獲勝的次數
4. 將百分比作為概率報告

對於整個錦標賽：
1. 模擬所有小組賽
2. 晉級前 2 名 + 8 個最佳第 3 名
3. 模擬淘汰賽
4. 重複 2,000 次
5. 報告每支球隊達到每個階段的頻率""")
    else:
        st.markdown("""For each match, we:
1. Score both teams on all 17 factors
2. Run 5,000 simulated matches
3. Count how often each team wins
4. Report the percentage as probability

For the full tournament:
1. Simulate all group stage matches
2. Advance top 2 + 8 best 3rd-place teams
3. Simulate knockout rounds
4. Repeat 2,000 times
5. Report how often each team reaches each stage""")

    st.divider()

    # DISCLAIMER
    st.header("⚠️ " + ("重要聲明" if is_cn else "IMPORTANT DISCLAIMER"))
    st.warning(("這是基於大數據分析的 AI 統計概率推算，並非博彩建議。結果為概率估算，不構成任何保證。足球不可預測——這正是它的魅力！"
                if is_cn else
                "This is an AI statistical projection based on big data analysis. It is NOT gambling advice. Results are probabilistic estimates, not guarantees. Football is unpredictable — that's what makes it beautiful!"))


def show_home():
    """Dashboard — Home page with today's matches, trending teams, quick stats"""
    lang = st.session_state.language if 'language' in st.session_state else 'en'
    is_cn = lang in ['zh_hant', 'zh_hans']
    theme = init_theme()
    apply_custom_css(lang, theme)
    tokens = get_design_tokens(lang, theme)

    st.title("🏆 " + ("2026 世界盃 AI 預測" if is_cn else "World Cup 2026 AI Predictor"))
    st.caption("Formula V12 — 17+1 Dimensions × 3 EmoGlyphPlay Engines × Dynamic Market Intelligence")

    # Quick Stats Row
    st.markdown("### 📊 " + ("快速統計" if is_cn else "Quick Stats"))
    stat_cols = st.columns(4)

    if _V11_AVAILABLE:
        try:
            v11 = load_v11_engine()
            result = v11.simulate_tournament(500)
            preds = result['predictions']
            top_team = list(preds.keys())[0]
            top_prob = preds[top_team]["win_probability"]

            with stat_cols[0]:
                st.metric("🏆 " + ("最可能冠軍" if is_cn else "Most Likely Champion"), top_team, f"{top_prob:.1%}")
            with stat_cols[1]:
                # Find dark horse (team with 2-8% win prob, highest among them)
                dark_horses = [(t, p) for t, p in preds.items() if 0.02 <= p["win_probability"] <= 0.08]
                if dark_horses:
                    dh = max(dark_horses, key=lambda x: x[1]["win_probability"])
                    st.metric("🐴 " + ("黑馬" if is_cn else "Dark Horse"), dh[0], f"{dh[1]['win_probability']:.1%}")
                else:
                    st.metric("🐴 " + ("黑馬" if is_cn else "Dark Horse"), "—", "—")
            with stat_cols[2]:
                # Biggest upset potential (lowest ranked team with >50% group advance)
                upsets = [(t, p) for t, p in preds.items() if p["group_advance_probability"] > 0.5 and p["win_probability"] < 0.03]
                if upsets:
                    upset_team = max(upsets, key=lambda x: x[1]["group_advance_probability"])
                    st.metric("🔥 " + ("最大冷門" if is_cn else "Upset Alert"), upset_team[0], f"{upset_team[1]['group_advance_probability']:.0%}")
                else:
                    st.metric("🔥 " + ("最大冷門" if is_cn else "Upset Alert"), "—", "—")
            with stat_cols[3]:
                total_teams = len(preds)
                st.metric("⚽ " + ("參賽球隊" if is_cn else "Teams"), f"{total_teams}", "48 " + ("隊" if is_cn else "teams"))
        except Exception as e:
            st.caption(f"Stats unavailable: {e}")

    st.divider()

    # Today's Featured Matches
    st.markdown("### ⚽ " + ("焦點比賽" if is_cn else "Featured Matches"))

    if _V11_AVAILABLE:
        try:
            v11 = load_v11_engine()
            featured_matches = [
                ("France", "Brazil"),
                ("England", "Germany"),
                ("Argentina", "Spain"),
            ]

            for home, away in featured_matches:
                pred = v11.predict_match(home, away, {'stage': 'group'})
                home_p = pred['prob_a_win']
                draw_p = pred['prob_draw']
                away_p = pred['prob_b_win']

                home_pct = int(home_p * 100)
                draw_pct = int(draw_p * 100)
                away_pct = int(away_p * 100)

                winner = home if home_p > away_p else away
                winner_pct = max(home_p, away_p)

                st.markdown(f"""
                <div style="background:#1E1E1E;border-radius:8px;padding:12px 16px;margin:6px 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <span style="font-weight:bold;color:#4CAF50;">{home}</span>
                        <span style="color:#FFB300;">vs</span>
                        <span style="font-weight:bold;color:#81C784;">{away}</span>
                    </div>
                    <div style="display:flex;height:24px;border-radius:6px;overflow:hidden;">
                        <div style="width:{home_pct}%;background:#4CAF50;display:flex;align-items:center;justify-content:center;color:white;font-size:0.8rem;font-weight:bold;">{home_pct}%</div>
                        <div style="width:{draw_pct}%;background:#FFB300;display:flex;align-items:center;justify-content:center;color:#1E1E1E;font-size:0.8rem;font-weight:bold;">{draw_pct}%</div>
                        <div style="width:{away_pct}%;background:#81C784;display:flex;align-items:center;justify-content:center;color:#1E1E1E;font-size:0.8rem;font-weight:bold;">{away_pct}%</div>
                    </div>
                    <div style="text-align:center;margin-top:4px;color:#888;font-size:0.8rem;">
                        💡 {winner} {('勝率' if is_cn else 'wins')} {winner_pct:.0%}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.caption(f"Match predictions unavailable: {e}")

    st.divider()

    # Tournament Top 10
    st.markdown("### 🏆 " + ("奪冠概率 Top 10" if is_cn else "Tournament Win Probability Top 10"))

    if _V11_AVAILABLE:
        try:
            v11 = load_v11_engine()
            result = v11.simulate_tournament(500)
            preds = result['predictions']

            for i, (team, p) in enumerate(list(preds.items())[:10]):
                wp = p["win_probability"]
                col_rank, col_team, col_bar = st.columns([1, 3, 6])
                with col_rank:
                    st.markdown(f"**{i+1}**")
                with col_team:
                    st.markdown(f"**{team}**")
                with col_bar:
                    st.progress(min(wp * 5, 1.0), text=f"{wp:.1%}")
        except Exception as e:
            st.caption(f"Tournament simulation unavailable: {e}")

    st.divider()

    # Trending Teams
    st.markdown("### 📈 " + ("趨勢球隊" if is_cn else "Trending Teams"))

    if _V11_AVAILABLE:
        try:
            v11 = load_v11_engine()
            # Show teams with highest structural advantage
            from formula_v11_emoglyph import WC2026_GROUPS
            trending = []
            for group_name, teams in WC2026_GROUPS.items():
                for team in teams:
                    sa = v11.score_structural_advantage(team, {'stage': 'group'})
                    if sa > 0.7:
                        trending.append((team, sa, group_name))

            trending.sort(key=lambda x: x[1], reverse=True)

            if trending:
                cols = st.columns(min(4, len(trending)))
                for i, (team, sa, group) in enumerate(trending[:4]):
                    with cols[i]:
                        st.markdown(f"**{team}**\n🏗️ Group {group}\nSA: {sa:.0%}")
            else:
                st.caption("No trending teams data")
        except Exception:
            st.caption("Trending data unavailable")

    # Footer
    st.divider()
    st.caption("⚠️ " + ("這是 AI 統計概率推算，並非博彩建議" if is_cn else "AI statistical projection — NOT gambling advice"))

def show_match_prediction():
    st.title(f"⚽ {t('match_prediction_title')}")

    lang = st.session_state.language
    is_cn = lang in ['zh_hant', 'zh_hans']
    teams = engine.get_all_teams()
    if not teams:
        st.error(f"❌ {t('no_teams_available')}")
        return

    team_display_names = {team: get_team_name(team, lang) for team in teams}
    display_teams = [team_display_names[t] for t in teams]

    col1, col2 = st.columns(2)
    with col1:
        default_home = teams.index("Brazil") if "Brazil" in teams else 0
        home_display = st.selectbox(t('home_team'), display_teams, index=default_home)
        home_team = teams[display_teams.index(home_display)]
    with col2:
        default_away = teams.index("Argentina") if "Argentina" in teams else (1 if len(teams) > 1 else 0)
        away_display = st.selectbox(t('away_team'), display_teams, index=default_away)
        away_team = teams[display_teams.index(away_display)]

    if tournament is not None:
        groups = tournament.generate_groups()
        home_group = None
        away_group = None
        for letter, group_teams in groups.items():
            if home_team in group_teams:
                home_group = letter
            if away_team in group_teams:
                away_group = letter

        group_col1, group_col2 = st.columns(2)
        with group_col1:
            if home_group:
                st.info(f"**{t('group')} {home_group}**")
        with group_col2:
            if away_group:
                st.info(f"**{t('group')} {away_group}**")

    opta_probs = {
        'Argentina': 12.5, 'France': 11.8, 'Brazil': 10.5, 'England': 9.2,
        'Spain': 8.5, 'Germany': 7.8, 'Portugal': 5.5, 'Netherlands': 4.2,
        'Italy': 3.8, 'Belgium': 3.2, 'Croatia': 2.5, 'Uruguay': 2.1
    }

    top_teams_for_opta = [t_name for t_name in [home_team, away_team] if t_name in opta_probs]
    if top_teams_for_opta:
        st.subheader(f"📊 {t('opta_win_prob')}")
        opta_cols = st.columns(len(top_teams_for_opta))
        for idx, team in enumerate(top_teams_for_opta):
            with opta_cols[idx]:
                st.metric(get_team_name(team, lang), f"{opta_probs[team]}%")

    # Auto-fetch statistical consensus (replaces manual odds input)
    if _ODDS_AVAILABLE:
        try:
            odds_layer = OddsDataLayer()
            market_data = odds_layer.fetch_market_consensus(home_team, away_team)
            auto_alpha = odds_layer.calculate_dynamic_alpha()  # Default: no match time
            use_odds = True
        except Exception:
            auto_alpha = 0.15
            use_odds = False
    else:
        auto_alpha = 0.15
        use_odds = False

    # Advanced settings (collapsed)
    with st.expander("⚙️ " + ("進階設定" if is_cn else "Advanced Settings")):
        use_odds = st.toggle("📊 " + ("統計共識整合" if is_cn else "Statistical Consensus Integration"), value=use_odds, help="Blend model prediction with statistical consensus")
        alpha_val = st.slider("📊 " + ("共識權重 (α)" if is_cn else "Consensus Weight (α)"), min_value=0.0, max_value=1.0, value=auto_alpha, step=0.05, help=f"α=1.0 = pure consensus, α=0.0 = pure model (auto: {auto_alpha:.2f})")

    if st.button(t('predict_match'), width='stretch'):
        result = engine.predict_match(home_team, away_team, 2.0, 3.2, 3.5)

        if not result['success']:
            st.error(result.get('error', t('prediction_failed')))
            return

        model_probs = (
            result['home_win_probability'],
            result['draw_probability'],
            result['away_win_probability'],
        )

        if use_odds:
            odds_predictor.alpha = alpha_val
            blended = odds_predictor.predict(home_team, away_team, model_probs)
            home_win_prob = blended.final_home
            draw_prob = blended.final_draw
            away_win_prob = blended.final_away
        else:
            home_win_prob = model_probs[0]
            draw_prob = model_probs[1]
            away_win_prob = model_probs[2]

        home_display = get_team_name(home_team, lang)
        away_display = get_team_name(away_team, lang)

        # ═══ MATCH CARD ═══
        st.markdown("---")
        st.subheader("⚽ " + ("比賽預測" if is_cn else "MATCH PREDICTION"))

        # Visual probability bar
        home_pct = int(home_win_prob * 100)
        draw_pct = int(draw_prob * 100)
        away_pct = int(away_win_prob * 100)

        st.markdown(f"""
        <div style="background:#1E1E1E;border-radius:12px;padding:20px;margin:10px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span style="font-size:1.3rem;font-weight:bold;color:#4CAF50;">{home_display}</span>
                <span style="font-size:1rem;color:#FFB300;">vs</span>
                <span style="font-size:1.3rem;font-weight:bold;color:#81C784;">{away_display}</span>
            </div>
            <div style="display:flex;height:32px;border-radius:8px;overflow:hidden;margin-bottom:8px;">
                <div style="width:{home_pct}%;background:#4CAF50;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:0.9rem;">{home_pct}%</div>
                <div style="width:{draw_pct}%;background:#FFB300;display:flex;align-items:center;justify-content:center;color:#1E1E1E;font-weight:bold;font-size:0.9rem;">{draw_pct}%</div>
                <div style="width:{away_pct}%;background:#81C784;display:flex;align-items:center;justify-content:center;color:#1E1E1E;font-weight:bold;font-size:0.9rem;">{away_pct}%</div>
            </div>
            <div style="display:flex;justify-content:space-between;color:#888;font-size:0.8rem;">
                <span>{home_display} Win</span>
                <span>Draw</span>
                <span>{away_display} Win</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Key Factors
        st.markdown("### 🎯 " + ("關鍵因素" if is_cn else "KEY FACTORS"))

        if _V11_AVAILABLE:
            try:
                v11 = load_v11_engine()
                dims = v11._calculate_all_dimensions(home_team, {'stage': 'group'})
                dims_away = v11._calculate_all_dimensions(away_team, {'stage': 'group'})

                # Find top 3 factors with biggest difference
                factor_diffs = []
                human_names = {
                    "elo_rating": ("歷史評級" if is_cn else "Historical Rating"),
                    "recent_form": ("近期狀態" if is_cn else "Recent Form"),
                    "squad_depth": ("陣容深度" if is_cn else "Squad Depth"),
                    "coaching_style": ("教練水平" if is_cn else "Coaching"),
                    "xfactor_players": ("X因子球員" if is_cn else "X-Factor Players"),
                    "mental_psychological": ("心理素質" if is_cn else "Mental Strength"),
                    "squad_value": ("陣容身價" if is_cn else "Squad Value"),
                    "tournament_experience": ("大賽經驗" if is_cn else "Big-Game Experience"),
                    "tactical_matchup": ("風格對位" if is_cn else "Style Matchup"),
                    "rest_recovery": ("休息恢復" if is_cn else "Recovery"),
                    "extreme_heat": ("耐熱能力" if is_cn else "Heat Tolerance"),
                    "travel_fatigue": ("旅途疲勞" if is_cn else "Travel Fatigue"),
                    "home_advantage": ("主場優勢" if is_cn else "Home Advantage"),
                    "altitude_effect": ("海拔適應" if is_cn else "Altitude"),
                    "structural_advantage": ("小組策略" if is_cn else "Group Strategy"),
                }

                for dim_name in dims:
                    if dim_name in dims_away:
                        diff = dims[dim_name] - dims_away[dim_name]
                        factor_diffs.append((dim_name, dims[dim_name], dims_away[dim_name], diff))

                factor_diffs.sort(key=lambda x: abs(x[3]), reverse=True)

                for dim_name, home_val, away_val, diff in factor_diffs[:3]:
                    name = human_names.get(dim_name, dim_name)
                    if diff > 0:
                        advantage_team = home_display
                        stars = "⭐" * max(1, min(5, int(home_val * 5)))
                        st.markdown(f"  • **{advantage_team}**: {name} 優勢 {stars}")
                    else:
                        advantage_team = away_display
                        stars = "⭐" * max(1, min(5, int(away_val * 5)))
                        st.markdown(f"  • **{advantage_team}**: {name} 優勢 {stars}")
            except Exception:
                st.caption("Factor analysis unavailable")

        # Why? section
        st.markdown("### 💡 " + ("為什麼？" if is_cn else "WHY?"))
        winner = home_display if home_win_prob > away_win_prob else away_display
        winner_prob = max(home_win_prob, away_win_prob)
        loser = away_display if winner == home_display else home_display

        if is_cn:
            st.info(f"**{winner}** 的勝率為 {winner_prob:.0%}。主要優勢來自關鍵因素的差異。足球比賽充滿不確定性，{loser} 仍有翻盤機會！")
        else:
            st.info(f"**{winner}** has a {winner_prob:.0%} chance to win. Their advantage comes from key factor differences. But football is unpredictable — **{loser}** still has a chance!")

        # Confidence meter
        st.markdown("### 📊 " + ("信心指數" if is_cn else "CONFIDENCE"))
        if _ODDS_AVAILABLE and use_odds:
            try:
                odds_layer = OddsDataLayer()
                model_p = {"home_prob": home_win_prob, "draw_prob": draw_prob, "away_prob": away_win_prob}
                market_p = market_data.to_frontend_dict() if market_data and hasattr(market_data, 'to_frontend_dict') else {"home_prob": 0.5, "draw_prob": 0.25, "away_prob": 0.5}
                conf = odds_layer.calculate_confidence(model_p, market_p)
                conf_pct = int(conf["confidence_score"] * 100)
                conf_level = conf["confidence_level"]
                conf_desc = conf["description"]

                conf_icon = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(conf_level, "⚪")
                st.progress(conf_pct / 100, text=f"{conf_icon} {conf_level}: {conf_pct}% — {conf_desc}")
            except Exception:
                st.progress(0.5, text="🟡 Medium: 50% — Default confidence")
        else:
            st.progress(0.5, text="🟡 " + ("中等：無市場數據" if is_cn else "Medium: No market data"))

        # Last updated
        st.caption("🔄 " + ("市場數據每 6 小時更新" if is_cn else "Market data refreshes every 6 hours"))

        st.subheader(f"📊 {t('factor_breakdown')}")
        premium_badge()
        if st.session_state.get('is_premium', False):
            factors = result['factors']

            st.write(f"**{t('expected_goals')}:**")
            col_xg1, col_xg2 = st.columns(2)
            with col_xg1:
                st.metric(home_display, f"{factors['xg']['home']:.2f}")
            with col_xg2:
                st.metric(away_display, f"{factors['xg']['away']:.2f}")

            st.write(f"**{t('player_factor')}:**")
            # Simple emoji factor comparison
            pf_home = factors['player_factor']['home']
            pf_away = factors['player_factor']['away']
            pf_home_stars = "⭐" * max(1, min(5, int(pf_home * 5)))
            pf_away_stars = "⭐" * max(1, min(5, int(pf_away * 5)))
            st.markdown(f"**{home_display}**: {pf_home_stars} ({pf_home:.2f})")
            st.markdown(f"**{away_display}**: {pf_away_stars} ({pf_away:.2f})")

            st.write(f"**{t('defensive_pk')}:**")
            col_pk1, col_pk2 = st.columns(2)
            with col_pk1:
                st.metric(home_display, f"{factors['defensive_pk']['home']:.2f}")
            with col_pk2:
                st.metric(away_display, f"{factors['defensive_pk']['away']:.2f}")

            st.write(f"**{t('xfactor_players')}:**")
            col_xf1, col_xf2 = st.columns(2)
            with col_xf1:
                st.metric(home_display, f"{factors['xfactor']['home']:.2f}")
            with col_xf2:
                st.metric(away_display, f"{factors['xfactor']['away']:.2f}")
        else:
            premium_gate("Detailed Factor Analysis")

        # Environmental Factors (integrated from Extreme Environment page)
        st.subheader("🌡️ " + ("環境因素" if is_cn else "Environmental Factors"))

        if _V11_AVAILABLE:
            try:
                from formula_v11_emoglyph import FormulaV11Engine, WC2026_GROUPS
                from wc2026_venue_data import get_wbgt_risk, get_altitude_effect
                from wc2026_recovery_data import get_team_recovery

                v11 = load_v11_engine()
                env_col1, env_col2 = st.columns(2)

                with env_col1:
                    st.markdown(f"**{home_display}**")
                    # Heat
                    heat_h = v11.score_extreme_heat(home_team, {'stage': 'group'})
                    heat_icon = "🟢" if heat_h > 0.7 else "🟡" if heat_h > 0.4 else "🔴"
                    st.markdown(f"{heat_icon} 🌡️ {'耐熱能力' if is_cn else 'Heat Tolerance'}: {heat_h:.0%}")
                    # Recovery
                    rec_h = v11.score_rest_recovery(home_team, {'stage': 'group'})
                    rec_icon = "🟢" if rec_h > 0.7 else "🟡" if rec_h > 0.4 else "🔴"
                    st.markdown(f"{rec_icon} 🔋 {'休息恢復' if is_cn else 'Recovery'}: {rec_h:.0%}")
                    # Travel
                    trav_h = v11.score_travel_fatigue(home_team, {'stage': 'group'})
                    trav_icon = "🟢" if trav_h > 0.7 else "🟡" if trav_h > 0.4 else "🔴"
                    st.markdown(f"{trav_icon} ✈️ {'旅途疲勞' if is_cn else 'Travel Fatigue'}: {trav_h:.0%}")
                    # Altitude
                    alt_h = v11.score_altitude_effect(home_team, {'stage': 'group'})
                    alt_icon = "🟢" if alt_h > 0.7 else "🟡" if alt_h > 0.4 else "🔴"
                    st.markdown(f"{alt_icon} ⛰️ {'海拔適應' if is_cn else 'Altitude Adaptation'}: {alt_h:.0%}")

                with env_col2:
                    st.markdown(f"**{away_display}**")
                    heat_a = v11.score_extreme_heat(away_team, {'stage': 'group'})
                    heat_icon_a = "🟢" if heat_a > 0.7 else "🟡" if heat_a > 0.4 else "🔴"
                    st.markdown(f"{heat_icon_a} 🌡️ {'耐熱能力' if is_cn else 'Heat Tolerance'}: {heat_a:.0%}")
                    rec_a = v11.score_rest_recovery(away_team, {'stage': 'group'})
                    rec_icon_a = "🟢" if rec_a > 0.7 else "🟡" if rec_a > 0.4 else "🔴"
                    st.markdown(f"{rec_icon_a} 🔋 {'休息恢復' if is_cn else 'Recovery'}: {rec_a:.0%}")
                    trav_a = v11.score_travel_fatigue(away_team, {'stage': 'group'})
                    trav_icon_a = "🟢" if trav_a > 0.7 else "🟡" if trav_a > 0.4 else "🔴"
                    st.markdown(f"{trav_icon_a} ✈️ {'旅途疲勞' if is_cn else 'Travel Fatigue'}: {trav_a:.0%}")
                    alt_a = v11.score_altitude_effect(away_team, {'stage': 'group'})
                    alt_icon_a = "🟢" if alt_a > 0.7 else "🟡" if alt_a > 0.4 else "🔴"
                    st.markdown(f"{alt_icon_a} ⛰️ {'海拔適應' if is_cn else 'Altitude Adaptation'}: {alt_a:.0%}")

                # Plain text summary
                env_advantage = home_team if (heat_h + rec_h) > (heat_a + rec_a) else away_team
                st.info(f"💡 {'環境因素傾向於' if is_cn else 'Environmental factors favor'} **{env_advantage}**")

                # Defensive Counter-Attack Advantage
                if _V11_AVAILABLE:
                    try:
                        from formula_v11_emoglyph import TEAM_STYLE_CLASSIFICATION
                        home_style = TEAM_STYLE_CLASSIFICATION.get(home_team, "balanced")
                        away_style = TEAM_STYLE_CLASSIFICATION.get(away_team, "balanced")

                        style_names = {
                            "defensive_counter": ("防守反擊" if is_cn else "Defensive Counter"),
                            "attacking_possession": ("進攻控球" if is_cn else "Attacking Possession"),
                            "balanced": ("均衡" if is_cn else "Balanced"),
                        }

                        st.markdown(f"**🛡️ {'戰術風格' if is_cn else 'Tactical Style'}**")
                        style_col1, style_col2 = st.columns(2)
                        with style_col1:
                            st.markdown(f"{home_display}: {style_names.get(home_style, home_style)}")
                        with style_col2:
                            st.markdown(f"{away_display}: {style_names.get(away_style, away_style)}")

                        # Check if there's a defensive advantage in extreme conditions
                        v11 = load_v11_engine()
                        def_bonus_h = v11.score_defensive_counter_advantage(home_team, away_team, {'stage': 'group', 'venue_wbgt': 30})
                        def_bonus_a = v11.score_defensive_counter_advantage(away_team, home_team, {'stage': 'group', 'venue_wbgt': 30})

                        if abs(def_bonus_h) > 0.01 or abs(def_bonus_a) > 0.01:
                            if def_bonus_h > def_bonus_a:
                                adv_team = home_display
                                adv_pct = f"+{def_bonus_h:.0%}"
                                adv_reason = ("在高溫下防守反擊佔優" if is_cn else "defensive counter advantage in heat")
                            else:
                                adv_team = away_display
                                adv_pct = f"+{def_bonus_a:.0%}"
                                adv_reason = ("在高溫下防守反擊佔優" if is_cn else "defensive counter advantage in heat")
                            st.info(f"🛡️ **{adv_team}** {adv_pct} {adv_reason}")
                    except Exception:
                        pass
            except Exception as e:
                st.caption(f"Environmental data unavailable: {e}")
        else:
            st.caption("Environmental factors require V11 engine")

def show_team_comparison():
    st.title(f"⚔️ {t('team_comparison_title')}")

    lang = st.session_state.language
    teams = engine.get_all_teams()
    if not teams:
        st.error(f"❌ {t('no_teams_available')}")
        return

    team_display_names = {team: get_team_name(team, lang) for team in teams}
    display_teams = [team_display_names[t] for t in teams]

    col1, col2 = st.columns(2)
    with col1:
        default_t1 = teams.index("Argentina") if "Argentina" in teams else 0
        team1_display = st.selectbox(t('team_1'), display_teams, index=default_t1)
        team1 = teams[display_teams.index(team1_display)]
    with col2:
        default_t2 = teams.index("Brazil") if "Brazil" in teams else (1 if len(teams) > 1 else 0)
        team2_display = st.selectbox(t('team_2'), display_teams, index=default_t2)
        team2 = teams[display_teams.index(team2_display)]

    if st.button(t('compare_teams'), width='stretch'):
        comparison = engine.get_team_comparison(team1, team2)

        if not comparison['success']:
            st.error(comparison.get('error', t('comparison_failed')))
            return

        st.subheader(f"🏆 {t('5_point_comparison')}")

        team1_display = get_team_name(team1, lang)
        team2_display = get_team_name(team2, lang)

        metrics = ['overall_strength', 'attack_power', 'defense_strength', 'pk_ability', 'xfactor_players']
        metric_names = [t('overall_strength'), t('attack_power'), t('defense_strength'), t('pk_ability'), t('xfactor_players_label')]

        team1_values = []
        team2_values = []

        for metric, name in zip(metrics, metric_names):
            data = comparison['comparison'][metric]
            winner = data['winner']
            team1_values.append(data[team1])
            team2_values.append(data[team2])

            col_a, col_b, col_c = st.columns([2, 1, 2])
            with col_a:
                st.write(f"**{team1_display}:** {data[team1]}")
            with col_b:
                st.write(f"🏆 {get_team_name(winner, lang)}")
            with col_c:
                st.write(f"**{team2_display}:** {data[team2]}")

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=team1_values,
            theta=metric_names,
            fill='toself',
            fillcolor='rgba(76,175,80,0.3)',
            line_color='#4CAF50',
            name=team1_display
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=team2_values,
            theta=metric_names,
            fill='toself',
            fillcolor='rgba(255,179,0,0.3)',
            line_color='#FFB300',
            name=team2_display
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True,
            title=t('5_point_comparison')
        )
        st.plotly_chart(fig_radar, width='stretch')

        st.subheader(f"📋 {get_team_name(team1, lang)} {t('xfactor_list_title')}")
        premium_badge()
        if st.session_state.get('is_premium', False):
            team1_players = [p for p in comparison['team1_players'] if p['is_xfactor']]
            if team1_players:
                for player in team1_players:
                    player_name = get_player_name(player['name'], team1, lang)
                    st.write(f"⭐ {player_name} ({player['position']})")
            else:
                st.write(t('no_xfactor_players'))

            st.subheader(f"📋 {get_team_name(team2, lang)} {t('xfactor_list_title')}")
            team2_players = [p for p in comparison['team2_players'] if p['is_xfactor']]
            if team2_players:
                for player in team2_players:
                    player_name = get_player_name(player['name'], team2, lang)
                    st.write(f"⭐ {player_name} ({player['position']})")
            else:
                st.write(t('no_xfactor_players'))
        else:
            premium_gate("X-Factor Player Details")

def show_player_database():
    st.title(f"👥 {t('player_database_title')}")

    lang = st.session_state.language
    teams = engine.get_all_teams()
    if not teams:
        st.error(f"❌ {t('no_teams_available')}")
        return

    team_display_names = {team: get_team_name(team, lang) for team in teams}
    display_teams = [team_display_names[t] for t in teams]

    selected_display = st.selectbox(t('select_team'), display_teams)
    selected_team = teams[display_teams.index(selected_display)]

    show_xfactor_only = st.checkbox(t('show_xfactor_only'), value=False)

    players = engine.get_team_players(selected_team)

    if players:
        for p in players:
            p['name'] = get_player_name(p['name'], selected_team, lang)

        df = pd.DataFrame(players)
        df = df[['name', 'position', 'age', 'dribbling_skill', 'pace', 'shooting',
                 'passing', 'defending', 'fitness_level', 'world_cup_experience',
                 'is_xfactor', 'injury_status']]

        df_display = df.copy()
        df_display['name'] = df_display.apply(
            lambda row: f"⭐ {row['name']}" if row['is_xfactor'] else row['name'],
            axis=1
        )

        if show_xfactor_only:
            df_display = df_display[df_display['is_xfactor']]
            df = df[df['is_xfactor']]

        st.dataframe(df_display, width='stretch')

        st.subheader(f"📊 {t('attribute_distribution')}")

        avg_pace = df['pace'].mean()
        avg_shooting = df['shooting'].mean()
        avg_passing = df['passing'].mean()
        avg_defending = df['defending'].mean()
        avg_dribbling = df['dribbling_skill'].mean()
        avg_fitness = df['fitness_level'].mean()

        categories = ['Pace', 'Shooting', 'Passing', 'Defending', 'Dribbling', 'Fitness']
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=[avg_pace, avg_shooting, avg_passing, avg_defending, avg_dribbling, avg_fitness],
            theta=categories,
            fill='toself',
            fillcolor='rgba(76,175,80,0.3)',
            line_color='#4CAF50',
            name=get_team_name(selected_team, lang)
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title=f"{get_team_name(selected_team, lang)} {t('attribute_distribution')}"
        )
        st.plotly_chart(fig_radar, width='stretch')

        st.subheader(f"⭐ {t('xfactor_players_section')}")
        xfactor_players = df[df['is_xfactor']]
        if not xfactor_players.empty:
            st.dataframe(xfactor_players, width='stretch')
        else:
            st.info(t('no_xfactor_in_team'))
    else:
        st.warning(t('no_players_found'))

def show_tournament_simulation():
    st.title(f"🎯 {t('tournament_simulation_title')}")

    lang = st.session_state.language

    if tournament is None:
        st.error(f"❌ {t('tournament_model_error')}")
        return

    st.markdown(f"📋 **{t('tournament_format')}** | {t('third_place_advance')}")

    groups = tournament.generate_groups()
    group_letters = sorted(groups.keys())

    st.subheader(f"📊 {t('groups_stage')}")

    for row_start in range(0, len(group_letters), 4):
        row_letters = group_letters[row_start:row_start + 4]
        cols = st.columns(len(row_letters))
        for col, letter in zip(cols, row_letters):
            with col:
                st.markdown(f"**{t('group')} {letter}**")
                for team_name in groups[letter]:
                    display_name = get_team_name(team_name, lang)
                    st.write(f"- {display_name}")

    if 'tournament_result' not in st.session_state:
        st.session_state.tournament_result = None

    if st.button(f"🎲 {t('simulate_tournament')}", width='stretch'):
        with st.spinner(t('simulating')):
            st.session_state.tournament_result = tournament.simulate_tournament()

    if st.session_state.tournament_result:
        result = st.session_state.tournament_result

        st.success(f"**🏆 {t('champion')}:** {get_team_name(result['champion'], lang)}")
        st.info(f"**🥈 {t('runner_up')}:** {get_team_name(result['runner_up'], lang)}")
        st.info(f"**🥉 {t('third_place')}:** {get_team_name(result['third_place'], lang)}")

        st.subheader(f"📊 {t('group_stage_results')}")
        for group_name, group_data in result['group_stage'].items():
            group_letter = group_name.replace("Group ", "")
            st.markdown(f"**{t('group')} {group_letter}**")
            standings = pd.DataFrame(group_data['standings']).T
            standings = standings.sort_values('points', ascending=False)
            display_index = [get_team_name(team, lang) for team in standings.index]
            standings_display = standings.copy()
            standings_display.index = display_index
            st.dataframe(standings_display, width='stretch')

        st.subheader(f"⚔️ {t('knockout_stage')}")

        bracket = result['knockout_bracket']

        if 'round_of_32_results' in bracket:
            st.write(f"**{t('round_of_32')}:**")
            for match in bracket['round_of_32_results']:
                teams_in_match = match['match'].split(' vs ')
                display_match = f"{get_team_name(teams_in_match[0], lang)} vs {get_team_name(teams_in_match[1], lang)}"
                st.write(f"  {display_match} → **{get_team_name(match['winner'], lang)}** ({t('confidence')}: {match['confidence']}%)")

        st.write(f"**{t('round_of_16')}:**")
        for match in bracket['round_of_16_results']:
            teams_in_match = match['match'].split(' vs ')
            display_match = f"{get_team_name(teams_in_match[0], lang)} vs {get_team_name(teams_in_match[1], lang)}"
            st.write(f"  {display_match} → **{get_team_name(match['winner'], lang)}** ({t('confidence')}: {match['confidence']}%)")

        st.write(f"**{t('quarterfinals')}:**")
        for match in bracket['quarterfinal_results']:
            teams_in_match = match['match'].split(' vs ')
            display_match = f"{get_team_name(teams_in_match[0], lang)} vs {get_team_name(teams_in_match[1], lang)}"
            st.write(f"  {display_match} → **{get_team_name(match['winner'], lang)}** ({t('confidence')}: {match['confidence']}%)")

        st.write(f"**{t('semifinals')}:**")
        for match in bracket['semifinal_results']:
            teams_in_match = match['match'].split(' vs ')
            display_match = f"{get_team_name(teams_in_match[0], lang)} vs {get_team_name(teams_in_match[1], lang)}"
            st.write(f"  {display_match} → **{get_team_name(match['winner'], lang)}** ({t('confidence')}: {match['confidence']}%)")

        st.write(f"**🏆 {t('final')}:**")
        final = bracket['final_result']
        teams_in_final = final['match'].split(' vs ')
        display_final = f"{get_team_name(teams_in_final[0], lang)} vs {get_team_name(teams_in_final[1], lang)}"
        st.write(f"  {display_final} → **{get_team_name(final['winner'], lang)}** ({t('confidence')}: {final['confidence']}%)")

def show_model_analysis():
    st.title(f"📈 {t('model_analysis_title')}")

    st.subheader(f"📊 {t('research_statistics')}")

    accuracy_data = pd.DataFrame({
        'Iteration': ['100', '300', '500', '735'],
        'Accuracy (%)': [75.0, 80.0, 85.0, 90.4]
    })
    fig_accuracy = px.line(accuracy_data, x='Iteration', y='Accuracy (%)',
                           markers=True, title=t('accuracy_trend'),
                           line_shape='linear')
    fig_accuracy.update_traces(line=dict(width=3, color='#4CAF50'), marker=dict(size=10, color='#4CAF50'))
    st.plotly_chart(fig_accuracy, width='stretch')

    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
    with col_n1:
        st.metric(f"Phase 1", "2,500")
    with col_n2:
        st.metric(f"Phase 2", "5,000")
    with col_n3:
        st.metric(f"Phase 3", "7,500")
    with col_n4:
        st.metric(f"Phase 4", "10,001")

    st.subheader(f"🔧 {t('factor_weights_title')}")
    premium_badge()
    if st.session_state.get('is_premium', False):
        weights_data = {
            t('factor_attack_power').split('—')[0].strip(): 0.25,
            t('factor_market_odds').split('—')[0].strip(): 0.20,
            t('factor_squad_value').split('—')[0].strip(): 0.20,
            t('factor_form_fitness').split('—')[0].strip(): 0.20,
            t('factor_xfactor_players').split('—')[0].strip(): 0.15
        }

        weight_df = pd.DataFrame({
            'Factor': list(weights_data.keys()),
            'Weight': list(weights_data.values())
        })

        fig = px.pie(weight_df, values='Weight', names='Factor', title=t('weight_distribution'),
                     color_discrete_sequence=['#4CAF50', '#FFB300', '#81C784', '#F57F17', '#A5D6A7'])
        st.plotly_chart(fig, width='stretch')

        st.subheader(f"📊 {t('three_board_params')}")
        params = engine.three_board.factors
        params_df = pd.DataFrame({
            t('parameter'): list(params.keys()),
            t('value'): list(params.values())
        })
        st.dataframe(params_df, width='stretch')
    else:
        premium_gate("Factor Weights & Model Parameters")

    st.subheader(f"🏆 {t('team_strength_distribution')}")
    team_data = []
    for team_name, team in engine.teams.items():
        team_data.append({
            'Team': team_name,
            t('overall_strength'): team.overall_strength,
            t('attack_power'): team.attack_power,
            t('defense_strength'): team.defense_strength,
            t('pk_ability'): team.pk_ability
        })

    if not team_data:
        st.warning(f"⚠️ {t('no_team_data')}")
        return

    df = pd.DataFrame(team_data)
    overall_col = t('overall_strength')
    attack_col = t('attack_power')
    defense_col = t('defense_strength')
    pk_col = t('pk_ability')

    fig = px.scatter_matrix(df, dimensions=[overall_col, attack_col, defense_col, pk_col],
                           title=t('correlation_matrix'),
                           color='Team')
    st.plotly_chart(fig, width='stretch')

    st.subheader(f"📈 {t('top_by_category')}")
    categories = [overall_col, attack_col, defense_col, pk_col]
    lang = st.session_state.language

    for cat in categories:
        top_teams = df.nlargest(5, cat)
        team_names = [get_team_name(t_name, lang) for t_name in top_teams['Team']]
        heatmap_values = top_teams[[cat]].values

        fig_heat = px.imshow(
            heatmap_values.T,
            x=team_names,
            y=[cat],
            color_continuous_scale=['#1B5E20', '#4CAF50', '#81C784', '#FFB300', '#FFD54F'],
            aspect='auto',
            title=f"{t('top_5_teams')} - {cat}"
        )
        fig_heat.update_xaxes(side='bottom')
        st.plotly_chart(fig_heat, width='stretch')

def load_news_data():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('news', [])
    except Exception:
        return []

def show_news():
    st.title(f"📰 {t('news_title')}")

    news_data = load_news_data()

    if not news_data:
        st.warning(t('news_no_articles'))
        return

    sources = list(set(item['source'] for item in news_data))
    sources.sort()

    col1, col2 = st.columns([1, 3])
    with col1:
        filter_source = st.selectbox(
            t('news_filter_source'),
            [t('news_all_sources')] + sources
        )

    if filter_source != t('news_all_sources'):
        filtered_news = [n for n in news_data if n['source'] == filter_source]
    else:
        filtered_news = news_data

    total_articles = len(filtered_news)
    st.info(f"**{t('news_total')}:** {total_articles:,}")

    items_per_page = 50
    total_pages = (total_articles + items_per_page - 1) // items_per_page

    if total_pages > 1:
        page_num = st.number_input(
            f"{t('news_page_info')} (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1
        )
    else:
        page_num = 1

    start_idx = (page_num - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_news = filtered_news[start_idx:end_idx]

    tokens = get_design_tokens(st.session_state.language, st.session_state.get('theme', 'dark'))

    for i, article in enumerate(page_news):
        with st.container():
            st.markdown(f"""
            <div class="news-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="source">📰 {article['source']}</span>
                    <span class="timestamp">{article['timestamp']}</span>
                </div>
                <div class="content">{article['content']}</div>
            </div>
            """, unsafe_allow_html=True)

def get_all_xfactor_players():
    xfactor_players = []
    for team_name, team in engine.teams.items():
        for player in team.players:
            if player.is_xfactor:
                rating = int((player.dribbling_skill + player.pace + player.shooting + player.passing + player.defending) / 5)
                xfactor_players.append({
                    'name': player.name,
                    'team': team_name,
                    'position': player.position,
                    'rating': rating,
                    'goals': int(rating * 0.15),
                    'assists': int(rating * 0.12),
                    'form': player.fitness_level // 20,
                    'fitness': player.fitness_level
                })
    return xfactor_players

def show_xfactor():
    st.title(f"⭐ {t('xfactor_title')}")

    xfactor_players = get_all_xfactor_players()

    if not xfactor_players:
        st.warning(t('xfactor_no_players'))
        return

    st.metric(t('xfactor_total'), len(xfactor_players))

    lang = st.session_state.language

    df = pd.DataFrame(xfactor_players)
    df['display_name'] = df.apply(
        lambda row: f"{get_player_name(row['name'], row['team'], lang)} ({get_team_name(row['team'], lang)})",
        axis=1
    )

    st.subheader(f"📊 {t('xfactor_radar_chart')}")

    selected_players = st.multiselect(
        t('xfactor_select_compare'),
        df['display_name'].tolist(),
        max_selections=5
    )

    if selected_players:
        selected_df = df[df['display_name'].isin(selected_players)]

        categories = [t('xfactor_rating'), t('xfactor_goals'), t('xfactor_assists'),
                      t('xfactor_form'), t('xfactor_fitness')]

        fig = go.Figure()

        for idx, (_, player) in enumerate(selected_df.iterrows()):
            values = [
                player['rating'] / 100 * 5,
                min(player['goals'] / 30 * 5, 5),
                min(player['assists'] / 20 * 5, 5),
                player['form'],
                player['fitness'] / 20
            ]
            values.append(values[0])

            if idx == 0:
                fillcolor = 'rgba(76,175,80,0.3)'
                line_color = '#4CAF50'
            elif idx == 1:
                fillcolor = 'rgba(255,179,0,0.3)'
                line_color = '#FFB300'
            else:
                fillcolor = f'rgba(129,199,132,{0.3 - idx * 0.05})'
                line_color = '#81C784'

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill='toself',
                fillcolor=fillcolor,
                line_color=line_color,
                name=player['display_name']
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )
            ),
            showlegend=True,
            title=t('xfactor_compare_title')
        )

        st.plotly_chart(fig, width='stretch')

    st.subheader(f"📋 {t('xfactor_title')}")

    display_df = df[['display_name', 'position', 'rating', 'goals', 'assists', 'form', 'fitness']].copy()
    display_df.columns = [
        t('xfactor_team'), t('xfactor_position'), t('xfactor_rating'),
        t('xfactor_goals'), t('xfactor_assists'), t('xfactor_form'), t('xfactor_fitness')
    ]

    st.dataframe(display_df, width='stretch')

def show_team_profiles():
    """Team Profiles page with 4 sub-tabs: Squad, Coach & Strategy, Anime Cards, Venue Map"""
    st.title(f"🏟️ {t('team_profiles_title')}")

    lang_map = {'en': 'en', 'zh_hant': '繁中', 'zh_hans': '簡中'}
    lang = st.session_state.language
    profile_lang = lang_map.get(lang, 'en')

    teams = engine.get_all_teams()
    if not teams:
        st.error(f"❌ {t('team_profiles_no_data')}")
        return

    team_display_names = {team: get_team_name(team, lang) for team in teams}
    display_teams = [team_display_names[t] for t in teams]

    selected_display = st.selectbox(t('team_profiles_select'), display_teams)
    selected_team = teams[display_teams.index(selected_display)]

    tab_squad, tab_coach, tab_anime, tab_venue = st.tabs([
        f"👥 {t('team_profiles_squad')}",
        f"📋 {t('team_profiles_coach')}",
        f"🎴 {t('team_profiles_anime')}",
        f"🗺️ {t('team_profiles_venue')}",
    ])

    # ── Tab 1: Squad Overview ──────────────────────────────────────────
    with tab_squad:
        players = engine.get_team_players(selected_team)
        if not players:
            st.warning(t('team_squads_no_players'))
        else:
            avg_pace = sum(p['pace'] for p in players) / len(players)
            avg_shooting = sum(p['shooting'] for p in players) / len(players)
            avg_passing = sum(p['passing'] for p in players) / len(players)
            avg_defending = sum(p['defending'] for p in players) / len(players)
            avg_dribbling = sum(p['dribbling_skill'] for p in players) / len(players)
            avg_fitness = sum(p['fitness_level'] for p in players) / len(players)

            categories = [t('category_pace'), t('category_shooting'), t('category_passing'), t('category_defending'), t('category_dribbling'), t('category_fitness')]

            st.subheader(f"📊 {t('team_squads_avg_attributes')}")
            fig_team = go.Figure(data=go.Scatterpolar(
                r=[avg_pace, avg_shooting, avg_passing, avg_defending, avg_dribbling, avg_fitness],
                theta=categories,
                fill='toself',
                fillcolor='rgba(76,175,80,0.3)',
                line_color='#4CAF50',
                name=get_team_name(selected_team, lang)
            ))
            fig_team.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=True,
                title=f"{get_team_name(selected_team, lang)} {t('team_squads_avg_attributes')}"
            )
            st.plotly_chart(fig_team, width='stretch')

            st.subheader(f"⚽ {t('team_squads_player_abilities')}")
            for p in players:
                p['overall'] = (p['pace'] + p['shooting'] + p['passing'] + p['defending'] + p['dribbling_skill'] + p['fitness_level']) / 6
            players_sorted = sorted(players, key=lambda x: x['overall'], reverse=True)

            for i in range(0, len(players_sorted), 3):
                row_players = players_sorted[i:i+3]
                cols = st.columns(len(row_players))
                for col, p in zip(cols, row_players):
                    with col:
                        player_name = get_player_name(p['name'], selected_team, lang)
                        badge = f" {t('team_squads_xfactor_badge')}" if p['is_xfactor'] else ""
                        st.markdown(f"**{player_name}**{badge}")
                        st.caption(f"{p['position']} | {t('team_squads_overall')}: {p['overall']:.0f}")

                        fig_player = go.Figure(data=go.Scatterpolar(
                            r=[p['pace'], p['shooting'], p['passing'], p['defending'], p['dribbling_skill'], p['fitness_level']],
                            theta=categories,
                            fill='toself',
                            fillcolor='rgba(76,175,80,0.3)',
                            line_color='#4CAF50',
                            name=player_name
                        ))
                        fig_player.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                            showlegend=False,
                            margin=dict(l=20, r=20, t=20, b=20),
                            height=250
                        )
                        st.plotly_chart(fig_player, width='stretch')

    # ── Tab 2: Coach & Strategy ────────────────────────────────────────
    with tab_coach:
        if not _TEAM_PROFILES_AVAILABLE:
            st.warning(t('team_profiles_module_not_available'))
        else:
            profile = get_team_profile(selected_team)
            if not profile:
                st.warning(t('team_profiles_no_data'))
            else:
                coach = profile.get('coach', {})
                formation = profile.get('formation', '')
                main_player = get_team_main_player(selected_team, profile_lang)
                strategy = get_team_strategy(selected_team, profile_lang)
                strengths = get_team_strengths(selected_team, profile_lang)
                weaknesses = get_team_weaknesses(selected_team, profile_lang)
                style = profile.get('style', '')
                fifa_rank = profile.get('fifa_ranking', 0)
                elo = profile.get('elo_rating', 0)

                # Coach info card
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1E1E1E,#2D2D2D);border:1px solid #4CAF50;border-radius:12px;padding:24px;margin-bottom:20px;">
                    <h3 style="color:#4CAF50;margin:0 0 12px 0;">🧑‍💼 {t('team_profiles_coach_label')}</h3>
                    <p style="color:white;font-size:1.2rem;margin:4px 0;"><strong>{coach.get('name', 'N/A')}</strong></p>
                    <p style="color:#aaa;margin:4px 0;">{coach.get('nationality', '')} | {t('coach_age')}: {coach.get('age', '')} | {t('coach_style')}: {coach.get('style', '')}</p>
                </div>
                """, unsafe_allow_html=True)

                # Formation & Star Player
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div style="background:#1E1E1E;border:1px solid #FFB300;border-radius:12px;padding:20px;">
                        <h4 style="color:#FFB300;margin:0 0 8px 0;">📐 {t('team_profiles_formation')}</h4>
                        <p style="color:white;font-size:2rem;font-weight:bold;text-align:center;margin:8px 0;">{formation}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    mp_name = main_player.get('name', 'N/A') if isinstance(main_player, dict) else str(main_player)
                    mp_pos = main_player.get('position', '') if isinstance(main_player, dict) else ''
                    mp_nick = main_player.get('nickname', '') if isinstance(main_player, dict) else ''
                    if isinstance(mp_nick, dict):
                        mp_nick = mp_nick.get(profile_lang, mp_nick.get('en', ''))
                    st.markdown(f"""
                    <div style="background:#1E1E1E;border:1px solid #F44336;border-radius:12px;padding:20px;">
                        <h4 style="color:#F44336;margin:0 0 8px 0;">⭐ {t('team_profiles_main_player')}</h4>
                        <p style="color:white;font-size:1.3rem;font-weight:bold;margin:4px 0;">{mp_name}</p>
                        <p style="color:#aaa;margin:2px 0;">{mp_pos} {('"' + mp_nick + '"') if mp_nick else ''}</p>
                    </div>
                    """, unsafe_allow_html=True)

                # Strategy
                st.markdown(f"""
                <div style="background:#1E1E1E;border:1px solid #2196F3;border-radius:12px;padding:20px;margin-top:16px;">
                    <h4 style="color:#2196F3;margin:0 0 8px 0;">🎯 {t('team_profiles_strategy')}</h4>
                    <p style="color:white;margin:0;">{strategy}</p>
                </div>
                """, unsafe_allow_html=True)

                # Strengths & Weaknesses
                col_s, col_w = st.columns(2)
                with col_s:
                    st.markdown(f"### 💪 {t('team_profiles_strengths')}")
                    for s in strengths:
                        st.markdown(f"- ✅ {s}")
                with col_w:
                    st.markdown(f"### ⚠️ {t('team_profiles_weaknesses')}")
                    for w in weaknesses:
                        st.markdown(f"- ❌ {w}")

                # Style & Rankings
                style_labels = {
                    'defensive_counter': t('style_defensive_counter'),
                    'attacking_possession': t('style_attacking_possession'),
                    'balanced': t('style_balanced'),
                }
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1E1E1E,#2D2D2D);border-radius:12px;padding:16px;margin-top:16px;">
                    <div style="display:flex;justify-content:space-around;flex-wrap:wrap;">
                        <div style="text-align:center;padding:8px 16px;">
                            <p style="color:#aaa;margin:0;font-size:0.85rem;">{t('team_profiles_style')}</p>
                            <p style="color:white;margin:4px 0;font-weight:bold;">{style_labels.get(style, style)}</p>
                        </div>
                        <div style="text-align:center;padding:8px 16px;">
                            <p style="color:#aaa;margin:0;font-size:0.85rem;">{t('team_profiles_fifa_rank')}</p>
                            <p style="color:#FFB300;margin:4px 0;font-weight:bold;font-size:1.3rem;">#{fifa_rank}</p>
                        </div>
                        <div style="text-align:center;padding:8px 16px;">
                            <p style="color:#aaa;margin:0;font-size:0.85rem;">{t('team_profiles_elo')}</p>
                            <p style="color:#4CAF50;margin:4px 0;font-weight:bold;font-size:1.3rem;">{elo}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Tab 3: Anime Cards ─────────────────────────────────────────────
    with tab_anime:
        if not _ANIME_CARDS_AVAILABLE:
            st.warning(t('anime_card_not_available'))
        else:
            players = engine.get_team_players(selected_team)
            if not players:
                st.warning(t('team_squads_no_players'))
            else:
                for p in players:
                    p['overall'] = (p['pace'] + p['shooting'] + p['passing'] + p['defending'] + p['dribbling_skill'] + p['fitness_level']) / 6

                team_color = "#4CAF50"
                html = generate_team_cards_html(players, selected_team, team_color)
                st.markdown(html, unsafe_allow_html=True)

    # ── Tab 4: Venue Map ───────────────────────────────────────────────
    with tab_venue:
        if not _VENUE_MAP_AVAILABLE:
            st.warning(t('venue_map_not_available'))
        else:
            st.caption(t('team_profiles_venue_select'))
            fig = create_venue_map_3d(selected_team=selected_team)
            st.plotly_chart(fig, width='stretch')

            # Show flight distance details
            team_venues = get_team_venues(selected_team)
            if team_venues:
                from wc2026_venue_data import get_flight_distance, VENUES
                st.markdown(f"### ✈️ {t('flight_distances')}")
                for i in range(len(team_venues)):
                    for j in range(i+1, len(team_venues)):
                        v1, v2 = team_venues[i], team_venues[j]
                        dist = get_flight_distance(v1, v2)
                        v1_name = VENUES[v1]["name"] if v1 in VENUES else v1
                        v2_name = VENUES[v2]["name"] if v2 in VENUES else v2
                        st.markdown(f"**{v1_name}** ↔ **{v2_name}**: {dist:,.0f} {t('unit_miles')}")

def show_team_path_strategy():
    """Team Path Strategy page — per-team path analysis with social media export"""
    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']

    if not _PATH_GEN_AVAILABLE:
        st.error("Team Path Generator not available" if not is_cn else "球隊路徑生成器未載入")
        return

    st.title("🗺️ " + ("球隊路徑策略分析" if is_cn else "Team Path Strategy"))
    st.caption("Formula V12 — 17+1 Dimensions × 3 EmoGlyphPlay Engines × 48-Team Structural Advantage" if not is_cn
               else "Formula V12 — 17+1 維度 × 3 EmoGlyphPlay 引擎 × 48 隊結構優勢")

    from formula_v11_emoglyph import WC2026_GROUPS
    from wc2026_team_path_generator import TeamPathGenerator

    @st.cache_resource
    def load_path_gen():
        return TeamPathGenerator()

    path_gen = load_path_gen()

    # Build team list from groups
    all_teams = []
    for teams in WC2026_GROUPS.values():
        all_teams.extend(teams)

    # Team selector
    selected_team = st.selectbox(
        "Select Team" if not is_cn else "選擇球隊",
        all_teams,
        index=all_teams.index("France") if "France" in all_teams else 0,
        key="path_team_select"
    )

    # Language for social media
    sm_lang = st.selectbox(
        "Social Media Language" if not is_cn else "社交媒體語言",
        ["en", "zh_hans", "zh_hant"],
        format_func=lambda x: {"en": "English", "zh_hans": "簡體中文", "zh_hant": "繁體中文"}[x],
        key="path_sm_lang"
    )

    if st.button("🔍 " + ("分析路徑" if is_cn else "Analyze Path"), key="path_analyze_btn"):
        with st.spinner("Generating path analysis..." if not is_cn else "正在生成路徑分析..."):
            path = path_gen.generate_team_path(selected_team)

        # Header
        st.markdown(f"## {'⚽' if not is_cn else '⚽'} {selected_team}")
        group_label = f"Group {path['group']}" if not is_cn else f"第 {path['group']} 組"
        st.markdown(f"**{group_label}** — {', '.join(path['group_teammates'])}")

        # Structural Advantage
        sa = path['structural_advantage']
        sa_score = path['structural_advantage_score']
        sa_icon = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}.get(sa, "⚪")
        sa_label = "結構優勢" if is_cn else "Structural Advantage"
        st.markdown(f"### {sa_icon} {sa_label}: {sa} ({sa_score:.0%})")
        st.caption(path['structural_advantage_reason'])

        # Group Stage Matches
        st.markdown("### 🏟️ " + ("小組賽分析" if is_cn else "Group Stage Matches"))
        for match in path['group_matches']:
            approach = match.get(f'recommended_approach_{sm_lang}',
                                match.get('recommended_approach_en', ''))
            col1, col2, col3 = st.columns([2, 2, 3])
            with col1:
                st.markdown(f"**Match {match['match']}** vs {match['opponent']}")
            with col2:
                st.markdown(f"W: {match['win_prob']:.0%} | D: {match['draw_prob']:.0%} | L: {match['loss_prob']:.0%}")
            with col3:
                st.caption(approach)

        # Projected Group Finish
        finish = path['projected_group_finish']
        confidence = path['projected_group_finish_confidence']
        finish_label = "預計小組排名" if is_cn else "Projected Group Finish"
        st.markdown(f"**{finish_label}**: {finish} ({confidence:.0%})")

        # Knockout Path
        st.markdown("### 🏆 " + ("淘汰賽路徑" if is_cn else "Knockout Path"))
        for kp in path['knockout_path']:
            stage_name = kp['stage'].upper()
            strategy = kp.get(f'strategy_{sm_lang}', kp.get('strategy_en', ''))
            key_factor = kp.get('key_factor', '')
            st.markdown(f"**{stage_name}** vs {kp['opponent_team']} — Win: {kp['win_prob']:.0%}")
            if key_factor:
                st.caption(f"Key: {key_factor} | {strategy}")

        # Overall Win Probability
        st.markdown("### 📊 " + ("奪冠概率" if is_cn else "Overall Win Probability"))
        st.metric(selected_team, f"{path['overall_win_probability']:.1%}")

        # LightDarkBalance
        ldb = path.get('light_dark_balance', {})
        if ldb:
            st.markdown("### ⚖️ LightDarkBalance")
            ldb_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(ldb.get('confidence', ''), "⚪")
            col_l, col_d, col_ldb = st.columns(3)
            with col_l:
                st.metric("Light", f"{ldb.get('light', 0):.2f}")
            with col_d:
                st.metric("Dark", f"{ldb.get('dark', 0):.2f}")
            with col_ldb:
                st.metric(f"LDB {ldb_icon}", f"{ldb.get('ldb', 0):.3f}")

        # X-Factor Players
        xfactor = path.get('xfactor_players', [])
        if xfactor:
            st.markdown("### ⭐ " + ("X因子球員" if is_cn else "X-Factor Players"))
            st.markdown(", ".join(xfactor))

        # Critical Risk
        risk = path.get('critical_risk', '')
        if risk:
            st.warning(f"⚠️ {'關鍵風險' if is_cn else 'Critical Risk'}: {risk}")

        # Scenarios
        best = path.get('best_case_scenario', '')
        worst = path.get('worst_case_scenario', '')
        if best or worst:
            st.markdown("### 🔮 " + ("情景分析" if is_cn else "Scenarios"))
            col_best, col_worst = st.columns(2)
            with col_best:
                st.success(f"✅ {'最佳' if is_cn else 'Best'}: {best}")
            with col_worst:
                st.error(f"❌ {'最差' if is_cn else 'Worst'}: {worst}")

        # Social Media Export
        st.markdown("---")
        st.markdown("### 📱 " + ("社交媒體內容" if is_cn else "Social Media Content"))

        if _SOCIAL_GEN_AVAILABLE:
            from wc2026_social_media_generator import SocialMediaGenerator
            sm_gen = SocialMediaGenerator()

            spotlight = sm_gen.generate_team_spotlight(selected_team, sm_lang)
            path_pred = sm_gen.generate_path_prediction(selected_team, sm_lang)

            tab1, tab2 = st.tabs(["Spotlight", "Path Prediction" if not is_cn else "路徑預測"])
            with tab1:
                st.markdown(f"**Short (≤280 chars):**")
                st.code(spotlight['short'], language=None)
                st.markdown(f"**Long (≤1000 chars):**")
                st.code(spotlight['long'], language=None)
                st.markdown(f"**Hashtags:** {' '.join(spotlight['hashtags'])}")

            with tab2:
                st.markdown(f"**Short:**")
                st.code(path_pred['short'], language=None)
                st.markdown(f"**Long:**")
                st.code(path_pred['long'], language=None)
                st.markdown(f"**Hashtags:** {' '.join(path_pred['hashtags'])}")

        # Formula Explanation (collapsible)
        with st.expander("📖 " + ("公式原理" if is_cn else "How It Works")):
            st.markdown(path_gen.explain_formula_human_readable(sm_lang))

def show_investment_portfolio():
    """Investment Portfolio page — group consensus, ROI recommendations, portfolio allocation"""
    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']

    st.title("💼 " + t('investment_portfolio_title'))

    # Compliance disclaimer at top
    st.markdown(f"""
    <div style="background:rgba(255,179,0,0.15);border:1px solid #FFB300;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
        <p style="margin:0;color:#FFB300;font-size:0.9rem;">⚠️ {t('investment_disclaimer')}</p>
    </div>
    """, unsafe_allow_html=True)

    if not _MARKET_CONSENSUS_AVAILABLE or not _PORTFOLIO_OPTIMIZER_AVAILABLE:
        st.error(t('module_not_available') if not is_cn else "模組未載入")
        return

    from wc2026_market_consensus import MarketConsensus, GROUP_CONSENSUS_BASELINE
    from wc2026_portfolio_optimizer import PortfolioOptimizer, ExplanationGenerator
    from formula_v11_emoglyph import WC2026_GROUPS, ELO_RATINGS

    @st.cache_resource
    def load_market_consensus():
        return MarketConsensus()

    @st.cache_resource
    def load_optimizer():
        return PortfolioOptimizer()

    mc = load_market_consensus()
    optimizer = load_optimizer()

    # Budget input
    budget = st.number_input(
        t('budget_label'),
        min_value=100,
        max_value=100000,
        value=1000,
        step=100,
        key="portfolio_budget"
    )

    # Get all group consensus data
    all_consensus = mc.fetch_all_groups_consensus()

    # Build positions list for optimizer
    positions = []
    for group_name, teams in WC2026_GROUPS.items():
        group_data = all_consensus.get(group_name, {})
        for team in teams:
            team_data = group_data.get(team, {})
            if not team_data:
                continue

            # 1st place position
            market_odds_1st = team_data.get('1st_odds', 50.0)
            market_implied_1st = team_data.get('1st_prob', 0.02)

            # Model probability from V12 engine
            if _V11_AVAILABLE and engine:
                try:
                    # Use Elo-based model probability as approximation
                    elo = ELO_RATINGS.get(team, 1700)
                    # Scale Elo to probability relative to group
                    group_elos = [ELO_RATINGS.get(t, 1700) for t in teams]
                    total_elo = sum(10 ** (e / 400) for e in group_elos)
                    model_prob_1st = (10 ** (elo / 400)) / total_elo
                except Exception:
                    model_prob_1st = market_implied_1st
            else:
                model_prob_1st = market_implied_1st

            positions.append({
                'group': group_name,
                'position': '1st',
                'team': team,
                'market_odds': market_odds_1st,
                'market_implied_prob': market_implied_1st,
                'model_prob': model_prob_1st,
            })

            # 2nd place position
            market_odds_2nd = team_data.get('2nd_odds', 50.0)
            market_implied_2nd = team_data.get('2nd_prob', 0.02)

            # Model probability for 2nd (conditional)
            if _V11_AVAILABLE and engine:
                try:
                    elo = ELO_RATINGS.get(team, 1700)
                    group_elos = [ELO_RATINGS.get(t, 1700) for t in teams]
                    total_elo = sum(10 ** (e / 400) for e in group_elos)
                    rel_strength = (10 ** (elo / 400)) / total_elo
                    # 2nd place is roughly: rel_strength * (1 - rel_strength) * adjustment
                    model_prob_2nd = rel_strength * (1 - rel_strength) * 1.5
                    model_prob_2nd = min(model_prob_2nd, 0.50)
                except Exception:
                    model_prob_2nd = market_implied_2nd
            else:
                model_prob_2nd = market_implied_2nd

            positions.append({
                'group': group_name,
                'position': '2nd',
                'team': team,
                'market_odds': market_odds_2nd,
                'market_implied_prob': market_implied_2nd,
                'model_prob': model_prob_2nd,
            })

    # Run optimization
    result = optimizer.optimize(budget, positions)

    # Last updated timestamp
    st.caption(f"🕐 {t('last_updated')}: {mc.get_last_updated()}")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 " + t('group_overview_section'),
        "💰 " + t('roi_recommendations_section'),
        "🥧 " + t('portfolio_allocation_section'),
        "📈 " + t('risk_reward_section'),
    ])

    # =========================================================================
    # TAB 1: Group Overview
    # =========================================================================
    with tab1:
        st.header(t('group_overview_section'))

        for group_name, teams in WC2026_GROUPS.items():
            group_data = all_consensus.get(group_name, {})
            st.markdown(f"### {t('col_group')} {group_name}")

            rows = []
            for team in teams:
                td = group_data.get(team, {})
                prob_1st = td.get('1st_prob', 0)
                prob_2nd = td.get('2nd_prob', 0)

                # Color coding
                if prob_1st >= 0.50:
                    color = "🟢"
                elif prob_1st >= 0.25:
                    color = "🟡"
                else:
                    color = "🔴"

                rows.append({
                    '': color,
                    t('col_team'): team,
                    t('col_1st'): f"{prob_1st:.1%}",
                    t('col_2nd'): f"{prob_2nd:.1%}",
                    t('statistical_consensus') + ' (1st)': f"{td.get('1st_odds', 0):.2f}",
                    t('statistical_consensus') + ' (2nd)': f"{td.get('2nd_odds', 0):.2f}",
                })

            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.markdown("---")

    # =========================================================================
    # TAB 2: ROI Recommendations
    # =========================================================================
    with tab2:
        st.header(t('roi_recommendations_section'))

        if not result.top_picks:
            st.info(t('no_edge_found'))
        else:
            # Top picks
            st.markdown(f"### ⭐ {t('top_picks')}")
            for i, pick in enumerate(result.top_picks, 1):
                exp = pick.explanation.get(lang, pick.explanation.get('en', ''))
                st.markdown(f"**{i}. {pick.team}** — {t('col_group')} {pick.group} {pick.position}")
                st.markdown(f"   {t('col_edge')}: {pick.edge_pct:+.1f}% | {t('col_roi')}: {pick.roi_pct:+.1f}% | {t('col_allocation')}: HKD {pick.allocation_hkd:.0f}")
                st.caption(f"💡 {exp}")

            st.markdown("---")

            # Full table
            st.markdown(f"### 📋 {t('value_positions')}")
            table_rows = []
            for pos in result.positions:
                if pos.edge_pct > 0:
                    table_rows.append({
                        t('col_group'): pos.group,
                        t('col_position'): pos.position,
                        t('col_team'): pos.team,
                        t('col_consensus'): f"{pos.market_implied_prob:.1%}",
                        t('col_model'): f"{pos.model_prob:.1%}",
                        t('col_edge'): f"{pos.edge_pct:+.1f}%",
                        t('col_roi'): f"{pos.roi_pct:+.1f}%",
                        t('col_allocation'): f"HKD {pos.allocation_hkd:.0f}",
                    })

            if table_rows:
                st.dataframe(table_rows, use_container_width=True, hide_index=True)
            else:
                st.info(t('no_edge_found'))

    # =========================================================================
    # TAB 3: Portfolio Allocation
    # =========================================================================
    with tab3:
        st.header(t('portfolio_allocation_section'))

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t('budget_label'), f"HKD {budget:,.0f}")
        with col2:
            st.metric(t('total_projected_return'), f"HKD {result.total_expected_return:,.0f}")
        with col3:
            st.metric(t('expected_portfolio_roi'), f"{result.portfolio_roi:+.1f}%")

        st.metric(t('risk_level'), result.risk_level)

        # Pie chart
        allocated = [(p.team, p.allocation_hkd) for p in result.positions if p.allocation_hkd > 0]
        if allocated:
            import plotly.express as px
            labels = [a[0] for a in allocated]
            values = [a[1] for a in allocated]
            unallocated = budget - sum(values)
            if unallocated > 0:
                labels.append("Unallocated" if not is_cn else ("未配置" if lang == 'zh_hans' else "未配置"))
                values.append(unallocated)

            fig = px.pie(
                values=values, names=labels,
                title=t('portfolio_allocation_section'),
                color_discrete_sequence=px.colors.sequential.Greens
            )
            fig.update_layout(
                paper_bgcolor='#1E1E1E',
                font_color='#ECEFF1',
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t('no_edge_found'))

    # =========================================================================
    # TAB 4: Risk / Reward
    # =========================================================================
    with tab4:
        st.header(t('risk_reward_section'))

        # Scatter plot
        positive_positions = [p for p in result.positions if p.edge_pct > 0]
        if positive_positions:
            import plotly.graph_objects as go
            fig = go.Figure()

            x_vals = [p.risk_score for p in positive_positions]
            y_vals = [p.roi_pct for p in positive_positions]
            labels = [f"{p.team} ({p.group} {p.position})" for p in positive_positions]
            sizes = [max(10, p.allocation_hkd / budget * 200) for p in positive_positions]

            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='markers+text',
                text=labels,
                textposition='top center',
                marker=dict(
                    size=sizes,
                    color=[p.edge_pct for p in positive_positions],
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title=t('col_edge')),
                ),
            ))

            fig.update_layout(
                xaxis_title="Risk Score",
                yaxis_title=f"{t('col_roi')} (%)",
                paper_bgcolor='#1E1E1E',
                plot_bgcolor='#121212',
                font_color='#ECEFF1',
                height=500,
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t('no_edge_found'))

    # Bottom disclaimer
    st.markdown("---")
    st.markdown(f"""
    <div style="background:rgba(255,179,0,0.1);border:1px solid #FFB300;border-radius:8px;padding:10px 14px;">
        <p style="margin:0;color:#FFB300;font-size:0.85rem;">⚠️ {t('investment_disclaimer')} {t('model_estimates_note')}</p>
    </div>
    """, unsafe_allow_html=True)

def show_group_combinations():
    """Group Combinations page — all 16 result patterns, 3rd-place projection, convergence"""
    lang = init_language()
    is_cn = lang in ['zh_hant', 'zh_hans']

    st.title("🧩 " + ("小組組合分析" if is_cn else "Group Stage Combinations"))
    st.caption("Formula V12 — 48 Teams × 16 Result Patterns × 3rd-Place Advancement × 10K Monte Carlo")

    if not _GROUP_COMBO_AVAILABLE:
        st.error("Group Combination Engine not available" if not is_cn else "小組組合引擎未載入")
        return

    from wc2026_group_combinations import GroupCombinationEngine
    from formula_v11_emoglyph import WC2026_GROUPS, TEAM_STYLE_CLASSIFICATION

    @st.cache_resource
    def load_combo_engine():
        return GroupCombinationEngine()

    combo = load_combo_engine()

    # Build team list
    all_teams = []
    for teams in WC2026_GROUPS.values():
        all_teams.extend(teams)

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 " + ("球隊組合" if is_cn else "Team Combinations"),
        "🥉 " + ("第三名晉級" if is_cn else "3rd-Place Advancement"),
        "🛡️ " + ("防守反擊優勢" if is_cn else "Defensive Advantage"),
        "📊 " + ("收斂測試" if is_cn else "Convergence Test"),
    ])

    with tab1:
        selected_team = st.selectbox(
            "Select Team" if not is_cn else "選擇球隊",
            all_teams,
            index=all_teams.index("France") if "France" in all_teams else 0,
            key="combo_team_select"
        )

        if st.button("🔍 " + ("分析組合" if is_cn else "Analyze Combinations"), key="combo_analyze_btn"):
            with st.spinner("Calculating combinations..." if not is_cn else "正在計算組合..."):
                combos = combo.generate_team_combinations(selected_team)
                six_pts = combo.detect_six_points_after_two(selected_team)
                must_win = combo.detect_must_win_match3(selected_team)
                rec = combo.project_strategic_recommendation(selected_team, ('zh_hant' if lang == 'zh_hant' else 'zh_hans') if is_cn else 'en')

            # Most likely patterns
            st.markdown("### 📋 " + ("結果模式概率" if is_cn else "Result Pattern Probabilities"))
            sorted_combos = sorted(combos.items(), key=lambda x: x[1], reverse=True)

            for pattern, prob in sorted_combos[:8]:
                pts_map = {"W": 3, "D": 1, "L": 0}
                if pattern == "WW-":
                    points = 6
                    desc = ("✅ 6分已定，可輪換休息！" if is_cn else "6pts secured, can rotate & rest!")
                else:
                    points = sum(pts_map.get(c, 0) for c in pattern)
                    if points >= 7:
                        desc = ("✅ 穩定晉級" if is_cn else "Safe advancement")
                    elif points >= 4:
                        desc = ("⚠️ 邊緣位置" if is_cn else "Borderline position")
                    elif points >= 3:
                        desc = ("🟡 第三名候選" if is_cn else "3rd-place candidate")
                    else:
                        desc = ("❌ 可能淘汰" if is_cn else "Likely eliminated")

                bar_pct = int(prob * 100)
                st.markdown(f"**{pattern}** ({points}pts) — {prob:.1%} {desc}")
                st.progress(min(1.0, prob), text=f"{pattern}: {prob:.1%}")

            # 6-points-after-2 detection
            st.markdown("### 🔑 " + ("6分戰略優勢" if is_cn else "6-Point Strategic Advantage"))
            if six_pts['probability'] > 0.3:
                st.success(f"✅ {six_pts['probability']:.1%} " + ("概率可在前2場獲6分" if is_cn else "chance of 6 points after 2 matches"))
            else:
                st.warning(f"⚠️ {six_pts['probability']:.1%} " + ("概率可在前2場獲6分" if is_cn else "chance of 6 points after 2 matches"))
            st.caption(six_pts.get('strategic_implication', ''))

            # Must-win match 3
            st.markdown("### ⚡ " + ("必勝第三場" if is_cn else "Must-Win Match 3"))
            if must_win['must_win_probability'] > 0.2:
                st.error(f"🔥 {must_win['must_win_probability']:.1%} " +
                         ("概率第三場必須贏！" if is_cn else "chance match 3 is MUST-WIN!"))
            else:
                st.info(f"ℹ️ {must_win['must_win_probability']:.1%} " +
                        ("概率第三場必須贏" if is_cn else "chance match 3 is must-win"))
            if must_win.get('match3_opponent'):
                st.caption(("第三場對手" if is_cn else "Match 3 opponent") + f": {must_win['match3_opponent']}")

            # Strategic recommendation
            st.markdown("### 🧠 " + ("戰略建議" if is_cn else "Strategic Recommendation"))
            st.info(rec)

    with tab2:
        st.markdown("### 🥉 " + ("第三名晉級預測" if is_cn else "3rd-Place Advancement Projection"))

        if st.button("🔮 " + ("預測第三名晉級" if is_cn else "Project 3rd-Place Advancement"), key="third_place_btn"):
            with st.spinner("Simulating group stages..." if not is_cn else "正在模擬小組賽..."):
                third_place = combo.project_third_place_rankings()

            st.markdown("#### " + ("晉級的8支第三名球隊" if is_cn else "Top 8 3rd-Place Teams Advancing"))
            for i, team_data in enumerate(third_place[:8], 1):
                team_name = team_data['team']
                pts = team_data['expected_points']
                gd = team_data['expected_gd']
                style = TEAM_STYLE_CLASSIFICATION.get(team_name, "balanced")
                style_icon = {"defensive_counter": "🛡️", "attacking_possession": "⚔️", "balanced": "⚖️"}.get(style, "⚖️")

                st.markdown(f"**{i}. {style_icon} {team_name}** — {pts:.1f}pts, GD: {gd:+.1f}")

            st.markdown("#### " + ("被淘汰的第三名球隊" if is_cn else "3rd-Place Teams Eliminated"))
            for team_data in third_place[8:]:
                team_name = team_data['team']
                pts = team_data['expected_points']
                gd = team_data['expected_gd']
                st.markdown(f"❌ {team_name} — {pts:.1f}pts, GD: {gd:+.1f}")

        # Per-team 3rd-place probability
        st.markdown("---")
        st.markdown("#### " + ("單隊第三名晉級概率" if is_cn else "Per-Team 3rd-Place Advancement Probability"))
        tp_team = st.selectbox(
            "Select Team" if not is_cn else "選擇球隊",
            all_teams,
            index=all_teams.index("Morocco") if "Morocco" in all_teams else 0,
            key="tp_team_select"
        )

        if st.button("📊 " + ("計算概率" if is_cn else "Calculate Probability"), key="tp_calc_btn"):
            tp_prob = combo.project_third_place_advancement_probability(tp_team)
            prob_val = tp_prob.get('advancement_probability', 0)

            if prob_val > 0.5:
                st.success(f"✅ {tp_team}: {prob_val:.1%} " + ("晉級概率" if is_cn else "advancement probability"))
            elif prob_val > 0.2:
                st.warning(f"⚠️ {tp_team}: {prob_val:.1%} " + ("晉級概率" if is_cn else "advancement probability"))
            else:
                st.error(f"❌ {tp_team}: {prob_val:.1%} " + ("晉級概率" if is_cn else "advancement probability"))

            if tp_prob.get('r32_opponent'):
                st.caption(("R32 對手" if is_cn else "R32 Opponent") + f": {tp_prob['r32_opponent']}")
            else:
                r32_info = combo.project_r32_opponent_for_third_place(tp_team)
                if 'projected_opponent' in r32_info:
                    st.caption(("R32 對手" if is_cn else "R32 Opponent") + f": {r32_info['r32_matchup']} (upset {r32_info['upset_probability']:.0%})")

    with tab3:
        st.markdown("### 🛡️ " + ("防守反擊 vs 進攻控球" if is_cn else "Defensive Counter vs Attacking Possession"))

        if _V11_AVAILABLE:
            from formula_v11_emoglyph import TEAM_STYLE_CLASSIFICATION

            # Count by style
            style_counts = {}
            for team, style in TEAM_STYLE_CLASSIFICATION.items():
                style_counts[style] = style_counts.get(style, 0) + 1

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🛡️ " + ("防守反擊" if is_cn else "Defensive Counter"), style_counts.get("defensive_counter", 0))
            with col2:
                st.metric("⚔️ " + ("進攻控球" if is_cn else "Attacking Possession"), style_counts.get("attacking_possession", 0))
            with col3:
                st.metric("⚖️ " + ("均衡" if is_cn else "Balanced"), style_counts.get("balanced", 0))

            st.markdown("#### " + ("極端條件下的優勢" if is_cn else "Advantage in Extreme Conditions"))
            st.markdown(("| 條件 | 防守反擊 | 進攻控球 | 淨差異 |\n|---|---|---|---|\n| 🌡️ 極端高溫 (WBGT>28°C) | +5% | -5% | 10% |\n| ⛰️ 高海拔 (>1500m) | +3% | -3% | 6% |\n| 🌡️+⛰️ 兩者疊加 | +8% | -8% | 16% |"
                         if is_cn else
                         "| Condition | Defensive Counter | Attacking Possession | Net Swing |\n|---|---|---|---|\n| 🌡️ Extreme Heat (WBGT>28°C) | +5% | -5% | 10% |\n| ⛰️ Altitude (>1500m) | +3% | -3% | 6% |\n| 🌡️+⛰️ Both Combined | +8% | -8% | 16% |"))

            # List teams by style
            for style_name, icon in [("defensive_counter", "🛡️"), ("attacking_possession", "⚔️"), ("balanced", "⚖️")]:
                teams_in_style = [t for t, s in TEAM_STYLE_CLASSIFICATION.items() if s == style_name]
                style_label = {"defensive_counter": "防守反擊" if is_cn else "Defensive Counter",
                              "attacking_possession": "進攻控球" if is_cn else "Attacking Possession",
                              "balanced": "均衡" if is_cn else "Balanced"}[style_name]
                with st.expander(f"{icon} {style_label} ({len(teams_in_style)})"):
                    st.markdown(", ".join(teams_in_style))

    with tab4:
        st.markdown("### 📊 " + ("蒙特卡洛收斂測試" if is_cn else "Monte Carlo Convergence Test"))

        n_iter = st.selectbox(
            "Max Iterations" if not is_cn else "最大迭代次數",
            [1000, 2000, 5000, 10000],
            index=0,
            key="convergence_iter"
        )

        if st.button("🚀 " + ("運行收斂測試" if is_cn else "Run Convergence Test"), key="convergence_btn"):
            if _V11_AVAILABLE:
                with st.spinner(f"Running {n_iter} simulations..." if not is_cn else f"正在運行 {n_iter} 次模擬..."):
                    v11 = load_v11_engine()
                    convergence = v11.simulate_tournament_convergence(n_max=n_iter)

                # Convergence status
                status = convergence['convergence_status']
                status_icon = "✅" if status == "Converged" else "⚠️"
                st.markdown(f"### {status_icon} {status}")
                st.caption(convergence.get('convergence_detail', ''))

                # Top teams at each checkpoint
                st.markdown("#### " + ("各檢查點結果" if is_cn else "Results at Each Checkpoint"))
                for ck_name, ck_data in convergence.get('checkpoints', {}).items():
                    stability = ck_data.get('top5_stability', 0)
                    stab_icon = "🟢" if stability < 0.01 else "🟡" if stability < 0.03 else "🔴"
                    preds = ck_data.get('predictions', {})
                    top3 = list(preds.items())[:3]
                    top3_str = " | ".join([f"{t}: {p.get('win_probability', 0):.1%}" for t, p in top3])
                    st.markdown(f"**{ck_name} iters** {stab_icon} stability: {stability:.2%} — {top3_str}")

                # Confidence interval
                ci_data = convergence.get('confidence_intervals', {})
                if ci_data.get('top_team'):
                    tt = ci_data['top_team']
                    st.markdown("#### " + ("95% 信心區間" if is_cn else "95% Confidence Interval"))
                    st.info(f"**{tt['team']}**: {tt['win_prob']:.1%} ± {tt['ci_95'][1] - tt['win_prob']:.1%}")

                # Upset detection
                upsets = convergence.get('upset_detection', [])
                if upsets:
                    st.markdown("#### " + ("爆冷檢測" if is_cn else "Upset Detection"))
                    for upset in upsets[:5]:
                        st.warning(f"🔥 {upset['match']}: Model {upset['model_prob']:.0%} vs Elo {upset['elo_prob']:.0%} (divergence: {upset['divergence']:.0%})")
            else:
                st.error(t('v12_engine_not_available'))

if __name__ == "__main__":
    main()
