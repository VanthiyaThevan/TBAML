# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Set environment variables from .env if it exists
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $matches[1]
            $value = $matches[2]
            Set-Item -Path "env:$name" -Value $value
        }
    }
}

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8001