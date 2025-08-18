# Valorant Parlay — Fantasy Team Builder

Build Valorant fantasy teams from live VLR.gg data. Auto-scrapes, scores players, and serves a simple web UI.

## Features
- Auto polling + optional daily refresh
- Incremental scraping (storage-friendly)
- Points & costs calculation
- Simple HTML pages in `templates/`

## Tech
Python (FastAPI), httpx, BeautifulSoup, SQLite

## Quickstart
```bash
# Create & activate a venv
# Windows:
py -m venv venv && venv\Scripts\activate
# macOS/Linux:
python3 -m venv venv && source venv/bin/activate

pip install -r requirements.txt
cp env.example .env   # Windows: copy env.example .env
uvicorn app.server:app --reload
# Open http://127.0.0.1:8000
