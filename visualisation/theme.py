"""
feature_theme.py
----------------
Dark / Light theme toggle and CSS injection for BioOptimize.

HOW TO INTEGRATE into code1.py (app):
  1. Import at top:
        from feature_theme import render_theme_toggle, get_theme_css
  2. Near the top of the app (before any other UI), add:
        _ui_theme = render_theme_toggle()
        st.markdown(get_theme_css(_ui_theme), unsafe_allow_html=True)
  3. Pass `theme=_ui_theme` to plot_growth_bar() and plot_sensitivity() in visuals.py.
     (See feature_visuals.py for the updated plotting functions.)
"""

import streamlit as st


def render_theme_toggle() -> str:
    """
    Renders a fixed top-right 🌙 / ☀️ radio toggle.
    Returns 'dark' or 'light'.
    """
    mode = st.radio(
        "🌙 / ☀️",
        ["🌙", "☀️"],
        horizontal=True,
        key="display_mode",
        label_visibility="collapsed",
    )
    return "dark" if mode == "🌙" else "light"


def get_theme_css(theme: str) -> str:
    """
    Returns a full <style> block for the chosen theme.
    Inject with: st.markdown(get_theme_css(theme), unsafe_allow_html=True)
    """
    is_dark = theme == "dark"
    bg = "#000000" if is_dark else "#ffffff"
    surface = "#111111" if is_dark else "#f5f5f5"
    border = "#333333" if is_dark else "#d4d4d4"
    text = "#ffffff" if is_dark else "#000000"
    logo_filter = "invert(1)" if is_dark else "none"
    hr_color = "#ffffff" if is_dark else "#cccccc"

    return f"""
<style>
    :root {{
        --gem-bg: {bg};
        --gem-surface: {surface};
        --gem-text: {text};
        --gem-orange: #f97316;
        --gem-border: {border};
        --fs-section-title: 1.725rem;
        --fs-base: 1.4025rem;
        --fs-caption: 1.254rem;
        --fs-tagline: 1.452rem;
        --fs-accent: 1.452rem;
        --fs-brand: clamp(3.9rem, 7.8vw, 5.07rem);
    }}

    /* ── Global background / text ── */
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                     "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        background-color: var(--gem-bg) !important;
        color: var(--gem-text) !important;
    }}
    .main .block-container {{
        padding-top: 2rem;
        padding-left: 8% !important;
        padding-right: 8% !important;
        color: var(--gem-text);
        font-size: var(--fs-base);
        line-height: 1.5;
    }}
    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3,
    .main .block-container h4 {{
        font-size: var(--fs-section-title) !important;
        line-height: 1.3 !important;
        font-weight: 600 !important;
        color: var(--gem-text) !important;
    }}

    /* ── Hide sidebar ── */
    section[data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

    /* ── Header bar ── */
    header[data-testid="stHeader"] {{
        background-color: var(--gem-bg) !important;
    }}
    header[data-testid="stHeader"] button {{
        color: var(--gem-text) !important;
    }}

    /* ── General text ── */
    .main .block-container strong {{ color: var(--gem-text) !important; }}
    .main .block-container .stMarkdown,
    .main .block-container label,
    .main .block-container p:not(.brand-title):not(.tagline):not(.drag-hint-text) {{
        color: var(--gem-text) !important;
    }}
    .main .block-container a {{ color: var(--gem-orange) !important; }}
    .stCaption, [data-testid="stCaption"] {{
        color: var(--gem-text) !important;
        font-size: var(--fs-caption) !important;
    }}

    /* ── Metric cards ── */
    .stMetric {{
        background-color: var(--gem-surface) !important;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid var(--gem-border);
        box-shadow: none;
        font-size: var(--fs-base) !important;
        color: var(--gem-text) !important;
    }}
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMarkdownContainer"] p {{
        color: var(--gem-text) !important;
    }}

    /* ── Buttons (default) ── */
    .stButton > button {{
        width: 100%;
        border-radius: 8px;
        min-height: 2.75rem;
        font-weight: 600;
        font-size: var(--fs-base) !important;
        background-color: var(--gem-surface) !important;
        color: var(--gem-text) !important;
        border: 1px solid var(--gem-border) !important;
    }}
    .stButton > button:hover {{
        border-color: var(--gem-orange) !important;
        color: var(--gem-text) !important;
    }}

    /* ── Primary "Run GEM engine" button — solid orange ── */
    button[data-testid="baseButton-primary"],
    button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
        background-color: var(--gem-orange) !important;
        color: #0a0a0a !important;
        border: none !important;
        box-shadow: 0 4px 24px rgba(249, 115, 22, 0.35) !important;
        min-height: 3.25rem !important;
        font-size: var(--fs-accent) !important;
        font-weight: 700 !important;
    }}
    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {{
        background-color: #ea580c !important;
        color: #0a0a0a !important;
    }}
    button[data-testid="baseButton-primary"] *,
    button[data-testid="baseButton-primary"] p {{
        color: #0a0a0a !important;
    }}

    /* ── Header banner ── */
    .header-banner {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem 0 1.5rem;
        min-height: 12vh;
    }}
    .header-logo {{
        max-height: 110px;
        width: auto;
        height: auto;
        display: block;
        filter: {logo_filter};
    }}

    /* ── Brand title / tagline ── */
    .brand-title {{
        font-family: inherit;
        font-size: clamp(5rem, 10vw, 7rem);
        font-weight: 700;
        text-align: center;
        margin: 0.5rem 0;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }}
    .brand-title .gem  {{ color: var(--gem-orange) !important; }}
    .brand-title .timise {{ color: var(--gem-text) !important; }}
    .tagline {{
        text-align: center;
        color: var(--gem-text) !important;
        margin: 0 0 2rem 0;
        font-size: clamp(1.4rem, 2.8vw, 2rem);
        font-weight: 500;
        line-height: 1.45;
    }}
    .drag-hint-text {{
        text-align: center;
        color: var(--gem-orange) !important;
        font-size: var(--fs-accent);
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: 0.02em;
    }}
    section[data-testid="stFileUploader"] label p {{
        font-size: var(--fs-accent) !important;
        font-weight: 700 !important;
        color: var(--gem-text) !important;
    }}

    /* ── Select / radio inputs ── */
    [data-baseweb="radio"] label,
    [data-baseweb="select"] label {{ color: var(--gem-text) !important; }}
    div[data-baseweb="select"] > div {{
        background-color: var(--gem-surface) !important;
        border-color: var(--gem-border) !important;
        color: var(--gem-text) !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent !important;
        gap: 0.5rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: var(--gem-text) !important;
        font-size: var(--fs-base) !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: var(--gem-orange) !important;
        border-bottom-color: var(--gem-orange) !important;
    }}

    /* ── Expander ── */
    [data-testid="stExpander"] {{
        background-color: var(--gem-surface);
        border: 1px solid var(--gem-border);
        border-radius: 8px;
    }}

    /* ── Alert / notification banners ── */
    [data-testid="stAlert"] {{
        background-color: var(--gem-surface) !important;
        color: var(--gem-text) !important;
        border: 1px solid var(--gem-border) !important;
    }}
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] div,
    [data-testid="stAlert"] span {{ color: var(--gem-text) !important; }}
    [data-testid="stAlert"][data-baseweb="notification"] {{ border-left-width: 4px !important; }}
    div[data-testid="stSuccessNotification"] {{ border-left-color: #22c55e !important; }}
    div[data-testid="stErrorNotification"]   {{ border-left-color: #ef4444 !important; }}
    div[data-testid="stWarningNotification"] {{ border-left-color: var(--gem-orange) !important; }}
    div[data-testid="stInfoNotification"]    {{ border-left-color: #38bdf8 !important; }}

    /* ── Force strict text colour everywhere ── */
    .stApp, .stApp *,
    [data-testid="stAppViewContainer"] *,
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stText, label, p, span, div, li, td, th {{
        color: var(--gem-text) !important;
    }}
    /* Orange stays orange */
    .gem, .brand-title .gem,
    .stTabs [aria-selected="true"],
    .drag-hint-text,
    .stApp a {{ color: var(--gem-orange) !important; }}

    /* ── Radio dot: orange, no highlight on selected label ── */
    [data-baseweb="radio"] [aria-checked="true"],
    [data-baseweb="radio"] [role="radio"][aria-checked="true"],
    [data-baseweb="radio"] [aria-checked="true"] > div:first-child {{
        background-color: transparent !important;
        box-shadow: none !important;
    }}
    [data-baseweb="radio"] [aria-checked="true"] div[class] {{
        border-color: var(--gem-orange) !important;
    }}
    [data-baseweb="radio"] [aria-checked="true"] div[class] > div,
    [data-baseweb="radio"] input:checked ~ div div div {{
        background-color: var(--gem-orange) !important;
    }}
    [data-baseweb="radio"] [aria-checked="true"] svg circle {{
        fill: var(--gem-orange) !important;
        stroke: var(--gem-orange) !important;
    }}

    /* ── Horizontal rule ── */
    hr {{
        border: none !important;
        border-top: 1.5px solid {hr_color} !important;
        opacity: 1 !important;
        margin: 1rem 0 !important;
    }}

    /* ── Theme toggle: fixed top-right ── */
    div[data-testid="stRadio"]:has(input[name="display_mode"]) {{
        position: fixed !important;
        top: 0.55rem !important;
        right: 1.5rem !important;
        left: auto !important;
        z-index: 9999 !important;
        background: transparent !important;
        width: auto !important;
    }}
    div[data-testid="stRadio"]:has(input[name="display_mode"]) label,
    div[data-testid="stRadio"]:has(input[name="display_mode"]) p {{
        font-size: 1.35rem !important;
    }}
</style>
"""
