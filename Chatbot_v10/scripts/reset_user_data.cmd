@echo off
chcp 65001 > nul
setlocal

echo ============================================
echo   Chatbot v10 사용자 데이터만 초기화
echo ============================================
echo.
echo   도메인 지식은 유지하고,
echo   사용자 데이터만 재학습할 수 있게 합니다.
echo.

cd /d "%~dp0.."

echo [1/2] 사용자 데이터 학습 기록 제거 중...

if exist "data\.ingested_files" (
    :: user: 로 시작하는 줄만 제거
    powershell -Command "(Get-Content 'data\.ingested_files') | Where-Object { $_ -notmatch '^user:' } | Set-Content 'data\.ingested_files'"
    echo       ✓ 사용자 학습 기록 제거 완료
) else (
    echo       - 학습 기록 없음 ^(스킵^)
)

echo.
echo [2/2] 사용자 데이터 폴더 내용:
echo ----------------------------------------
if exist "data\user" (
    dir /b "data\user\*.txt" "data\user\*.md" "data\user\*.pdf" 2>nul
    if errorlevel 1 (
        echo       ^(파일 없음^)
    )
) else (
    echo       ^(폴더 없음^)
)

echo.
echo ============================================
echo   사용자 데이터 초기화 완료!
echo.
echo   다음 단계:
echo   1. data\user\ 폴더에 새 데이터 추가
echo   2. train.cmd 실행
echo ============================================
echo.

pause
