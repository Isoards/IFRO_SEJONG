@echo off
chcp 65001 > nul
setlocal

echo ============================================
echo   Chatbot v10 학습 실행 스크립트
echo ============================================
echo.

cd /d "%~dp0..\.."

echo [INFO] data\ 폴더의 파일 확인 중...
echo.
dir /b "Chatbot_v10\data\*.txt" "Chatbot_v10\data\*.md" "Chatbot_v10\data\*.pdf" 2>nul
if errorlevel 1 (
    echo.
    echo [경고] 학습할 데이터 파일이 없습니다!
    echo       Chatbot_v10\data\ 폴더에 .txt, .md, .pdf 파일을 추가하세요.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Docker 컨테이너 재시작으로 학습 시작
echo ============================================
echo.

echo [1/2] chatbot 컨테이너 중지 중...
docker-compose -f docker-compose.gpu.yml stop chatbot
echo       ✓ 중지 완료

echo.
echo [2/2] chatbot 컨테이너 시작 중...
docker-compose -f docker-compose.gpu.yml up -d chatbot
echo       ✓ 시작 완료

echo.
echo ============================================
echo   학습이 백그라운드에서 진행 중입니다.
echo.
echo   로그 확인:
echo   docker logs chatbot-gpu --tail=50 -f
echo ============================================
echo.

set /p SHOW_LOG="로그를 실시간으로 확인하시겠습니까? (y/n): "
if /i "%SHOW_LOG%"=="y" (
    docker logs chatbot-gpu --tail=50 -f
)

pause
