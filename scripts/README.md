# Scripts Directory

This directory contains utility scripts for the Valorant Fantasy Team Builder project. These scripts are optional and used for development, testing, and manual operations.

## Scripts Overview

### **Core Data Processing**
- **`scrape_playoffs_full_pipeline.py`** - Comprehensive tournament scraping pipeline
- **`calculate_ppg_and_costs.py`** - Calculate player PPG and costs from tournament data
- **`calc_cost.py`** - Cost calculation utilities
- **`score_calc.py`** - Scoring calculation utilities

### **Data Management**
- **`tournament_players_parse.py`** - Parse tournament player data
- **`merge_player_display_json.py`** - Merge player display JSON files
- **`player_info.py`** - Player information and metadata

### **Analysis & Utilities**
- **`lin_regress.py`** - Linear regression analysis for player performance
- **`agents_to_roles.py`** - Map Valorant agents to player roles
- **`parlay.py`** - Simple utility functions

### **Scraping Utilities**
- **`extract_playoff_urls_from_url.py`** - Extract playoff URLs from tournament pages
- **`scrape_playoff_urls_selenium.py`** - Selenium-based URL extraction
- **`scrape_playoff_matches.py`** - Scrape individual playoff matches
- **`playoff_stats_and_points.py`** - Process playoff statistics and points

## Usage

These scripts are primarily used for:
- **Development**: Testing new scraping methods
- **Manual Operations**: One-time data processing
- **Analysis**: Player performance analysis
- **Debugging**: Troubleshooting data issues

## Running Scripts

```bash
# From the project root directory
python scripts/scrape_playoffs_full_pipeline.py
python scripts/calculate_ppg_and_costs.py
```

## Note

The main application (`app/` directory) handles all automatic operations. These scripts are supplementary and not required for normal operation.
