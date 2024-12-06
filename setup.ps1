# Colors for output
$Green = [System.ConsoleColor]::Green
$Blue = [System.ConsoleColor]::Blue
$Red = [System.ConsoleColor]::Red

Write-Host "Setting up Audio Transcription App..." -ForegroundColor $Blue

try {
    # Check Python version
    $pythonVersion = (python --version 2>&1) -replace "Python "
    if ([version]$pythonVersion -lt [version]"3.8") {
        Write-Host "Python 3.8 or higher is required. Current version: $pythonVersion" -ForegroundColor $Red
        exit 1
    }

    # Check npm version
    $npmVersion = (npm --version)
    if ([version]$npmVersion -lt [version]"6.0.0") {
        Write-Host "npm 6.0.0 or higher is required. Current version: $npmVersion" -ForegroundColor $Red
        exit 1
    }

    # Check if Python is installed
    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Python 3 is not installed. Please install Python 3 first." -ForegroundColor $Red
        exit 1
    }

    # Check if Node.js is installed
    if (!(Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "Node.js is not installed. Please install Node.js first." -ForegroundColor $Red
        exit 1
    }

    # Create virtual environment
    Write-Host "Creating Python virtual environment..." -ForegroundColor $Blue
    python -m venv venv

    # Activate virtual environment
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        . .\venv\Scripts\Activate.ps1
    } else {
        Write-Host "Failed to create virtual environment." -ForegroundColor $Red
        exit 1
    }

    # Install Python dependencies
    Write-Host "Installing Python dependencies..." -ForegroundColor $Blue
    pip install -r backend\requirements.txt

    # Install Node.js dependencies
    Write-Host "Installing Node.js dependencies..." -ForegroundColor $Blue
    Set-Location frontend
    npm install
    Set-Location ..

    Write-Host "Setup completed successfully!" -ForegroundColor $Green

} catch {
    Write-Host "An error occurred during setup: $_" -ForegroundColor $Red
    exit 1
}
