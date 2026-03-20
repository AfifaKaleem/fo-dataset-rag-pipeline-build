"""
Example Query Results from PolarityIQ RAG Pipeline
==================================================

This file demonstrates real queries executed against the 250-record family office dataset,
showing the retrieval pipeline in action.

Generated: 2025-03-20
"""

import sys
sys.path.insert(0, '.')

from retrieval import query
import json

def run_example_queries():
    """Run and document example queries."""
    
    queries = [
        {
            "text": "Family offices with AI focus and check sizes above $10M",
            "expected": "Should return tech/AI-focused FOs with premium check sizes"
        },
        {
            "text": "Single-family offices that have made direct investments in the last 12 months",
            "expected": "Should filter for SFOs with recent activity signals"
        },
        {
            "text": "Multi-family offices in Asia-Pacific seeking ESG and impact focus with co-investment opportunities",
            "expected": "Should return MFOs in Asia-Pacific with ESG emphasis"
        },
        {
            "text": "Family offices in North America managing $500M-$1B AUM focusing on technology",
            "expected": "Should return North American tech-focused FOs in the mid-market AUM range"
        },
        {
            "text": "Hedge fund relationships and LP syndication opportunities in Europe",
            "expected": "Should identify European FOs with fund relationships and syndication interest"
        },
        {
            "text": "Direct investments in healthcare and life sciences with decision maker contact details",
            "expected": "Should retrieve healthcare-focused FOs with contact information"
        }
    ]
    
    results = []
    
    for i, q_data in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"EXAMPLE QUERY {i}")
        print(f"{'='*80}")
        print(f"Query: {q_data['text']}")
        print(f"Expected: {q_data['expected']}")
        print(f"\nRetrieving...")
        
        try:
            result = query(q_data['text'], top_k=20, max_results=10)
            
            print(f"\n✓ Success!")
            print(f"  Filters Applied: {result['filters_applied']}")
            print(f"  Filter Description: {result['filter_description']}")
            print(f"  Total Matches: {result['total_results']}")
            print(f"  Records Returned: {len(result['records'])}")
            
            if result['records']:
                print(f"\n  Top Result:")
                r = result['records'][0]
                print(f"    Name: {r.get('name')}")
                print(f"    Type: {r.get('fo_type')}")
                print(f"    Region: {r.get('region')}")
                print(f"    AUM: {r.get('aum_range')}")
                print(f"    Primary Sector: {r.get('sector_primary')}")
                print(f"    Check Size: ${r.get('check_min')}M–${r.get('check_max')}M")
                print(f"    Decision Maker: {r.get('dm_name')} ({r.get('dm_title')})")
                print(f"    Score: {r.get('_score', 0):.4f}")
            
            if result.get('ai_answer'):
                print(f"\n  AI Answer Preview:")
                answer_preview = result['ai_answer'][:300] + "..." if len(result['ai_answer']) > 300 else result['ai_answer']
                print(f"    {answer_preview}")
            
            results.append({
                'query': q_data['text'],
                'status': 'Success',
                'matches': result['total_results'],
                'top_record': result['records'][0].get('name') if result['records'] else None
            })
            
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            results.append({
                'query': q_data['text'],
                'status': f'Error: {str(e)}',
                'matches': 0,
                'top_record': None
            })
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for i, r in enumerate(results, 1):
        status_symbol = "✓" if r['status'] == 'Success' else "✗"
        print(f"{status_symbol} Query {i}: {r['matches']} matches | Top: {r['top_record']}")
    
    return results


if __name__ == "__main__":
    results = run_example_queries()
    print("\n✓ All example queries completed!")
