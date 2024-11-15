# Colors for output
$Green = [System.ConsoleColor]::Green
$Blue = [System.ConsoleColor]::Blue
$Red = [System.ConsoleColor]::Red

# Function to cleanup background processes on exit
function Cleanup {
    Write-Host "`nShutting down services..." -ForegroundColor $Blue
    Get-Process -Name "node", "python" | Where-Object {$_.MainWindowTitle -eq ""} | Stop-Process -Force
    exit 0
}

# Set up cleanup on Ctrl+C
$PSDefaultParameterValues['*:ErrorAction'] = 'SilentlyContinue'
[Console]::TreatControlCAsInput = $true

# Activate virtual environment
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found. Please run setup.ps1 first." -ForegroundColor $Red
    exit 1
}

# Create necessary directories
New-Item -ItemType Directory -Force -Path backend\temp, backend\output | Out-Null

# Start backend server
Write-Host "Starting backend server..." -ForegroundColor $Blue
$backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd backend && uvicorn main:app --reload" -PassThru -WindowStyle Hidden

# Wait for backend to start
Start-Sleep -Seconds 2

# Start frontend development server
Write-Host "Starting frontend server..." -ForegroundColor $Blue
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "cd frontend && npm start" -PassThru -WindowStyle Hidden

Write-Host "Both servers are running!" -ForegroundColor $Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor $Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor $Green
Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor $Blue

try {
    # Check if ports are available
    $frontendPort = 3000
    $backendPort = 8000
    
    if ((Test-NetConnection localhost -Port $frontendPort -WarningAction SilentlyContinue).TcpTestSucceeded) {
        Write-Host "Port $frontendPort is already in use. Please free up the port." -ForegroundColor $Red
        exit 1
    }
    
    if ((Test-NetConnection localhost -Port $backendPort -WarningAction SilentlyContinue).TcpTestSucceeded) {
        Write-Host "Port $backendPort is already in use. Please free up the port." -ForegroundColor $Red
        exit 1
    }

    while ($true) {
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if (($key.Modifiers -band [ConsoleModifiers]::Control) -and ($key.Key -eq 'C')) {
                Cleanup
                break
            }
        }
        Start-Sleep -Milliseconds 100
    }
}
finally {
    Cleanup
}
