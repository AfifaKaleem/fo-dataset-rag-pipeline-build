"""
PolarityIQ RAG Pipeline — Streamlit Web Interface
A live, interactive family office intelligence tool
"""
import streamlit as st
import json
import os
from retrieval import query
from datetime import datetime

# Page config
st.set_page_config(
    page_title="PolarityIQ — Family Office Intelligence",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    [data-testid="stMainBlockContainer"] {
        padding-top: 2rem;
    }
    
    .header-section {
        text-align: center;
        padding: 2rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .result-card {
        background: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .highlight {
        background: #fff3cd;
        padding: 0.1rem 0.3rem;
        border-radius: 0.2rem;
    }
    
    .query-footer {
        text-align: center;
        color: #999;
        font-size: 0.9rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-section">
    <h1>💎 PolarityIQ — Family Office Intelligence</h1>
    <p style="font-size: 1.1rem; color: #666;">
        Query 250+ family office records using natural language. 
        Powered by TF-IDF retrieval + Claude AI synthesis.
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    top_k = st.slider("Top-K Retrieval", min_value=5, max_value=50, value=20, 
                      help="Number of documents to retrieve before filtering")
    max_results = st.slider("Max Results", min_value=1, max_value=15, value=10,
                           help="Number of final results to display")
    
    st.markdown("### 📊 Example Queries")
    examples = [
        "AI focus with $10M+ check sizes",
        "Single-family offices with direct investments",
        "Asia-Pacific ESG/impact focus with co-invest",
        "European multi-family offices in healthcare",
        "$500M–$1B AUM in tech (North America)",
        "ESG focus seeking syndication partners"
    ]
    for i, ex in enumerate(examples, 1):
        st.caption(f"→ {ex}")
    
    st.markdown("### 📖 About")
    st.markdown("""
This RAG (Retrieval-Augmented Generation) pipeline:
- **Ingests** 250 family office records
- **Embeds** with TF-IDF vectors (8K features, bigrams)
- **Retrieves** via cosine similarity + structured filters
- **Synthesizes** answers with Claude API
- **Operates** fully in-browser (no server compute)

[📊 View Dataset](data/metadata.json)
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🔍 Query Your Data")
    
    # Query input
    user_query = st.text_input(
        label="Enter your question",
        placeholder="e.g., 'Family offices with AI focus and $10M+ check sizes'",
        label_visibility="collapsed"
    )
    
    # Search button
    search_button = st.button("🔎 Search", type="primary", use_container_width=True)

with col2:
    st.markdown("### 📈 Pipeline Stats")
    
    # Load metadata for stats
    try:
        with open("data/metadata.json", "r") as f:
            metadata = json.load(f)
        
        regions = {}
        fo_types = {}
        for r in metadata:
            reg = r.get("region", "Unknown")
            ft = r.get("fo_type", "Unknown")
            regions[reg] = regions.get(reg, 0) + 1
            fo_types[ft] = fo_types.get(ft, 0) + 1
        
        st.metric("Total Records", len(metadata))
        st.metric("Regions Covered", len(regions))
        st.metric("FO Types", len(fo_types))
    except:
        st.warning("Stats unavailable")

# Results section
if search_button and user_query:
    st.markdown("---")
    st.markdown(f"### 📋 Results for: **{user_query}**")
    
    with st.spinner("🔄 Searching..."):
        try:
            result = query(user_query, top_k=top_k, max_results=max_results)
            
            # Filter info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Filters Applied",
                    len(result['filters_applied']),
                    result['filter_description'][:50] + "..." if result['filter_description'] else "None"
                )
            with col2:
                st.metric("Matches Found", result['total_results'])
            with col3:
                st.metric("Displayed", len(result['records']))
            
            # AI Answer
            if result.get('ai_answer'):
                st.markdown("#### 🤖 AI Answer")
                st.markdown(result['ai_answer'])
            else:
                st.info("💡 AI synthesis is enabled when ANTHROPIC_API_KEY is configured. Showing raw results below.")
            
            # Results table
            st.markdown("#### 📊 Retrieved Records")
            
            for i, r in enumerate(result['records'], 1):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{i}. {r.get('name', 'N/A')}**")
                        st.caption(f"{r.get('fo_type', 'N/A')} | {r.get('region', 'N/A')}")
                        st.text_input("", f"📍 {r.get('city', '')}, {r.get('country', '')}", 
                                     disabled=True, label_visibility="collapsed", key=f"loc_{i}")
                    
                    with col2:
                        st.text_input("", f"AUM: {r.get('aum_range', 'N/A')}", 
                                     disabled=True, label_visibility="collapsed", key=f"aum_{i}")
                        check_min = r.get('check_min', 0)
                        check_max = r.get('check_max', 0)
                        try:
                            check_str = f"${int(float(check_min))}M–${int(float(check_max))}M"
                        except:
                            check_str = "N/A"
                        st.text_input("Check Size", check_str, 
                                     disabled=True, label_visibility="collapsed", key=f"check_{i}")
                    
                    with col3:
                        score = r.get('_score', 0)
                        st.metric("Score", f"{score:.3f}")
                    
                    # Details
                    with st.expander("📋 Full Details"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Key Details**")
                            st.markdown(f"""
- **Sector**: {r.get('sector_primary', 'N/A')} / {r.get('sector_secondary', 'N/A')}
- **Strategy**: {r.get('investment_strategy', 'N/A')}
- **Themes**: {r.get('investment_themes', 'N/A')}
- **ESG Focus**: {r.get('esg_focus', 'N/A')}
- **Co-Invest**: {r.get('co_invest', 'N/A')}
                            """)
                        
                        with col2:
                            st.markdown("**Contact & Links**")
                            st.markdown(f"""
- **Decision Maker**: {r.get('dm_name', 'N/A')}
- **Title**: {r.get('dm_title', 'N/A')}
- **Email**: {r.get('dm_email', 'N/A')}
- **Website**: {r.get('website', 'N/A')}
                            """)
                        
                        st.markdown("**Portfolio & Relationships**")
                        st.markdown(f"""
- **Portfolio**: {r.get('portfolio_companies', 'N/A')}
- **Funds**: {r.get('fund_relationships', 'N/A')}
- **Recent Signal**: {r.get('recent_signal', 'N/A')}
                        """)
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("""
<div class="query-footer">
    <p>PolarityIQ v2.0 | Retrieval-Augmented Generation Pipeline for Family Office Intelligence</p>
    <p>Built with Streamlit • TF-IDF • Claude API</p>
</div>
""", unsafe_allow_html=True)
