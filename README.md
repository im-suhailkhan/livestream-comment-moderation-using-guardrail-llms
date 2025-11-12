# YouTube Comment Moderator

A Streamlit application that moderates YouTube-style comments using AI, with a YouTube-like interface.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Setup Instructions

### 1. Create and Activate Virtual Environment (if not already done)

```bash
cd "/Users/suhail/Documents/HumanAI Interaction/AI_Comment_Moderation"
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install streamlit pandas walledai
```

### 3. Run the Application

**Option 1: Simple command**
```bash
cd "/Users/suhail/Documents/HumanAI Interaction/AI_Comment_Moderation"
source venv/bin/activate
streamlit run app.py
```

**Option 2: One-liner**
```bash
cd "/Users/suhail/Documents/HumanAI Interaction/AI_Comment_Moderation" && source venv/bin/activate && streamlit run app.py
```

### 4. Access the Application

Once running, Streamlit will display:
- **Local URL:** http://localhost:8501
- **Network URL:** http://172.26.64.170:8501

Open your browser and navigate to `http://localhost:8501`

## Features

- YouTube-like dark theme UI
- Live chat sidebar
- Comment moderation using WalledAI
- Moderator panel for reviewing flagged comments
- Real-time comment posting

## Stopping the Application

Press `Ctrl+C` in the terminal where Streamlit is running.

## Troubleshooting

- **Module not found errors:** Make sure the virtual environment is activated (`source venv/bin/activate`)
- **Port already in use:** Streamlit will automatically use the next available port
- **API errors:** Check your WalledAI API key in `moderator.py`

