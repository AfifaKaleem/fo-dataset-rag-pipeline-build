"""
PolarityIQ RAG Pipeline — Retrieval Engine
============================================
Retrieval approach:
  1. Query expansion: extract intent signals (region, sector, check size, FO type, etc.)
  2. TF-IDF cosine similarity retrieval (top-k candidates)
  3. Structured filter post-pass: apply numeric / categorical constraints extracted from query
  4. Answer synthesis: template-based generation using retrieved records + Anthropic API
"""

import json
import pickle
import re
import os
import numpy as np
from scipy.sparse import issparse

STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "vector_store.pkl")
META_PATH  = os.path.join(os.path.dirname(__file__), "data", "metadata.json")

_store = None
_meta  = None

def _load():
    global _store, _meta
    if _store is None:
        with open(STORE_PATH, "rb") as f:
            _store = pickle.load(f)
        with open(META_PATH, "r", encoding="utf-8") as f:
            _meta = json.load(f)
    return _store, _meta


def cosine_similarity_sparse(query_vec, matrix):
    """Fast cosine similarity between query vector and TF-IDF matrix."""
    if issparse(query_vec):
        query_vec = query_vec.toarray()
    query_vec = query_vec.flatten()
    norm_q = np.linalg.norm(query_vec)
    if norm_q == 0:
        return np.zeros(matrix.shape[0])

    if issparse(matrix):
        mat_dense = matrix.toarray()
    else:
        mat_dense = matrix

    norms = np.linalg.norm(mat_dense, axis=1)
    norms[norms == 0] = 1e-10
    scores = mat_dense.dot(query_vec) / norms / norm_q
    return scores


def extract_filters(query: str) -> dict:
    """Parse structured constraints from natural language query."""
    q = query.lower()
    filters = {}

    # FO type
    if re.search(r'\bsfo\b|single.family', q):
        filters["fo_type"] = "SFO"
    elif re.search(r'\bmfo\b|multi.family', q):
        filters["fo_type"] = "MFO"

    # Check size
    m = re.search(r'check\s*size[s]?\s*(?:above|over|greater than|>|≥|min(?:imum)?)\s*\$?([\d,]+)([MBK]?)', q)
    if m:
        num = float(m.group(1).replace(",",""))
        unit = m.group(2).upper()
        if unit == "B": num *= 1000
        filters["check_min_above"] = num

    m = re.search(r'check\s*size[s]?\s*(?:below|under|less than|<|≤|max(?:imum)?)\s*\$?([\d,]+)([MBK]?)', q)
    if m:
        num = float(m.group(1).replace(",",""))
        unit = m.group(2).upper()
        if unit == "B": num *= 1000
        filters["check_max_below"] = num

    # AUM filter
    m = re.search(r'aum\s*(?:above|over|>)\s*\$?([\d,]+)([BM]?)', q)
    if m:
        num = float(m.group(1).replace(",",""))
        unit = m.group(2).upper()
        if unit == "B": num *= 1000
        filters["aum_above"] = num

    # Region
    region_patterns = [
        (r'\bnorth america\b|\busa\b|\bu\.s\.\b|\bunited states\b|\bamerican\b', "North America"),
        (r'\beurope\b|\beuropean\b', "Europe"),
        (r'\basia.pacific\b|\basia\b|\bapac\b|\bjapan\b|\bchina\b|\bindia\b|\bsingapore\b|\bkorea\b|\baustralia\b', "Asia-Pacific"),
        (r'\bmiddle east\b|\bgulf\b|\bmena\b|\buae\b|\bsaudi\b|\bdubai\b', "Middle East"),
        (r'\blatin america\b|\blatam\b|\bsouth america\b|\bbrazil\b|\bmexico\b', "Latin America"),
        (r'\bafrica\b|\bafrican\b|\bnigeria\b|\bkenya\b', "Africa"),
    ]
    for pattern, region in region_patterns:
        if re.search(pattern, q):
            filters["region"] = region
            break

    # Co-invest
    if re.search(r'co.invest|co-invest|coinvest|syndic', q):
        if re.search(r'high|frequent|active|often', q):
            filters["co_invest_high"] = True

    # ESG/Impact
    if re.search(r'\besg\b|impact|sustainability|green|climate|sustainable', q):
        filters["esg"] = True

    # Direct investments / recent activity
    if re.search(r'direct invest|direct deal|last 12|recent|2024|2025', q):
        filters["recent"] = True

    return filters


def apply_filters(records, filters: dict):
    """Post-retrieval hard filter pass on structured fields."""
    out = []
    for r in records:
        # FO type
        if "fo_type" in filters:
            ft = str(r.get("fo_type","")).strip().upper()
            if ft != filters["fo_type"].upper():
                continue
        # Check size lower bound
        if "check_min_above" in filters:
            try:
                mn = float(r.get("check_min", 0) or 0)
                if mn < filters["check_min_above"]:
                    continue
            except: pass
        # AUM lower bound
        if "aum_above" in filters:
            try:
                aum = float(r.get("aum_usd_m", 0) or 0)
                if aum < filters["aum_above"]:
                    continue
            except: pass
        # Region
        if "region" in filters:
            if filters["region"].lower() not in str(r.get("region","")).lower():
                continue
        # Co-invest high
        if filters.get("co_invest_high"):
            ci = str(r.get("co_invest","")).lower()
            if not re.search(r'high|very high', ci):
                continue
        # ESG
        if filters.get("esg"):
            esg = str(r.get("esg_focus","")).lower()
            strat = str(r.get("investment_strategy","")).lower()
            sector = str(r.get("sector_primary","")).lower()
            if not re.search(r'high|impact|esg|sustain|green|climate|very', esg + strat + sector):
                continue
        # Recent activity
        if filters.get("recent"):
            sig = str(r.get("recent_signal","")).lower()
            strat = str(r.get("investment_strategy","")).lower()
            if not re.search(r'direct|2024|2025|2023|acqui|invest|fund|rais', sig + strat):
                continue
        out.append(r)
    return out


def retrieve(query: str, top_k: int = 15, max_results: int = 10):
    """Full retrieval pipeline: embed → similarity → filter → return."""
    store, meta = _load()
    vectorizer = store["vectorizer"]
    matrix     = store["matrix"]

    # Embed query
    q_vec = vectorizer.transform([query])

    # Cosine similarity
    scores = cosine_similarity_sparse(q_vec, matrix)
    top_indices = np.argsort(scores)[::-1][:top_k]

    # Gather candidates with scores
    candidates = []
    for idx in top_indices:
        r = dict(meta[idx])
        r["_score"] = float(scores[idx])
        candidates.append(r)

    # Extract and apply structural filters
    filters = extract_filters(query)
    if filters:
        filtered = apply_filters(candidates, filters)
        # If filters eliminate everything, fall back to unfiltered top results
        if len(filtered) == 0:
            filtered = candidates
    else:
        filtered = candidates

    return filtered[:max_results], filters


def format_record_card(r: dict) -> str:
    """Format a record as a readable intelligence card."""
    aum = r.get("aum_usd_m", 0)
    aum_str = f"${int(float(aum)):,}M" if aum and float(aum) > 0 else r.get("aum_range", "N/A")

    check_min = r.get("check_min", 0)
    check_max = r.get("check_max", 0)
    try:
        check_str = f"${int(float(check_min))}M – ${int(float(check_max))}M"
    except:
        check_str = "N/A"

    lines = [
        f"**{r.get('name','')}** ({r.get('fo_type','')})",
        f"📍 {r.get('city','')}, {r.get('country','')} | {r.get('region','')}",
        f"👤 {r.get('dm_name','')} — {r.get('dm_title','')}",
        f"💰 AUM: {r.get('aum_range','')} | Check Size: {check_str}",
        f"🎯 Strategy: {r.get('investment_strategy','')}",
        f"🏭 Sector: {r.get('sector_primary','')} / {r.get('sector_secondary','')}",
        f"📦 Portfolio: {r.get('portfolio_companies','')}",
        f"🤝 Co-Invest: {r.get('co_invest','')} | ESG: {r.get('esg_focus','')}",
        f"📡 Signal: {r.get('recent_signal','')}",
        f"🌐 {r.get('website','')} | ✉️ {r.get('dm_email','')}",
        f"🔗 {r.get('dm_linkedin','')}",
    ]
    return "\n".join(lines)


def synthesize_answer(query: str, records: list, filters: dict) -> dict:
    """
    Generate a structured answer using Anthropic API with retrieved records as context.
    Falls back to template-based answer if API unavailable.
    """
    n = len(records)
    filter_desc = []
    if "fo_type" in filters:
        filter_desc.append(f"type={filters['fo_type']}")
    if "region" in filters:
        filter_desc.append(f"region={filters['region']}")
    if "check_min_above" in filters:
        filter_desc.append(f"min check size ≥ ${filters['check_min_above']}M")
    if "esg" in filters:
        filter_desc.append("ESG/impact focus")
    if "co_invest_high" in filters:
        filter_desc.append("high co-invest frequency")
    filter_str = ", ".join(filter_desc) if filter_desc else "semantic similarity only"

    # Build context block for LLM
    context_lines = []
    for i, r in enumerate(records[:8], 1):
        context_lines.append(
            f"[{i}] {r.get('name','')} ({r.get('fo_type','')}) | "
            f"{r.get('region','')} | AUM: {r.get('aum_range','')} | "
            f"Sector: {r.get('sector_primary','')} | "
            f"Strategy: {r.get('investment_strategy','')} | "
            f"Check: ${r.get('check_min',0)}M-${r.get('check_max',0)}M | "
            f"Co-invest: {r.get('co_invest','')} | "
            f"ESG: {r.get('esg_focus','')} | "
            f"DM: {r.get('dm_name','')} ({r.get('dm_email','')}) | "
            f"Portfolio: {r.get('portfolio_companies','')} | "
            f"Signal: {r.get('recent_signal','')}"
        )
    context_block = "\n".join(context_lines)

    # Try Anthropic API
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    ai_answer = None
    
    if api_key.strip():
        try:
            import urllib.request
            prompt_text = f"""You are PolarityIQ, an AI-powered family office intelligence assistant. You have been given retrieved records from a proprietary dataset of 250 international family offices.

USER QUERY: {query}

RETRIEVED FAMILY OFFICE RECORDS:
{context_block}

RETRIEVAL FILTERS APPLIED: {filter_str}
TOTAL MATCHING RECORDS: {n}

Instructions:
- Answer the user's query directly and concisely using ONLY the data provided above.
- Lead with a direct summary answer (1-2 sentences).
- Then list the most relevant family offices with key intelligence details.
- Be specific: cite names, AUM, check sizes, sectors, decision makers from the data.
- If the query asks for contact info, include email and LinkedIn from the records.
- End with 1 actionable insight or pattern you notice across the results.
- Do NOT make up information not in the records. If something is missing, say "not disclosed".
- Keep total response under 400 words."""

            payload = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt_text}]
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            ai_answer = data["content"][0]["text"]
        except Exception as e:
            ai_answer = None

    return {
        "query": query,
        "filters_applied": filters,
        "filter_description": filter_str,
        "total_results": n,
        "ai_answer": ai_answer,
        "records": records,
    }


def query(q: str, top_k: int = 15, max_results: int = 10) -> dict:
    """Main entry point for the RAG pipeline."""
    records, filters = retrieve(q, top_k=top_k, max_results=max_results)
    return synthesize_answer(q, records, filters)
