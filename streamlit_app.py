"""
PolarityIQ RAG Pipeline — Streamlit Web Interface
Matches the luxury Flask UI with full functionality
"""
import streamlit as st
import json
import os
from retrieval import query, _load, _meta
from datetime import datetime

# ── Configuration ──
st.set_page_config(
    page_title="PolarityIQ — Family Office Intelligence",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Pre-load Vector Store ──
@st.cache_resource
def load_and_init():
    try:
        _load()
        return True
    except Exception as e:
        st.error(f"❌ Cannot load vector store: {str(e)}\n\nRun `python ingest.py` first.")
        return False

if not load_and_init():
    st.stop()

# ── Custom CSS (exact match to Flask luxury design) ──
st.markdown("""
<style>
    :root {
        --bg: #0a0c0f;
        --surface: #111318;
        --surface2: #181c23;
        --surface3: #1e2330;
        --border: #252b38;
        --border2: #2e3547;
        --gold: #c9a84c;
        --gold-dim: #a07830;
        --teal: #3dd9c4;
        --teal-dim: #1e9e8e;
        --text: #e8ecf4;
        --text2: #9aa3b5;
        --text3: #5a6478;
    }
    
    /* Global overrides */
    [data-testid="stAppViewContainer"] {
        background: var(--bg);
    }
    
    [data-testid="stMainBlockContainer"] {
        background: var(--bg);
        padding: 0;
    }
    
    section[data-testid="stAppViewContainer"] > div:first-child {
        background: var(--bg);
    }
    
    .stMarkdown {
        color: var(--text);
    }
    
    /* Header */
    .header-gold {
        color: var(--gold);
        font-weight: 600;
        font-size: 2.4rem;
    }
    
    /* Stats bar */
    .stats-row {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .stat-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.2s;
    }
    
    .stat-card:hover {
        background: var(--surface2);
        border-color: var(--gold);
    }
    
    .stat-num {
        font-size: 1.8rem;
        font-weight: 600;
        color: var(--gold);
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: var(--text3);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Search box */
    .stTextInput input {
        background: var(--surface) !important;
        border: 1px solid var(--border2) !important;
        color: var(--text) !important;
        border-radius: 10px !important;
        padding: 1rem 1.2rem !important;
    }
    
    .stTextInput input:focus {
        border-color: var(--gold-dim) !important;
        box-shadow: 0 0 0 3px rgba(201,168,76,0.12) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: var(--gold) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
    }
    
    .stButton > button:hover {
        background: #d4af60 !important;
    }
    
    /* Example chips */
    .example-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .stButton > button.chip {
        background: var(--surface2) !important;
        border: 1px solid var(--border2) !important;
        color: var(--text2) !important;
        border-radius: 100px !important;
        padding: 0.4rem 0.9rem !important;
        font-size: 0.85rem !important;
    }
    
    .stButton > button.chip:hover {
        background: var(--surface3) !important;
        border-color: var(--gold-dim) !important;
        color: var(--gold) !important;
    }
    
    /* Results */
    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.5rem;
    }
    
    .result-count {
        font-size: 0.9rem;
        color: var(--text3);
    }
    
    /* AI Panel */
    .ai-panel {
        background: var(--surface);
        border: 1px solid var(--border2);
        border-left: 3px solid var(--teal);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--teal);
        margin-bottom: 0.75rem;
    }
    
    .ai-badge-dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: var(--teal);
    }
    
    /* Record cards */
    .record-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
        transition: all 0.2s;
    }
    
    .record-card:hover {
        border-color: var(--border2);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    
    .card-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        padding: 1.2rem;
        border-bottom: 1px solid var(--border);
        gap: 1rem;
    }
    
    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text);
        line-height: 1.25;
    }
    
    .badge {
        display: inline-block;
        border-radius: 4px;
        padding: 0.25rem 0.6rem;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        white-space: nowrap;
    }
    
    .badge-sfo {
        background: rgba(201,168,76,0.12);
        color: var(--gold);
        border: 1px solid rgba(201,168,76,0.2);
    }
    
    .badge-mfo {
        background: rgba(61,217,196,0.08);
        color: var(--teal);
        border: 1px solid rgba(61,217,196,0.2);
    }
    
    .card-body {
        padding: 1rem;
    }
    
    .card-row {
        display: flex;
        align-items: flex-start;
        gap: 0.7rem;
        margin-bottom: 0.75rem;
        font-size: 0.9rem;
    }
    
    .card-icon {
        font-size: 0.9rem;
        flex-shrink: 0;
        width: 1.2rem;
        margin-top: 0.1rem;
    }
    
    .card-label {
        font-size: 0.75rem;
        color: var(--text3);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        width: 60px;
        flex-shrink: 0;
    }
    
    .card-value {
        color: var(--text2);
        flex: 1;
    }
    
    .card-value strong {
        color: var(--text);
        font-weight: 500;
    }
    
    .card-value a {
        color: var(--teal);
        text-decoration: none;
        font-size: 0.85rem;
    }
    
    .card-value a:hover {
        text-decoration: underline;
    }
    
    /* Score bar */
    .score-bar-wrap {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-top: 0.75rem;
    }
    
    .score-bar {
        height: 3px;
        border-radius: 2px;
        background: var(--border);
        flex: 1;
        overflow: hidden;
    }
    
    .score-fill {
        height: 100%;
        border-radius: 2px;
        background: linear-gradient(90deg, var(--gold-dim), var(--gold));
    }
    
    .score-label {
        font-size: 0.75rem;
        color: var(--text3);
        flex-shrink: 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: var(--text2);
        font-size: 0.85rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border);
    }
    
    .footer strong {
        color: var(--gold);
    }
    
    /* Containers */
    .stContainer {
        background: transparent !important;
    }
    
    [data-testid="stMetric"] {
        background: transparent !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border2);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text3);
    }
    
    @media (max-width: 768px) {
        .stats-row {
            grid-template-columns: repeat(2, 1fr);
        }
    }
</style>
""", unsafe_allow_html=True)

# ── Header (Flask style) ──
st.markdown("""
<div style="border-bottom:1px solid #252b38; padding:1.2rem 0; margin-bottom:2rem;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap:0.8rem;">
            <div style="width:28px; height:28px; background:#c9a84c; clip-path:polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%); display:flex; align-items:center; justify-content:center; font-family:monospace; font-size:8px; color:#000; font-weight:500;">PIQ</div>
            <div style="font-family:Georgia, serif; font-size:1.4rem; font-weight:700; color:#e8ecf4; letter-spacing:-0.02em;">Polarity<span style="color:#c9a84c;">IQ</span></div>
        </div>
        <div style="text-align:right; font-family:monospace; font-size:0.7rem; color:#5a6478; line-height:1.5;">
            <div style="color:#3dd9c4; display:inline-flex; gap:0.4rem; align-items:center; font-size:0.65rem; margin-bottom:0.2rem;"><span style="width:4px; height:4px; background:#3dd9c4; border-radius:50%;"></span>RAG Pipeline Active</div><br>
            250 Family Offices · 28 Intelligence Fields
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Hero Section ──
st.markdown("""
<div style="text-align:center; padding:3rem 0 2rem; margin-bottom:2rem;">
    <div style="font-family:monospace; font-size:0.7rem; letter-spacing:0.18em; text-transform:uppercase; color:#c9a84c; margin-bottom:1.2rem; opacity:0.8;">Family Office Intelligence Platform</div>
    <h1 style="color:#e8ecf4; font-size:2.4rem; font-weight:700; margin:0 0 1rem 0; line-height:1.2;">
        Query the world's family offices<br>in <em style="font-style:italic; color:#c9a84c;">natural language</em>
    </h1>
    <p style="font-size:0.95rem; color:#9aa3b5; margin:0; line-height:1.65; max-width:600px; margin-left:auto; margin-right:auto;">
        A RAG-powered intelligence layer over 250 international family offices. Ask anything — sector focus, check sizes, co-invest frequency, decision makers, recent signals.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Stats Bar (Flask style grid) ──
try:
    from retrieval import _meta as metadata
    if metadata:
        regions = {}
        fo_types = {}
        for r in metadata:
            reg = r.get("region", "Unknown")
            ft = r.get("fo_type", "Unknown")
            regions[reg] = regions.get(reg, 0) + 1
            fo_types[ft] = fo_types.get(ft, 0) + 1
        
        sfo_count = fo_types.get("SFO", 0)
        mfo_count = fo_types.get("MFO", 0)
        
        st.markdown(f"""
        <div style="display:flex; gap:0; border:1px solid #252b38; border-radius:10px; overflow:hidden; margin-bottom:3rem;">
            <div style="flex:1; padding:1rem 1.2rem; border-right:1px solid #252b38; text-align:center; background:#111318; transition:all 0.2s;">
                <div style="font-family:monospace; font-size:1.4rem; font-weight:500; color:#c9a84c; display:block;">{len(metadata)}</div>
                <div style="font-size:0.7rem; color:#5a6478; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.1rem; display:block;">Family Offices</div>
            </div>
            <div style="flex:1; padding:1rem 1.2rem; border-right:1px solid #252b38; text-align:center; background:#111318; transition:all 0.2s;">
                <div style="font-family:monospace; font-size:1.4rem; font-weight:500; color:#c9a84c; display:block;">28</div>
                <div style="font-size:0.7rem; color:#5a6478; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.1rem; display:block;">Intel Fields</div>
            </div>
            <div style="flex:1; padding:1rem 1.2rem; border-right:1px solid #252b38; text-align:center; background:#111318; transition:all 0.2s;">
                <div style="font-family:monospace; font-size:1.4rem; font-weight:500; color:#c9a84c; display:block;">{len(regions)}</div>
                <div style="font-size:0.7rem; color:#5a6478; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.1rem; display:block;">Global Regions</div>
            </div>
            <div style="flex:1; padding:1rem 1.2rem; border-right:1px solid #252b38; text-align:center; background:#111318; transition:all 0.2s;">
                <div style="font-family:monospace; font-size:1.4rem; font-weight:500; color:#c9a84c; display:block;">{sfo_count}</div>
                <div style="font-size:0.7rem; color:#5a6478; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.1rem; display:block;">SFOs</div>
            </div>
            <div style="flex:1; padding:1rem 1.2rem; text-align:center; background:#111318; transition:all 0.2s;">
                <div style="font-family:monospace; font-size:1.4rem; font-weight:500; color:#c9a84c; display:block;">{mfo_count}</div>
                <div style="font-size:0.7rem; color:#5a6478; text-transform:uppercase; letter-spacing:0.1em; margin-top:0.1rem; display:block;">MFOs</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
except:
    pass

# ── Search Section ──
st.markdown("""
<div style="margin:2rem 0;">
    <div style="font-family:monospace; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#5a6478; margin-bottom:0.8rem; opacity:0.8;">Search Family Office Intelligence</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 0.15])
with col1:
    user_query = st.text_input(
        "Query",
        placeholder="e.g., 'Which SFOs in Europe focus on AI with check sizes above $10M?'",
        label_visibility="collapsed",
        key="query_input"
    )
with col2:
    search_button = st.button("Search ›", type="primary", use_container_width=True, key="search_btn")

# ── Example Queries Label ──
st.markdown("""
<div style="font-family:monospace; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.12em; color:#5a6478; margin:1.5rem 0 0.8rem 0; opacity:0.8;">Example Queries →</div>
""", unsafe_allow_html=True)
EXAMPLES = [
    "Which family offices focus on AI or technology with check sizes above $10M?",
    "Show me all SFOs in Europe that have high co-investment frequency",
    "Find family offices with strong ESG or impact investing mandates",
    "Which family offices in Asia-Pacific have made recent direct investments?",
    "Show me family offices in the Middle East with AUM above $10 billion",
    "Who are the decision makers at the top tech-focused family offices?",
    "Find family offices focused on healthcare or biotech investments",
    "Which family offices have fund relationships with KKR or Blackstone?",
    "Show me family offices founded before 1950 with real estate focus",
    "Find family offices with very high co-invest frequency and check sizes over $5M",
]

st.markdown("**Example Queries** →")

# Store selected example in session state for tracking
if 'selected_example' not in st.session_state:
    st.session_state.selected_example = None

def set_example(example_text):
    st.session_state.query_input = example_text
    st.session_state.selected_example = example_text

cols = st.columns(2)
for i, example in enumerate(EXAMPLES):
    col_idx = i % 2
    with cols[col_idx]:
        st.button(
            example,
            key=f"ex_{i}",
            use_container_width=True,
            on_click=set_example,
            args=(example,)
        )

# If an example was selected, run the query
if st.session_state.get('selected_example') and not search_button:
    user_query = st.session_state.selected_example
    search_button = True
    st.session_state.selected_example = None  # Reset
# ── Search & Display Results ──
if search_button and user_query:
    st.markdown("""<div style="margin:2rem 0; border-top:1px solid #252b38; border-bottom:1px solid #252b38; padding:1rem 0;"></div>""", unsafe_allow_html=True)
    
    with st.spinner("🔄 Retrieving intelligence…"):
        try:
            result = query(user_query, top_k=20, max_results=10)
            
            if not result or result.get('total_results', 0) == 0:
                st.info("💡 No results found. Try a different query.")
            else:
                # Results header
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding:1rem 0; border-bottom:1px solid #252b38; margin-bottom:1.5rem;">
                    <div style="font-size:0.9rem; color:#5a6478;">
                        Showing <strong style="color:#c9a84c;">{len(result.get('records', []))}</strong> of <strong style="color:#c9a84c;">{result.get('total_results', 0)}</strong> results
                        {f"· Filters: {result.get('filter_description', '')}" if result.get('filter_description') else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # AI Answer
                if result.get('ai_answer'):
                    st.markdown(f"""
                    <div style="background:#111318; border:1px solid #2e3547; border-left:3px solid #3dd9c4; border-radius:10px; padding:1.5rem; margin:1.5rem 0;">
                        <div style="font-size:0.75rem; color:#3dd9c4; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:0.75rem;">🤖 AI Intelligence Summary</div>
                        <div style="color:#9aa3b5; line-height:1.7; white-space:pre-wrap;">
                    """, unsafe_allow_html=True)
                    st.markdown(result['ai_answer'])
                    st.markdown("</div></div>", unsafe_allow_html=True)
                
                # Record Cards
                st.markdown("<h3 style='margin-top:2rem; margin-bottom:1rem;'>📊 Retrieved Records</h3>", unsafe_allow_html=True)
                
                for idx, r in enumerate(result.get('records', []), 1):
                    fo_type = (r.get('fo_type', 'SFO') or 'SFO').upper()
                    badge_color = 'badge-mfo' if fo_type == 'MFO' else 'badge-sfo'
                    score = r.get('_score', 0)
                    score_pct = min(100, round(score * 100 / 0.4))
                    
                    # Check size
                    try:
                        check_min = float(r.get('check_min', 0)) or 0
                        check_max = float(r.get('check_max', 0)) or 0
                        if check_min and check_max:
                            check_str = f"${int(check_min)}M – ${int(check_max)}M"
                        elif check_min:
                            check_str = f"${int(check_min)}M+"
                        elif check_max:
                            check_str = f"Up to ${int(check_max)}M"
                        else:
                            check_str = "—"
                    except:
                        check_str = "—"
                    
                    st.markdown(f"""
                    <div class="record-card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">{idx}. {r.get('name', 'N/A')}</div>
                            </div>
                            <div class="card-badges">
                                <span class="badge {badge_color}">{fo_type}</span>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="card-row">
                                <span class="card-icon">📍</span>
                                <span class="card-label">Location</span>
                                <span class="card-value"><strong>{r.get('city', '')}, {r.get('country', '')}</strong> · {r.get('region', '')}</span>
                            </div>
                            <div class="card-row">
                                <span class="card-icon">👤</span>
                                <span class="card-label">DM</span>
                                <span class="card-value"><strong>{r.get('dm_name', '')}</strong> · {r.get('dm_title', '')}</span>
                            </div>
                            <div class="card-row">
                                <span class="card-icon">💰</span>
                                <span class="card-label">AUM</span>
                                <span class="card-value"><strong>{r.get('aum_range', '')}</strong> · Check: {check_str}</span>
                            </div>
                            <div class="card-row">
                                <span class="card-icon">🎯</span>
                                <span class="card-label">Strategy</span>
                                <span class="card-value">{r.get('investment_strategy', '')}</span>
                            </div>
                            <div class="card-row">
                                <span class="card-icon">🏭</span>
                                <span class="card-label">Sector</span>
                                <span class="card-value"><strong>{r.get('sector_primary', '')}</strong> · {r.get('sector_secondary', '')}</span>
                            </div>
                            <div class="card-row">
                                <span class="card-icon">📦</span>
                                <span class="card-label">Portfolio</span>
                                <span class="card-value">{r.get('portfolio_companies', '')}</span>
                            </div>
                            <div class="card-row">
                                <span class="card-icon">🤝</span>
                                <span class="card-label">Co-Invest</span>
                                <span class="card-value">{r.get('co_invest', '')} · ESG: {r.get('esg_focus', '')}</span>
                            </div>
                            <div class="card-row">
                                <span class="card-icon">🌐</span>
                                <span class="card-label">Website</span>
                                <span class="card-value"><a href="https://{r.get('website', '#').replace('https://', '').replace('http://', '')}" target="_blank">{r.get('website', '')}</a></span>
                            </div>
                            <div class="card-row">
                                <span class="card-icon">✉️</span>
                                <span class="card-label">Email</span>
                                <span class="card-value"><a href="mailto:{r.get('dm_email', '#')}">{r.get('dm_email', '')}</a></span>
                            </div>
                            <div class="score-bar-wrap">
                                <span class="score-label">Relevance</span>
                                <div class="score-bar"><div class="score-fill" style="width:{score_pct}%"></div></div>
                                <span class="score-label">{score_pct}%</span>
                            </div>
                        </div>
                        {f"<div style='padding:0.75rem 1.2rem; background:#181c23; border-top:1px solid #252b38;'><span style='display:inline-flex; align-items:center; gap:0.4rem; font-size:0.75rem; color:#5a6478;'>📡 {r.get('recent_signal', '')}</span></div>" if r.get('recent_signal') else ""}
                    </div>
                    """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ── Footer ──
st.markdown("""
<div class="footer">
    <p><strong>PolarityIQ</strong> Intelligence Platform — RAG Pipeline · TF-IDF + Cosine Similarity · Claude API Synthesis</p>
    <p>250 records · 28 fields · Q1 2026 · For research use only</p>
</div>
""", unsafe_allow_html=True)
