# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an RSS-Github automation system that monitors content from RSS feeds (YouTube, Bilibili, blogs), processes media content using AI transcription/analysis, and pushes structured data to Feishu (Lark) spreadsheets for intelligence tracking.

## Core Architecture

### Main Components

1. **main.py** - Entry point and orchestration logic that coordinates all modules
2. **rss_manager.py** - RSS feed parsing and duplicate detection using `history.json`
3. **media_handler.py** - Media download and audio extraction using `yt-dlp` and `ffmpeg`
4. **gemini_agent.py** - AI analysis using ZhipuAI GLM-Flash model (primary) with Google Gemini fallback for content extraction and classification
5. **feishu_pusher.py** - Feishu API integration for pushing structured data to spreadsheets
6. **wewe_handler.py** - WeChat article fetcher and orchestrator
7. **obsidian_pusher.py** - Optional Obsidian vault integration for local knowledge base
8. **wewe_scraper.py** - Legacy WeChat article scraper with content extraction and history tracking

### Feishu Integration Module (`feishu_integration/`)

Separate module containing Feishu management utilities:
- **create_feishu_fields.py** - Creates spreadsheet fields with 24+ predefined field types
- **update_business_field.py** - Updates field types (star ratings)
- **delete_specific_fields.py** - Field cleanup utilities
- **clear_feishu_table.py** - Data clearing functionality
- **list_feishu_fields.py** - Field inspection utilities

## Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env  # Edit .env with your API keys
```

Required environment variables:
```
ZHIPUAI_API_KEY=your_zhipuai_api_key  # Primary AI model (zhipuai GLM-Flash)
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4  # Optional: custom endpoint
ZHIPUAI_MODEL=glm-4-flash-250414  # Optional: model selection
GOOGLE_API_KEY=your_gemini_api_key  # Legacy/backup
GROQ_API_KEY=your_groq_api_key  # For Whisper transcription
FEISHU_APP_ID=your_feishu_app_id
FEISHU_APP_SECRET=your_feishu_app_secret
FEISHU_BITABLE_APP_TOKEN=your_table_token
FEISHU_TABLE_ID=your_table_id
RSS_FEEDS=comma_separated_rss_urls
WEWE_RSS_URL=wechat_rss_service_url
TEST_MODE=false  # Set to true to limit processing for testing
```

## Common Operations

### Running the System
```bash
# Full production run
python main.py

# Test mode (limits to first RSS source and 3 WeChat articles)
TEST_MODE=true python main.py
```

### Service Management
```bash
# Start as background service with logging
python manage_service.py start

# Stop background service
python manage_service.py stop

# Check service status
python manage_service.py status

# Continuous hourly monitoring
./run_hourly.sh
```

### Managing Feishu Integration
```bash
# Create all required fields in Feishu table
python feishu_integration/create_feishu_fields.py --auto-confirm

# List current fields
python feishu_integration/list_feishu_fields.py

# Update business potential field to star display
python feishu_integration/update_business_field.py

# Clear all table data
python feishu_integration/clear_feishu_table.py --auto-confirm
```

### Testing Individual Components
```bash
# Test RSS parsing
python -c "from rss_manager import RSSManager; print(RSSManager().parse_feed('your_rss_url'))"

# Test WeChat article fetching
python -c "from wewe_handler import WeWeHandler; print(WeWeHandler().fetch_article_list())"

# Test media download
python -c "from media_handler import MediaHandler; print(MediaHandler().download_media('url'))"

# Test AI analysis (uses ZhipuAI by default)
python -c "from gemini_agent import GeminiAgent; print(GeminiAgent().analyze_content('test content'))"

# Test Feishu integration
python -c "from feishu_pusher import FeishuPusher; print(FeishuPusher().test_connection())"
```

## Data Flow Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   RSS Sources   │    │ WeChat RSS   │    │  History Files  │
│  (YouTube, etc) │    │   Service    │    │ (history.json)  │
└─────────┬───────┘    └──────┬───────┘    └─────────────────┘
          │                  │                      │
          ▼                  ▼                      │
┌─────────────────┐    ┌──────────────┐            │
│  RSS Manager    │    │ WeWe Handler │◄───────────┘
└─────────┬───────┘    └──────┬───────┘
          │                  │
          ▼                  ▼
┌─────────────────┐    ┌──────────────┐
│ Content Type    │    │  Article Text │
│   Detection     │    │  Extraction   │
└─────────┬───────┘    └──────┬───────┘
          │                  │
    Video │                  │ Articles
          ▼                  ▼
┌─────────────────┐    ┌──────────────┐
│  Media Handler  │    │  Direct Text │
│ (Download +     │    │   to AI      │
│  Transcription) │    └──────┬───────┘
└─────────┬───────┘           │
          │                   │
          ▼                   ▼
┌─────────────────────────────────────┐
│      Gemini Agent (ZhipuAI)         │
│   GLM-Flash Model + JSON Output     │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────┬───────────────────┐    ┌─────────────────┐
│  Feishu Pusher  │   Obsidian Pusher │    │  Output Destinations │
│ (Field Mapping) │  (Vault Storage)  │    │  (Structured Data)    │
└─────────────────┴───────────────────┘    └─────────────────┘
```

## Key Data Structures

- **RSS Entry**: Standard feedparser format with title, link, published date
- **AI Analysis Output**: Structured JSON with metadata, technical specs, insights, and business potential ratings
- **Feishu Fields**: Comprehensive 24+ field schema including content type, transcription, tags, and ratings
- **History Tracking**: `history.json` for RSS, `wewe_history.json` for WeChat articles

## Project Structure

```
rss-github/
├── main.py                    # Main orchestration script
├── rss_manager.py             # RSS feed parsing and duplicate detection
├── wewe_handler.py            # WeChat article fetching and processing
├── wewe_scraper.py            # Legacy WeChat scraper
├── media_handler.py           # Media download and audio extraction
├── gemini_agent.py            # AI analysis using ZhipuAI GLM-Flash
├── feishu_pusher.py           # Feishu API integration
├── obsidian_pusher.py         # Optional Obsidian vault integration
├── manage_service.py          # Background service management
├── run_hourly.sh              # Hourly execution wrapper
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
├── history.json              # RSS processing history
├── wewe_history.json         # WeChat article history
├── ffmpeg                    # FFmpeg binary (80MB)
├── feishu_integration/       # Feishu management utilities
│   ├── create_feishu_fields.py
│   ├── list_feishu_fields.py
│   ├── update_business_field.py
│   └── clear_feishu_table.py
├── logs/                     # Service logs directory
├── wewe_articles/            # Downloaded WeChat articles
├── transcripts/              # Audio transcriptions
├── .github/workflows/        # GitHub Actions CI/CD
│   └── rss-monitor.yml       # Hourly automation workflow
└── com.user.rssmonitor.plist # macOS LaunchAgent configuration
```

## Deployment Options

### Local Development
- Virtual environment with Python 3.10+
- FFmpeg binary included (80MB) or system installation via `brew install ffmpeg`
- Environment variables via `.env` file

### Production Deployment
- **GitHub Actions**: Hourly cron jobs with automatic FFmpeg installation (`rss-monitor.yml`)
- **macOS LaunchAgent**: `com.user.rssmonitor.plist` for system service
- **Background Service**: `manage_service.py` for daemonized operation

### GitHub Actions Setup
Required repository secrets:
- `ZHIPUAI_API_KEY`: Primary AI model API key
- `GOOGLE_API_KEY`: Legacy Gemini API key
- `GROQ_API_KEY`: Whisper transcription API key
- `FEISHU_APP_ID`, `FEISHU_APP_SECRET`: Feishu app credentials
- `FEISHU_BITABLE_APP_TOKEN`, `FEISHU_TABLE_ID`: Feishu table identifiers
- `RSS_FEEDS`: Comma-separated RSS feed URLs
- `WEWE_RSS_URL`: WeChat RSS service endpoint

## Dependencies

### Core Libraries
- `zhipuai`: ZhipuAI GLM-Flash model client for primary AI analysis
- `google-genai`: Gemini AI API client (legacy/backup)
- `groq`: Whisper API for Chinese-focused transcription
- `feedparser`: RSS feed parsing
- `yt-dlp`: Media content extraction with robust configuration
- `requests`: HTTP client for API integrations

### Utilities
- `python-dotenv`: Environment variable management
- `beautifulsoup4`: WeChat article content extraction
- `ffmpeg-python`: Audio processing interface
- `Pillow`: Image processing

## System Features

### Media Processing
- Automatic video/audio download using `yt-dlp`
- Audio segmentation for long content processing
- Retry mechanisms and fallback strategies
- Thread-safe download queue management

### AI Analysis
- Structured JSON output enforcement
- Comprehensive content classification
- Business potential rating system
- Technical specification extraction

### Data Management
- Duplicate prevention across all content types
- Token caching for API efficiency
- Configurable test modes for safe development
- Comprehensive logging and artifact preservation

## Troubleshooting

- **RSS Issues**: Verify feed URLs are accessible and properly formatted
- **Media Download**: Ensure `yt-dlp` and `ffmpeg` are installed and accessible
- **Feishu API**: Verify API credentials and table permissions (bitable:app scope required)
- **ZhipuAI API**: Check quota limits and API key validity for GLM-Flash model
- **Gemini API**: Check quota limits and API key validity (legacy)
- **WeChat Scraping**: Ensure WeWe RSS service is accessible at configured URL
- **Service Issues**: Check logs in `logs/rss_monitor.log` for background operations