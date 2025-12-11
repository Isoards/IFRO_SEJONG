@echo off
chcp 65001 > nul
setlocal EnableDelayedExpansion

echo ============================================
echo   Chatbot v10 로컬 학습 스크립트
echo   (Docker 없이 로컬 Python으로 실행)
echo ============================================
echo.

cd /d "%~dp0.."

echo [INFO] data\ 폴더의 파일 확인 중...
echo.

set FILE_COUNT=0

:: domain 폴더 확인
if exist "data\domain\" (
    echo [domain 폴더]
    for %%f in (data\domain\*.txt data\domain\*.md data\domain\*.pdf) do (
        echo   - %%~nxf
        set /a FILE_COUNT+=1
    )
)

:: user 폴더 확인
if exist "data\user\" (
    for %%f in (data\user\*.txt data\user\*.md data\user\*.pdf) do (
        if !FILE_COUNT!==0 echo [user 폴더]
        echo   - %%~nxf
        set /a FILE_COUNT+=1
    )
)

echo.
echo 총 !FILE_COUNT!개 파일 발견

if !FILE_COUNT!==0 (
    echo.
    echo [경고] 학습할 데이터 파일이 없습니다!
    echo       data\domain\ 또는 data\user\ 폴더에 .txt, .md, .pdf 파일을 추가하세요.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   가상환경 확인
echo ============================================
echo.

if exist "venv\Scripts\activate.bat" (
    echo [INFO] 가상환경 활성화 중...
    call venv\Scripts\activate.bat
    echo       ✓ 가상환경 활성화 완료
) else (
    echo [경고] 가상환경이 없습니다!
    echo       먼저 다음 명령어로 가상환경을 생성하세요:
    echo       python -m venv venv
    echo       venv\Scripts\activate
    echo       pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   로컬 학습 시작
echo ============================================
echo.

echo [INFO] 학습 스크립트 실행 중...
venv\Scripts\python.exe scripts\run_training.py

if errorlevel 1 (
    echo.
    echo [오류] 학습 중 문제가 발생했습니다.
    pause
    exit /b 1
)

echo.
pause
