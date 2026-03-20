# Deploy to Streamlit Cloud — Step-by-Step Guide

## Prerequisites
- GitHub account with the PolarityIQ repository pushed
- Streamlit account (free at https://streamlit.io)
- Anthropic API key (optional but recommended for full demo)

## Steps

### 1. Initialize GitHub Repository

```bash
cd /path/to/polarityiq_rag

# If not already a git repo
git init
git add .
git commit -m "Initial commit: PolarityIQ RAG Pipeline Task #2"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/PolarityIQ-RAG-Pipeline.git
git push -u origin main
```

### 2. Create Streamlit Cloud Account

1. Go to https://streamlit.io
2. Click "Sign up for the cloud"
3. Connect your GitHub account
4. Grant necessary permissions

### 3. Deploy the App

1. In Streamlit Cloud dashboard, click **"New app"**
2. **Select repository**:
   - Repository: `YOUR_USERNAME/PolarityIQ-RAG-Pipeline`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
3. Click **"Deploy"**

Streamlit will:
- Clone your repo
- Build a container
- Run `pip install -r requirements.txt` (takes ~1 min)
- Start the app at `https://YOUR_USERNAME-polarityiq-rag-pipeline.streamlit.app`

### 4. (Optional) Add Anthropic API Key

For Claude-powered synthesis answers:

1. In Streamlit Cloud, go to your app's settings (⚙️)
2. Click **"Secrets"**
3. Add:
   ```
   ANTHROPIC_API_KEY = sk-ant-xxxxxxxxxxxxx
   ```
4. Save and restart app

Now the pipeline will use Claude to synthesize answers. Without the key, the app still works and shows raw retrieval results.

---

## Sharing Your Live App

Once deployed, share the live URL:
```
https://YOUR_USERNAME-polarityiq-rag-pipeline.streamlit.app
```

Users can immediately:
- Query the 250-record family office dataset
- See retrieval results with scores
- Get AI-synthesized answers (if API key is set)
- Export/filter results

## Troubleshooting

**App won't start?**
- Check Streamlit logs (click the menu → "Manage app")
- Are all dependencies in `requirements.txt`? (flask is not needed for Streamlit; remove if present)
- Does `streamlit_app.py` exist and is it valid Python?

**Data files missing?**
- Ensure `data/fo_dataset.xlsx`, `vector_store.pkl`, and `metadata.json` are tracked in git
- If they're too large, commit them; Streamlit will include them in the container

**API calls timing out?**
- Increase timeout in `retrieval.py` (currently 30 seconds)
- Check that ANTHROPIC_API_KEY is set correctly in secrets

---

**Live Demo Ready** ✅ | March 20, 2025
