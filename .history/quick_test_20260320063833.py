"""Quick test of retrieval pipeline"""
from retrieval import retrieve, extract_filters

q = "AI with check sizes above $10M"
records, filters = retrieve(q, top_k=20, max_results=5)

print(f"Query: {q}")
print(f"Filters extracted: {filters}")
print(f"Records found: {len(records)}")
for i, r in enumerate(records[:3], 1):
    print(f"\n[{i}] {r.get('name')} | {r.get('sector_primary')} | Check: ${r.get('check_min')}-${r.get('check_max')}M")
