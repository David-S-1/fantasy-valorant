<<<<<<< HEAD
# Valorant Fantasy Team Builder

A web application for building and managing Valorant fantasy teams using real tournament data from VLR.gg.

## Features

- **Real-time Data**: Automatically scrapes tournament data from VLR.gg
- **Team Builder**: Interactive web interface to build fantasy teams
- **Player Stats**: Tracks games played, points per game, and total points
- **Automatic Updates**: Daily updates ensure fresh tournament data
- **Role-based Selection**: Enforce team composition rules (2 Duelists, 2 Initiators, etc.)

## Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd valorant-parlay
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy the example config
   copy env.example .env
   # Edit .env and add your tournament URLs
   ```

5. **Add tournament URLs to .env**
   ```bash
   EVENT_URLS=https://www.vlr.gg/event/2501/vct-2025-americas-stage-2,https://www.vlr.gg/event/2500/vct-2025-pacific-stage-2,https://www.vlr.gg/event/2499/vct-2025-china-stage-2,https://www.vlr.gg/event/2498/vct-2025-emea-stage-2
   POLL_SECONDS=86400
   DAILY_RUN=true
   DAILY_RUN_AT=09:00
   TIMEZONE=America/New_York
   ```

6. **Run the application**
   ```bash
   uvicorn app.server:app --reload
   ```

7. **Open in browser**
   - Team Builder: http://127.0.0.1:8000/templates/team_builder.html
   - API Status: http://127.0.0.1:8000/api/status

## Configuration

### Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `EVENT_URLS` | - | Comma-separated VLR.gg tournament URLs |
| `POLL_SECONDS` | 86400 | Background poll interval (24 hours) |
| `DAILY_RUN` | true | Enable daily automatic updates |
| `DAILY_RUN_AT` | 09:00 | Time for daily updates (24h format) |
| `TIMEZONE` | America/New_York | Your local timezone |
| `JSON_DIR` | ./json | Directory for JSON data files |

### Adding New Tournaments

1. Find the tournament URL on VLR.gg (e.g., `https://www.vlr.gg/event/2501/vct-2025-americas-stage-2`)
2. Add it to `EVENT_URLS` in your `.env` file
3. Restart the server

## API Endpoints

- `GET /api/points` - Get all player points data
- `GET /api/status` - Get system status and storage info
- `GET /api/stream` - Server-sent events for real-time updates

## Storage Policy

The system uses an efficient storage policy to prevent disk space growth:

- **Default**: Files are overwritten in-place (no new files created)
- **Content Hashing**: Skips writes when data hasn't changed
- **Atomic Writes**: Prevents partial/corrupted files
- **Snapshots**: Optional daily backups (disabled by default)

## Manual Updates

If you need to update data immediately:

```bash
# Run a full refresh of all tournaments
python -c "import asyncio; from app.pipeline import daily_refresh; asyncio.run(daily_refresh())"

# Or run the full pipeline manually
python scrape_playoffs_full_pipeline.py
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Make sure you're in the virtual environment
   - Run `pip install -r requirements.txt`

2. **No data showing up**
   - Check that tournament URLs in `.env` are correct
   - Verify the server is running: `uvicorn app.server:app --reload`
   - Check API status: http://127.0.0.1:8000/api/status

3. **Stale data in browser**
   - Hard refresh the page (Ctrl+Shift+R)
   - Clear browser cache
   - Check that you're using the server URLs, not file:// URLs

4. **Scraping errors**
   - VLR.gg may have changed their HTML structure
   - Check the server logs for specific error messages
   - Try running a manual update

### Getting Help

- Check the server logs for error messages
- Verify your `.env` configuration
- Test the API endpoints directly
- Check that tournament URLs are accessible

## Development

### Project Structure

```
valorant-fantasy-team-builder/
├── app/                    # Main application code
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── pipeline.py        # Data processing pipeline
│   ├── server.py          # FastAPI web server
│   ├── storage.py         # File storage management
│   ├── vlr_event.py       # VLR.gg event scraping
│   └── vlr_match.py       # VLR.gg match scraping
├── templates/             # HTML templates
├── scripts/               # Utility scripts (optional)
├── json/                  # Generated JSON data (excluded from repo)
├── requirements.txt       # Python dependencies
├── env.example            # Environment configuration template
└── README.md             # This file
```

### Adding Features

1. **New Data Sources**: Modify `app/vlr_event.py` and `app/vlr_match.py`
2. **New API Endpoints**: Add to `app/server.py`
3. **UI Changes**: Edit files in `templates/`
4. **Storage Changes**: Modify `app/storage.py`
5. **Utility Scripts**: Add to `scripts/` directory

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
=======
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
>>>>>>> ebe46abfd06d19d512a68055237739395c8532c1
