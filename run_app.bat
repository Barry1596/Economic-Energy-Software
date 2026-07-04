@echo off
REM ============================================================
REM  Energi Economic Software - Streamlit App Launcher
REM  Double-click file ini untuk menjalankan web app.
REM  Browser akan otomatis membuka http://localhost:8501
REM ============================================================

cd /d "%~dp0"

echo ============================================================
echo   Energi Economic Software - Web App
echo ============================================================
echo.
echo  Menjalankan Streamlit...
echo  Browser akan otomatis terbuka di http://localhost:8501
echo.
echo  [Tekan Ctrl+C di jendela ini untuk menghentikan server]
echo.

streamlit run app.py

echo.
echo Server berhenti. Tekan tombol apapun untuk menutup jendela ini.
pause >nul
