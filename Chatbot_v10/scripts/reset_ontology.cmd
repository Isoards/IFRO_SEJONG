@echo off
chcp 65001 > nul
setlocal

echo ============================================
echo   Chatbot v10 온톨로지 초기화 스크립트
echo ============================================
echo.

cd /d "%~dp0.."

echo [1/3] SQLite DB 삭제 중...
if exist "ontology.db" (
    del /f /q "ontology.db"
    echo       ✓ ontology.db 삭제 완료
) else (
    echo       - ontology.db 없음 ^(스킵^)
)

echo.
echo [2/3] ChromaDB 폴더 삭제 중...
if exist "chroma_db" (
    rmdir /s /q "chroma_db"
    echo       ✓ chroma_db 삭제 완료
) else (
    echo       - chroma_db 없음 ^(스킵^)
)

echo.
echo [3/3] 학습 기록 삭제 중...
if exist "data\.ingested_files" (
    del /f /q "data\.ingested_files"
    echo       ✓ .ingested_files 삭제 완료
) else (
    echo       - .ingested_files 없음 ^(스킵^)
)

echo.
echo ============================================
echo   초기화 완료!
echo.
echo   다음 단계:
echo   1. data\ 폴더에 학습 데이터 추가
echo   2. train.cmd 실행하여 학습 시작
echo ============================================
echo.

pause
