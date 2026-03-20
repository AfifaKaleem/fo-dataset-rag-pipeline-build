"""
Test script to verify RAG pipeline with example queries
"""
import os
import json
from retrieval import query

def test_query(q: str):
    """Test a single query and print results."""
    print(f"\n{'='*80}")
    print(f"QUERY: {q}")
    print(f"{'='*80}")
    
    result = query(q, top_k=20, max_results=10)
    
    print(f"\nFILTERS APPLIED: {result['filters_applied']}")
    print(f"FILTER DESCRIPTION: {result['filter_description']}")
    print(f"TOTAL MATCHING RECORDS: {result['total_results']}")
    
    if result.get('ai_answer'):
        print(f"\nAI ANSWER:")
        print(result['ai_answer'])
    else:
        print("\n⚠️  AI answer not available (no API key configured)")
    
    print(f"\nTOP RESULTS ({len(result['records'])} records):")
    for i, r in enumerate(result['records'], 1):
        check_min = r.get('check_min', 0)
        check_max = r.get('check_max', 0)
        try:
            check_str = f"${int(float(check_min))}M–${int(float(check_max))}M"
        except:
            check_str = "N/A"
        
        print(f"\n[{i}] {r.get('name', 'N/A')} ({r.get('fo_type', 'N/A')})")
        print(f"    📍 {r.get('city', 'N/A')}, {r.get('country', 'N/A')} | {r.get('region', 'N/A')}")
        print(f"    💰 AUM: {r.get('aum_range', 'N/A')} | Check: {check_str}")
        print(f"    🎯 {r.get('sector_primary', 'N/A')} | {r.get('investment_strategy', 'N/A')}")
        print(f"    👤 {r.get('dm_name', 'N/A')} ({r.get('dm_title', 'N/A')})")
        score = r.get('_score', 0)
        print(f"    Score: {score:.4f}")


if __name__ == "__main__":
    queries = [
        "Which family offices in the dataset focus on AI with check sizes above $10M?",
        "Show me all single-family offices that have made direct investments in the last 12 months.",
        "Find family offices with high co-investment frequency in Asia-Pacific that focus on ESG.",
        "Which family offices in North America manage between $500M and $1B in AUM and focus on tech?",
        "Multi-family offices in Europe with a secondary sector focus on healthcare.",
        "Family offices with ESG and impact focus seeking syndication opportunities.",
    ]
    
    # Test a subset
    for q in queries[:3]:
        test_query(q)
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}\n")
