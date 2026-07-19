# Work Diary Assistant

> Automatically analyze screen activities with AI and generate daily work reports. Say goodbye to overtime report writing.

## Features

- **Smart Recognition**: AI-powered vision models (GLM / Ollama) automatically identify screen activities
- **Privacy Protection**: Auto-desensitization, no recording of contacts, accounts, passwords or sensitive info
- **Local Storage**: All data stored locally in CSV files, never uploaded to cloud
- **Real-time Statistics**: 24-hour heatmap visualization, automatic focus time calculation
- **Scheduled Monitoring**: Customizable interval for automatic screenshot analysis
- **Modern UI**: Fluent Design style based on PyQt-Fluent-Widgets

## Tech Stack

| Module | Technology |
|--------|------------|
| Language | Python 3.10 |
| GUI | PyQt5 + PyQt-Fluent-Widgets |
| AI Model | GLM-4.6V-Flash / Ollama (MiniCPM-V) |
| Image Processing | OpenCV + mss + numpy |
| Data Storage | CSV |
| Packaging | PyInstaller |

## Project Structure

```
├── main.py              # Entry file (empty)
├── screenshot.py        # Screenshot recognition core module
├── store.py             # Data storage module
├── requirements.txt     # Dependencies
├── UI/
│   ├── main_fluent.py   # Fluent Design main interface
│   └── main.py          # Legacy UI
└── data/
    ├── config.txt       # Configuration file
    ├── daily_summary.csv # Daily summary
    └── records.csv      # Detailed records
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python UI/main_fluent.py
```

## Work Categories

Supports 14 automatic work type classifications:

`Development` `Communication` `Life` `Learning` `Design` `Management` `Documentation` `Entertainment` `Product` `Meeting` `Operations` `Testing` `Data Analysis` `Other`

---

## TODO

- [ ] The AI Daily/Weekly/Monthly Summary.
- [ ] The Introduct Website which will include the download servic
- [ ] 
- [ ] 
- [ ] 
