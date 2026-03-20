"""
PolarityIQ RAG Pipeline — Flask API
"""
import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__, template_folder="templates", static_folder="static")

# Pre-load the vector store at startup
from retrieval import _load, query as rag_query
_load()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/query", methods=["POST"])
def api_query():
    data = request.get_json(force=True)
    q = data.get("query", "").strip()
    if not q:
        return jsonify({"error": "No query provided"}), 400

    top_k = int(data.get("top_k", 20))
    max_results = int(data.get("max_results", 10))

    result = rag_query(q, top_k=top_k, max_results=max_results)

    # Serialize records for JSON (handle numpy types)
    clean_records = []
    for r in result.get("records", []):
        cr = {}
        for k, v in r.items():
            if hasattr(v, 'item'):
                cr[k] = v.item()
            elif isinstance(v, float) and v != v:
                cr[k] = None
            else:
                cr[k] = v
        clean_records.append(cr)

    return jsonify({
        "query": result["query"],
        "filters_applied": result["filters_applied"],
        "filter_description": result["filter_description"],
        "total_results": result["total_results"],
        "ai_answer": result.get("ai_answer"),
        "records": clean_records,
    })

@app.route("/api/stats")
def api_stats():
    from retrieval import _meta
    if _meta is None:
        _load()
    from retrieval import _meta as meta
    regions = {}
    fo_types = {}
    for r in meta:
        reg = r.get("region","Unknown")
        ft = r.get("fo_type","Unknown")
        regions[reg] = regions.get(reg,0) + 1
        fo_types[ft] = fo_types.get(ft,0) + 1
    return jsonify({
        "total_records": len(meta),
        "regions": regions,
        "fo_types": fo_types,
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
