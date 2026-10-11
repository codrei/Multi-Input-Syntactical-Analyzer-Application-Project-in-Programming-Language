@echo off
rem SyntaxLens one-click launcher for Windows.
rem Starts the web app on this computer (no internet needed) and opens it in the browser.
title SyntaxLens
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -m syntaxlens web
    goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
    python -m syntaxlens web
    goto :end
)
echo SyntaxLens needs Python 3.10 or newer.
echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
:end
pause
