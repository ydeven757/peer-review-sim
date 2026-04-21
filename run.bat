@echo off
REM ============================================================
REM  Peer Review Simulator — Windows Launcher
REM  Run from the repo root (peer-review-sim folder)
REM ============================================================

cd /d "%~dp0"

REM Install dependencies if needed
pip install -r requirements.txt >nul 2>&1

REM Set PYTHONPATH so 'app' module is found
set PYTHONPATH=%CD%

REM Optional: uncomment and set your API key here (or set via env vars)
REM set ANTHROPIC_API_KEY=sk-ant-...

echo Starting Peer Review Simulator...
echo Open http://localhost:8501 in your browser
echo.

streamlit run app/main.py --server.headless true --browser.gatherUsageStats false
