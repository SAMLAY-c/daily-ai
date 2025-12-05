# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an RSS-Github automation system that monitors content from RSS feeds (YouTube, Bilibili, blogs), processes media content using AI transcription/analysis, and pushes structured data to Feishu (Lark) spreadsheets for intelligence tracking.

## Core Architecture

### Main Components

1. **main.py** - Entry point and orchestration logic that coordinates all modules
2. **rss_manager.py** - RSS feed parsing and duplicate detection using `history.json`
3. **media_handler.py** - Media download and audio extraction using `yt-dlp` and `ffmpeg`
4. **gemini_agent.py** - AI analysis using Google Gemini API for content extraction and classification
5. **feishu_pusher.py** - Feishu API integration for pushing structured data to spreadsheets

### Feishu Integration Module (`feishu_integration/`)

Separate module containing Feishu management utilities:
- **create_feishu_fields.py** - Creates spreadsheet fields
- **update_business_field.py** - Updates field types (star ratings)
- **delete_specific_fields.py** - Field cleanup utilities
- **clear_feishu_table.py** - Data clearing functionality

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
GOOGLE_API_KEY=your_gemini_api_key
FEISHU_APP_ID=your_feishu_app_id
FEISHU_APP_SECRET=your_feishu_app_secret
FEISHU_BITABLE_APP_TOKEN=your_table_token
FEISHU_TABLE_ID=your_table_id
```

## Common Operations

### Running the System
```bash
python main.py
```

### Managing Feishu Integration
```bash
# Create all required fields in Feishu table
python feishu_integration/create_feishu_fields.py --auto-confirm

# Update business potential field to star display
python feishu_integration/update_business_field.py

# Clear all table data
python feishu_integration/clear_feishu_table.py --auto-confirm
```

### Testing Individual Components
```bash
# Test RSS parsing
python -c "from rss_manager import RSSManager; print(RSSManager().parse_feed('your_rss_url'))"

# Test Feishu connection
python feishu_integration/test_feishu_integration.py
```

## Data Flow

1. **RSS Monitoring**: System polls RSS feeds defined in `main.py` RSS_LIST
2. **Duplicate Detection**: Uses `history.json` to track processed content IDs
3. **Media Processing**: Downloads video/audio for transcription when needed
4. **AI Analysis**: Gemini extracts structured data including title, summary, business potential
5. **Data Pushing**: FeishuPusher formats and uploads to spreadsheet with proper field mapping

## Key Data Structures

- **RSS Entry**: Standard feedparser format with title, link, published date
- **AI Analysis Output**: Structured JSON with metadata, technical specs, and insights
- **Feishu Fields**: Predefined schema matching AI output structure

## Dependencies

- `google-genai`: Gemini AI API client
- `feedparser`: RSS feed parsing
- `yt-dlp`: Media content extraction
- `requests`: HTTP client for Feishu API
- `python-dotenv`: Environment variable management
- `ffmpeg-python`: Audio processing
- `Pillow`: Image processing
- `groq`: Alternative AI model support

## Troubleshooting

- **RSS Issues**: Check feed URLs are accessible and properly formatted
- **Media Download**: Ensure `yt-dlp` and `ffmpeg` are installed and accessible
- **Feishu API**: Verify API credentials and table permissions
- **Gemini API**: Check quota limits and API key validity