# TBAML System Package

This package contains the TBAML (Trade-Based Anti-Money Laundering) system for line of business verification.

## Directory Structure
```
package_export/
├── app/                    # Main application code
├── config/                 # Configuration files
│   ├── .env.template      # Environment variables template
│   └── alembic.ini        # Database migration config
├── scripts/               # Startup and utility scripts
└── venv/                  # Python virtual environment
```

## Setup Instructions

1. Create and activate a virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Configure the environment:
```powershell
# Copy the environment template
Copy-Item config\.env.template config\.env

# Edit config\.env with your settings
notepad config\.env
```

4. Start the API:
```powershell
.\scripts\start_api.ps1
```

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Required External Services
- Ollama (for local LLM): Should be running on http://localhost:11434
- Database: Configure in .env file

## Endpoints
- `/api/v1/lob/verify` - Verify line of business
- `/health` - Health check endpoint
- `/` - Root endpoint (version info)