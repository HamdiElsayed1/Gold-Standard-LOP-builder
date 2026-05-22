"""
McKinsey-style theme for the Streamlit app.

Single public entry point: `inject_theme_css()`. Call it once, immediately
after `st.set_page_config(...)` in app.py and before any other Streamlit
elements render so the styles apply globally.

Design tokens mirror the ones encoded in
inputs/slide_workspace_v0/css/slide.css so the app chrome and the
rendered HTML slides feel like one product:

  - Navy           #051C2C   primary text, headers, primary button fill
  - Electric Blue  #1F40E6   accent (focus rings, hover, links)
  - Warm gray      #F5F3F0   app background
  - White                    main content / cards
  - Border light   #E1DDD7   dividers, input borders
  - Georgia                  headline typeface (matches --font-title)
  - system-ui                body typeface

The companion `.streamlit/config.toml` handles theming Streamlit owns
natively (background, primary colour, focus ring, progress bar fill).
This module covers everything that config.toml cannot reach: typography,
expander/divider/alert chrome, button radii, sidebar polish, etc.
"""

from __future__ import annotations

import streamlit as st


_THEME_CSS = """
<style>
:root {
  --mck-navy: #051C2C;
  --mck-navy-soft: #1A3349;
  --mck-blue: #1F40E6;
  --mck-cyan: #00A9F4;
  --mck-warm: #F5F3F0;
  --mck-warm-soft: #FBFAF8;
  --mck-border: #E1DDD7;
  --mck-text: #1A1A1A;
  --mck-text-muted: #4A5568;
  --mck-text-light: #718096;
  --mck-success: #10B981;
  --mck-warning: #F59E0B;
  --mck-error:   #DC2626;

  --mck-font-body:  system-ui, -apple-system, BlinkMacSystemFont,
                    'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --mck-font-title: Georgia, 'Times New Roman', serif;
  --mck-font-mono:  'SF Mono', Menlo, Consolas, 'Courier New', monospace;
}

/* ── App container ─────────────────────────────────────────────────── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  font-family: var(--mck-font-body);
  color: var(--mck-text);
  background-color: var(--mck-warm);
}

/* Center the main column with comfortable margins, capped width. */
.block-container,
[data-testid="stAppViewBlockContainer"] {
  padding-top: 2.5rem !important;
  padding-bottom: 4rem !important;
  max-width: 1080px;
}

/* Top toolbar — slim and transparent. */
[data-testid="stHeader"] {
  background: transparent !important;
  height: auto !important;
  box-shadow: none !important;
}

/* ── Headlines ─────────────────────────────────────────────────────── */
h1, h2, h3, h4 {
  font-family: var(--mck-font-title) !important;
  color: var(--mck-navy) !important;
  letter-spacing: -0.01em;
  line-height: 1.2;
  font-weight: 700;
}
h1 { font-size: 2rem    !important; margin-bottom: 0.4rem !important; }
h2 { font-size: 1.55rem !important; margin-bottom: 0.4rem !important; }
h3 { font-size: 1.25rem !important; margin-bottom: 0.4rem !important; }
h4 { font-size: 1.05rem !important; }

/* Body paragraphs — comfortable reading line height. */
.stMarkdown p, .stMarkdown li {
  line-height: 1.6;
  color: var(--mck-text);
}

/* Caption / helper text — muted, slightly tighter. */
[data-testid="stCaptionContainer"],
.stCaption {
  color: var(--mck-text-muted) !important;
  font-size: 0.82rem !important;
  letter-spacing: 0.01em;
}

/* ── Sidebar ───────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background-color: #FFFFFF;
  border-right: 1px solid var(--mck-border);
}
[data-testid="stSidebar"] h1 {
  font-family: var(--mck-font-title) !important;
  font-size: 1.35rem !important;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--mck-navy) !important;
  margin-bottom: 0.5rem !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
  font-size: 0.78rem !important;
  letter-spacing: 0.02em;
}
[data-testid="stSidebar"] hr {
  margin: 1rem 0 !important;
}

/* ── Buttons ───────────────────────────────────────────────────────── */
.stButton > button,
[data-testid="stDownloadButton"] > button {
  font-family: var(--mck-font-body);
  font-weight: 600;
  border-radius: 4px;
  border: 1px solid var(--mck-navy);
  color: var(--mck-navy);
  background-color: #FFFFFF;
  padding: 0.45rem 1.1rem;
  letter-spacing: 0.02em;
  box-shadow: none;
  transition: background-color 120ms ease,
              color           120ms ease,
              border-color    120ms ease;
}
.stButton > button:hover,
[data-testid="stDownloadButton"] > button:hover {
  background-color: var(--mck-navy);
  color: #FFFFFF;
  border-color: var(--mck-navy);
}
.stButton > button:focus,
.stButton > button:focus-visible,
[data-testid="stDownloadButton"] > button:focus,
[data-testid="stDownloadButton"] > button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--mck-blue) !important;
}

/* Primary variant — solid navy. */
.stButton > button[kind="primary"] {
  background-color: var(--mck-navy);
  color: #FFFFFF;
  border-color: var(--mck-navy);
}
.stButton > button[kind="primary"]:hover {
  background-color: var(--mck-navy-soft);
  border-color: var(--mck-navy-soft);
}

/* Disabled state. */
.stButton > button:disabled,
.stButton > button[disabled] {
  opacity: 0.45;
  cursor: not-allowed;
}

/* ── Expanders ─────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
  border: 1px solid var(--mck-border) !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  background-color: #FFFFFF !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] details > summary {
  font-family: var(--mck-font-body);
  font-weight: 600;
  color: var(--mck-navy) !important;
}
[data-testid="stExpander"] summary:hover {
  color: var(--mck-blue) !important;
}

/* ── Dividers ──────────────────────────────────────────────────────── */
hr,
[data-testid="stHorizontalBlock"] hr {
  border: none !important;
  border-top: 1px solid var(--mck-border) !important;
  margin: 1.4rem 0 !important;
  background: transparent !important;
}

/* ── Progress bar ──────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div > div > div {
  background-color: var(--mck-navy) !important;
}

/* ── Alerts (success / warning / error / info) ─────────────────────── */
/* Replace Streamlit's full-fill backgrounds with a flat near-white card
   carrying a 3px left border in the semantic colour. The inner content
   testids (Streamlit 1.30+) tell us which type each alert is. */
[data-testid="stAlert"] {
  border: 1px solid var(--mck-border) !important;
  border-left: 3px solid var(--mck-text-muted) !important;
  border-radius: 4px !important;
  background-color: var(--mck-warm-soft) !important;
  box-shadow: none !important;
  color: var(--mck-text) !important;
  padding: 0.6rem 0.9rem !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span {
  color: var(--mck-text) !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {
  border-left-color: var(--mck-success) !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {
  border-left-color: var(--mck-warning) !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {
  border-left-color: var(--mck-error) !important;
}
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) {
  border-left-color: var(--mck-blue) !important;
}

/* ── Inputs (text input, textarea, number input) ───────────────────── */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input {
  font-family: var(--mck-font-body) !important;
  border: 1px solid var(--mck-border) !important;
  border-radius: 4px !important;
  background-color: #FFFFFF !important;
  color: var(--mck-text) !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus,
.stDateInput input:focus {
  border-color: var(--mck-navy) !important;
  box-shadow: 0 0 0 2px rgba(31, 64, 230, 0.18) !important;
  outline: none !important;
}

/* Selectbox / multiselect chrome. */
.stSelectbox > div > div,
.stMultiSelect > div > div {
  border: 1px solid var(--mck-border) !important;
  border-radius: 4px !important;
  background-color: #FFFFFF !important;
}

/* Radio buttons — body font, navy when selected (selected dot uses
   primaryColor from config.toml, which is navy). */
.stRadio > div,
.stRadio label {
  font-family: var(--mck-font-body) !important;
}

/* ── Tabs ──────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  border-bottom: 1px solid var(--mck-border) !important;
  gap: 1.5rem;
}
.stTabs [role="tab"] {
  font-family: var(--mck-font-body) !important;
  font-weight: 600;
  color: var(--mck-text-muted) !important;
  border-bottom: 2px solid transparent !important;
  padding: 0.4rem 0.1rem !important;
}
.stTabs [role="tab"][aria-selected="true"] {
  color: var(--mck-navy) !important;
  border-bottom-color: var(--mck-navy) !important;
}

/* ── File uploader dropzone ────────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
  border: 1px dashed var(--mck-border) !important;
  border-radius: 4px !important;
  background-color: #FFFFFF !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--mck-navy) !important;
}

/* ── Code blocks ───────────────────────────────────────────────────── */
code, pre, kbd, samp {
  font-family: var(--mck-font-mono) !important;
  font-size: 0.86em !important;
}
.stMarkdown code:not(pre code) {
  background-color: var(--mck-warm) !important;
  color: var(--mck-navy) !important;
  padding: 0.1em 0.35em;
  border-radius: 3px;
}
pre {
  background-color: #FFFFFF !important;
  border: 1px solid var(--mck-border) !important;
  border-radius: 4px;
  padding: 0.75rem !important;
}

/* ── DataFrame ─────────────────────────────────────────────────────── */
[data-testid="stDataFrame"],
[data-testid="stTable"] {
  border: 1px solid var(--mck-border);
  border-radius: 4px;
}

/* ── Metrics ───────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background-color: #FFFFFF;
  border: 1px solid var(--mck-border);
  border-radius: 4px;
  padding: 0.75rem 1rem;
}
[data-testid="stMetricValue"] {
  font-family: var(--mck-font-title) !important;
  color: var(--mck-navy) !important;
}
[data-testid="stMetricLabel"] {
  color: var(--mck-text-muted) !important;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  font-size: 0.72rem !important;
}

/* ── Audio recorder / audio player ─────────────────────────────────── */
audio {
  width: 100%;
}

/* ── Streamlit running indicator (top-right spinner) ───────────────── */
[data-testid="stStatusWidget"] {
  font-family: var(--mck-font-body);
}
</style>
"""


def inject_theme_css() -> None:
    """
    Inject the McKinsey theme stylesheet into the current Streamlit page.

    Idempotent in practice: Streamlit re-runs the script on every
    interaction, so calling this once at the top of `app.py` re-applies
    the styles on every rerun. The `<style>` block is hidden from view
    via `unsafe_allow_html=True` and adds no visible whitespace.
    """
    st.markdown(_THEME_CSS, unsafe_allow_html=True)
