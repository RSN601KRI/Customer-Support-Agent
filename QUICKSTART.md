# 🚀 Quick Start Guide

## Atlan Customer Support AI Copilot

### 1-Minute Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenAI API key:**
   - Create `.env` file: `cp .env.example .env`
   - Add your OpenAI API key to `.env`
   - Or enter it in the app's sidebar

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

4. **Open browser:** `http://localhost:8501`

### Alternative: Use startup script
```bash
python run.py
```

### Test before running
```bash
python test_app.py
```

## 🎯 What This Application Does

### Bulk Classification Dashboard
- Load 12 sample tickets automatically
- AI classifies each ticket by:
  - **Topic Tags**: How-to, Product, Connector, API/SDK, etc.
  - **Sentiment**: Frustrated, Curious, Angry, Neutral, Urgent
  - **Priority**: P0 (High), P1 (Medium), P2 (Low)
- View detailed analytics and metrics

### Interactive AI Agent
- Submit new support queries
- Get real-time AI classification
- Receive intelligent responses:
  - **RAG-powered answers** for documentation questions
  - **Team routing** for complex technical issues

## 🔧 Key Features

✅ **Smart Classification**: AI-powered ticket categorization
✅ **RAG Integration**: Real-time knowledge base queries
✅ **Source Citations**: All answers include documentation links
✅ **Beautiful UI**: Professional Streamlit interface
✅ **Robust Error Handling**: Graceful API failure management
✅ **Content Caching**: Optimized performance
✅ **Docker Ready**: Easy containerized deployment

## 📊 Sample Queries to Try

**RAG-Powered (Gets AI Answers):**
- "How do I connect a Snowflake data source?"
- "What are the steps to set up SSO with OKTA?"
- "How can I use the Python SDK for bulk operations?"

**Team Routing (Gets Routed):**
- "My Databricks connector is not working"
- "Data lineage is not showing correctly"
- "PII detection is not working"

## 🚀 Deployment Options

### Streamlit Cloud (Recommended)
1. Push to GitHub
2. Deploy on https://share.streamlit.io/
3. Add OpenAI API key in secrets

### Docker
```bash
docker build -t atlan-copilot .
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key atlan-copilot
```

### Local Development
```bash
# Clone and setup
git clone <repo-url>
cd customer-support-copilot
pip install -r requirements.txt

# Run
streamlit run app.py
```

## 📋 Project Structure
```
customer-support-copilot/
├── app.py                 # Main Streamlit app
├── ticket_classifier.py   # AI classification logic
├── rag_pipeline.py        # RAG implementation
├── sample_tickets.json    # Sample data (12 tickets)
├── requirements.txt       # Dependencies
├── README.md              # Full documentation
├── QUICKSTART.md          # This file
├── test_app.py            # Test suite
├── run.py                 # Startup script
├── Dockerfile             # Container config
└── .env.example           # Environment template
```

## 🆘 Troubleshooting

**Issue: "OpenAI API key required"**
- Set `OPENAI_API_KEY` environment variable
- Or create `.env` file with your key
- Or enter key in app sidebar

**Issue: "Could not load sample tickets"**
- Ensure `sample_tickets.json` exists
- Check file format with `python -c "import json; json.load(open('sample_tickets.json'))"`

**Issue: Import errors**
- Run `pip install -r requirements.txt`
- Check Python version (3.8+ required)

**Issue: Web scraping fails**
- App will still work with fallback responses
- Check internet connection
- Some sites may block scraping

## 🎯 Next Steps

1. **Customize Topics**: Edit classification categories in `ticket_classifier.py`
2. **Add Knowledge Sources**: Expand URL mappings in `rag_pipeline.py`
3. **Improve UI**: Enhance Streamlit interface in `app.py`
4. **Scale Deployment**: Use cloud platforms for production
5. **Add Analytics**: Implement metrics and logging

---

**Built for the Atlan Customer Support Team Challenge** 🎯
