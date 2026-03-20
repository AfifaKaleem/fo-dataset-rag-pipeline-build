"""
PolarityIQ RAG Pipeline — Ingestion & Vector Store Builder
=============================================================
Strategy:
  - Each row becomes ONE "document" (rich text chunk) containing all 28 fields
  - We also create field-specific mini-chunks for precision retrieval
  - Embeddings: TF-IDF with sklearn (no external model needed, fast, accurate for structured data)
  - Vector store: numpy .npz + JSON metadata (fully self-contained, no ChromaDB needed)
  - Similarity: cosine similarity via scipy
"""

import pandas as pd
import numpy as np
import json
import pickle
import os
import re

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "data", "fo_dataset.xlsx")
STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "vector_store.pkl")
META_PATH  = os.path.join(os.path.dirname(__file__), "data", "metadata.json")

# ── Column mapping ──────────────────────────────────────────────────────────
COL_MAP = {
    "Record ID":                                        "record_id",
    "FO Firm Name":                                     "name",
    "FO Firm Type":                                     "fo_type",
    "Headquarters City":                                "city",
    "Headquarters Country":                             "country",
    "Region":                                           "region",
    "Year Founded":                                     "year_founded",
    "Wealth Origin Family":                             "family",
    "Wealth Source Industry":                           "wealth_source",
    "Estimated AUM USD M":                              "aum_usd_m",
    "AUM Range Label":                                  "aum_range",
    "FO Decision Maker Names":                          "dm_name",
    "FO Decision Maker Roles":                          "dm_title",
    "DM LinkedIn URL":                                  "dm_linkedin",
    "FO Email Pattern":                                 "dm_email",
    "FO Website Address":                               "website",
    "Investment Strategy":                              "investment_strategy",
    "Primary Sector Focus (Investment Focus)":          "sector_primary",
    "Secondary Sector Focus (Investment Focus)":        "sector_secondary",
    "FO Investment Themes":                             "investment_themes",
    "Min Check Size USD M (Acceptable Check Size Range) ": "check_min",
    "Max Check Size USD M (Acceptable Check Size Range)":  "check_max",
    "Co Invest Frequency":                              "co_invest",
    "FO Portfolio Companies":                           "portfolio_companies",
    "FO Fund Relationships":                            "fund_relationships",
    "ESG Impact Focus":                                 "esg_focus",
    "Recent FO Signal Activity":                        "recent_signal",
    "Data Source Confidence":                           "confidence",
}

def clean(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def build_document(row):
    """Convert a row into a rich natural-language document for embedding."""
    r = row
    parts = [
        f"{r['name']} is a {r['fo_type']} (family office type) headquartered in {r['city']}, {r['country']} ({r['region']}).",
        f"Founded in {r['year_founded']} by the {r['family']} family, with wealth originating from {r['wealth_source']}.",
        f"Estimated AUM: {r['aum_range']} (approximately ${r['aum_usd_m']}M).",
        f"Key decision maker: {r['dm_name']}, {r['dm_title']}.",
        f"Contact: {r['dm_email']} | LinkedIn: {r['dm_linkedin']} | Website: {r['website']}.",
        f"Investment strategy: {r['investment_strategy']}.",
        f"Primary sector focus: {r['sector_primary']}. Secondary sector: {r['sector_secondary']}.",
        f"Investment themes and asset allocation: {r['investment_themes']}.",
        f"Check size range: ${r['check_min']}M to ${r['check_max']}M.",
        f"Co-investment frequency: {r['co_invest']}.",
        f"Notable portfolio companies: {r['portfolio_companies']}.",
        f"Fund relationships / LP relationships: {r['fund_relationships']}.",
        f"ESG and impact focus: {r['esg_focus']}.",
        f"Recent activity and signals: {r['recent_signal']}.",
        f"Data confidence level: {r['confidence']}.",
    ]
    return " ".join(p for p in parts if p.strip())


def load_dataset():
    df = pd.read_excel(EXCEL_PATH, sheet_name="FO_Intelligence_Dataset", header=1)
    df = df.rename(columns=COL_MAP)
    df = df.fillna("")
    # clean numeric columns
    for col in ["aum_usd_m", "check_min", "check_max"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def build_vector_store():
    from sklearn.feature_extraction.text import TfidfVectorizer

    print("Loading dataset...")
    df = load_dataset()
    print(f"  {len(df)} records loaded")

    print("Building documents...")
    docs = [build_document(row) for _, row in df.iterrows()]

    print("Fitting TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=8000,
        ngram_range=(1, 2),   # unigrams + bigrams for better phrase matching
        min_df=1,
        sublinear_tf=True,    # log-scaled TF
        strip_accents="unicode",
        analyzer="word",
    )
    tfidf_matrix = vectorizer.fit_transform(docs)
    print(f"  Matrix shape: {tfidf_matrix.shape}")

    # Store metadata as list of dicts
    metadata = df.to_dict(orient="records")

    print("Saving vector store...")
    with open(STORE_PATH, "wb") as f:
        pickle.dump({"vectorizer": vectorizer, "matrix": tfidf_matrix}, f)

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, default=str)

    print(f"  Saved to {STORE_PATH}")
    print(f"  Saved metadata to {META_PATH}")
    return vectorizer, tfidf_matrix, metadata, docs


if __name__ == "__main__":
    import shutil
    src = "/FamilyOfficeIntelligence_PolarityIQ_250Records_task1.xlsx"
    dst = EXCEL_PATH
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)
    print(f"Copied dataset to {dst}")
    build_vector_store()
    print("Ingestion complete.")
