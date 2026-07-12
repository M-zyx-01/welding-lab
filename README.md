# Welding Intelligence Lab - Welding Intelligence Lab

Multi-physics welding analysis platform for research and engineering.

## Features

- **40 materials** database (carbon steel, stainless steel, nickel alloys, aluminium, titanium, copper, filler metals)
- **12 environments** (indoor, inland, coastal, underwater, deep sea, ultra-low temp, ultra-high temp, high humidity, corrosive chemical, vacuum, nuclear, space)
- **Multi-physics analysis**: thermal, mechanical, fluid dynamics, electromagnetic, environmental
- **Cross-domain inference engine**
- **Parameter sensitivity analysis**
- **Scenario comparison** with trade-off analysis
- **Batch processing** (CSV input)
- **PWA support** for mobile installation

## Quick Start

`ash
# Install dependencies
pip install fastapi uvicorn pydantic

# Run server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8716

# Open in browser
# http://127.0.0.1:8716
`

## Project Structure

`
welding-lab/
├── backend/
│   ├── main.py              # FastAPI server (16 API endpoints)
│   ├── analysis/            # Core analysis engines
│   │   ├── predictor.py     # Multi-physics prediction
│   │   ├── inference.py     # Cross-domain inference
│   │   ├── sensitivity.py   # Parameter sensitivity
│   │   ├── comparison.py    # Scenario comparison
│   │   ├── storage.py       # Scenario persistence
│   │   └── report.py        # Report generation
│   ├── data/
│   │   ├── material_db.py   # 40 materials database
│   │   └── weld_data.py     # Weld type enums
│   └── models/
│       ├── thermal.py       # Thermal model
│       ├── mechanical.py    # Mechanical model
│       ├── fluid.py         # Fluid dynamics
│       ├── electromagnetic.py # EM model
│       ├── material.py      # Material model
│       └── environmental.py # Environmental assessment
├── frontend/
│   ├── index.html           # Main page (Chinese/English)
│   ├── manifest.json        # PWA manifest
│   ├── sw.js                # Service Worker
│   ├── css/style.css        # Styles
│   ├── js/app.js            # Frontend logic
│   └── icons/               # App icons
└── build_apk.bat            # Android APK build script
`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/health | GET | Health check |
| /api/materials | GET | List all 40 materials |
| /api/environments | GET | List 12 service environments |
| /api/analyze | POST | Full multi-physics analysis |
| /api/quick | POST | Quick quality screening |
| /api/report | GET | Generate text report |
| /api/inference | POST | Cross-domain inference |
| /api/compare | POST | Multi-scenario comparison |
| /api/sensitivity | POST | Sensitivity sweep |
| /api/auto-sensitivity | POST | Auto sensitivity analysis |
| /api/batch | POST | Batch processing |
| /api/batch-csv | POST | CSV batch import |
| /api/scenarios | GET/POST/DELETE | Scenario CRUD |

## License

MIT
