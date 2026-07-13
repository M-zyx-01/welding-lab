@echo off
chcp 65001 >nul
title Welding Intelligence Lab - Server
echo ============================================
echo   Welding Intelligence Lab / 焊接智能分析实验室
echo ============================================
echo.
echo Starting server on http://127.0.0.1:8716
echo Keep this window open while using the app.
echo Press Ctrl+C to stop.
echo.
cd /d "E:\焊接\welding-lab-github"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8716
pause
