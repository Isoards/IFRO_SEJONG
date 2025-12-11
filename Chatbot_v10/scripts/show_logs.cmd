@echo off
chcp 65001 > nul
setlocal

echo ============================================
echo   Chatbot v10 로그 확인
echo ============================================
echo.

cd /d "%~dp0..\.."

echo [INFO] 최근 100줄 로그 출력 (실시간 추적)
echo       종료하려면 Ctrl+C를 누르세요.
echo.

docker logs chatbot-gpu --tail=100 -f
