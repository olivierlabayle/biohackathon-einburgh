"""
feature_header.py
-----------------
Branded header: logo banner, GEMtimise title, tagline.

HOW TO INTEGRATE into code1.py (app):
  1. Import at top:
        from feature_header import render_header
  2. Call once at the very top of your main UI (after CSS injection):
        render_header(theme)   # pass 'dark' or 'light' from feature_theme.py

  Note: The logo_filter (invert) is already handled by feature_theme.py CSS,
  so the logo URL is always the same regardless of theme.
"""

import streamlit as st

# Remote logo — black artwork; CSS filter inverts it to white on dark backgrounds.
_HEADER_LOGO_URL = "https://www.ingredientsnetwork.com/COLOR%20LOGO-BLACK-comp324183.png"


def render_header(theme: str = "dark") -> None:
    """
    Renders the full branded header:
      - Centred logo image (inverted automatically in dark mode via CSS)
      - GEMtimise brand title (GEM in orange, timise in theme text colour)
      - Subtitle tagline
    """
    # Logo banner
    st.markdown(
        f'<div class="header-banner">'
        f'<img src="{_HEADER_LOGO_URL}" alt="Brand logo" '
        f'class="header-logo" loading="lazy" />'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Brand title + tagline
    st.markdown(
        '<p class="brand-title">'
        '<span class="gem">GEM</span>'
        '<span class="timise">timise</span>'
        "</p>"
        '<p class="tagline">Automated GEM generation and media optimization</p>',
        unsafe_allow_html=True,
    )
