# Start the FastAPI Application
$ErrorActionPreference = "Stop"

# Script root directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath

# Activate virtual environment
Write-Host "Activating virtual environment..."
$venvPath = Join-Path $rootPath "venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript

# Set environment variables from config/.env if it exists
$envPath = Join-Path $rootPath "config\.env"
if (Test-Path $envPath) {
    Write-Host "Loading environment variables..."
    Get-Content $envPath | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value)
        }
    }
}

# Start FastAPI application
Write-Host "Starting FastAPI application..."
try {
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
catch {
    Write-Error "Failed to start the API: $_"
    exit 1
}