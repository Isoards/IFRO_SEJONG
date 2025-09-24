"""
PDF 업로드 및 관리 API
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import logging
from pydantic import BaseModel

# 핫 리로드 관리자 import
try:
    from server.hot_reload import get_hot_reload_manager
except ImportError:
    get_hot_reload_manager = None

logger = logging.getLogger(__name__)

router = APIRouter()

# PDF 알림 수신 모델
class PDFNotificationRequest(BaseModel):
    filename: str
    file_path: str
    timestamp: str
    source: str

# PDF 저장 경로
PDF_STORAGE_PATH = Path("data/pdfs")
PDF_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

@router.post("/upload-pdf")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    PDF 파일을 업로드하고 data/pdfs 폴더에 저장
    """
    try:
        # 파일 확장자 검증
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
        
        # 파일 크기 검증 (100MB 제한)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(status_code=400, detail="파일 크기는 100MB를 초과할 수 없습니다.")
        
        # 파일명 정리 (특수문자 제거)
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        file_path = PDF_STORAGE_PATH / safe_filename
        
        # 중복 파일명 처리
        counter = 1
        original_path = file_path
        while file_path.exists():
            name_parts = original_path.stem, counter, original_path.suffix
            file_path = PDF_STORAGE_PATH / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            counter += 1
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"📄 PDF 파일 업로드 완료: {file_path}")
        print(f"📄 PDF 파일 업로드 완료: {file_path}")
        
        # 백그라운드에서 임베딩 처리 시작
        background_tasks.add_task(process_pdf_embedding, str(file_path))
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "PDF 파일이 성공적으로 업로드되었습니다.",
                "filename": file_path.name,
                "file_path": str(file_path),
                "file_size": file_size,
                "status": "임베딩 처리 중..."
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 업로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}")

@router.get("/pdfs")
async def list_pdfs():
    """
    업로드된 PDF 파일 목록 조회
    """
    try:
        pdf_files = []
        for pdf_file in PDF_STORAGE_PATH.glob("*.pdf"):
            pdf_files.append({
                "filename": pdf_file.name,
                "file_path": str(pdf_file),
                "file_size": pdf_file.stat().st_size,
                "created_at": pdf_file.stat().st_ctime,
                "modified_at": pdf_file.stat().st_mtime
            })
        
        # 생성일 기준으로 정렬
        pdf_files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "pdfs": pdf_files,
                "total_count": len(pdf_files)
            }
        )
        
    except Exception as e:
        logger.error(f"PDF 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/pdfs/{filename}")
async def delete_pdf(filename: str):
    """
    PDF 파일 삭제
    """
    try:
        file_path = PDF_STORAGE_PATH / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        
        file_path.unlink()
        logger.info(f"PDF 파일 삭제 완료: {file_path}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"파일 '{filename}'이 성공적으로 삭제되었습니다."
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}")

async def process_pdf_embedding(file_path: str):
    """
    PDF 임베딩 처리 (백그라운드 작업) - 증분 임베딩 사용
    """
    try:
        logger.info(f"🔄 PDF 임베딩 처리 시작: {file_path}")
        print(f"🔄 PDF 임베딩 처리 시작: {file_path}")
        
        # 증분 임베딩 스크립트 실행
        import subprocess
        import sys
        
        cmd = [
            sys.executable,
            "scripts/incremental_embedding.py",
            "--pdf_dir", "data/pdfs",
            "--corpus_file", "data/corpus_v1.jsonl",
            "--vector_store_dir", "vector_store",
            "--processed_files_log", "data/processed_files.json"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10분 타임아웃
        )
        
        if result.returncode == 0:
            logger.info(f"✅ PDF 임베딩 처리 완료: {file_path}")
            print(f"✅ PDF 임베딩 처리 완료: {file_path}")
            logger.info(f"출력: {result.stdout}")
            
            # 핫 리로드 트리거
            try:
                from server.hot_reload import force_reload_pipeline
                if force_reload_pipeline():
                    # 메시지는 콜백에서 출력되므로 여기서는 출력하지 않음
                    pass
                else:
                    logger.warning("파이프라인 핫 리로드 실패")
            except Exception as e:
                logger.error(f"핫 리로드 오류: {str(e)}")
                
        else:
            logger.error(f"❌ PDF 임베딩 처리 실패: {result.stderr}")
            print(f"❌ PDF 임베딩 처리 실패: {result.stderr}")
        
    except subprocess.TimeoutExpired:
        logger.error("⏰ PDF 임베딩 처리 시간 초과")
        print("⏰ PDF 임베딩 처리 시간 초과")
    except Exception as e:
        logger.error(f"❌ PDF 임베딩 처리 오류: {str(e)}")
        print(f"❌ PDF 임베딩 처리 오류: {str(e)}")

@router.post("/rebuild-index")
async def rebuild_index(background_tasks: BackgroundTasks):
    """
    전체 벡터 인덱스 재구축
    """
    try:
        background_tasks.add_task(rebuild_vector_index)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "벡터 인덱스 재구축이 시작되었습니다."
            }
        )
        
    except Exception as e:
        logger.error(f"인덱스 재구축 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인덱스 재구축 중 오류가 발생했습니다: {str(e)}")

@router.get("/embedding-status")
async def get_embedding_status():
    """
    임베딩 처리 상태 조회
    """
    try:
        from server.hot_reload import get_hot_reload_manager
        
        # 핫 리로드 상태
        hot_reload_manager = get_hot_reload_manager()
        hot_reload_status = hot_reload_manager.get_status() if hot_reload_manager else {}
        
        # 처리된 파일 목록
        processed_files = []
        processed_files_log = Path("data/processed_files.json")
        if processed_files_log.exists():
            try:
                with open(processed_files_log, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    processed_files = data.get("processed_files", [])
            except Exception:
                pass
        
        # 코퍼스 통계
        corpus_stats = {"total_chunks": 0, "file_size": 0}
        corpus_file = Path("data/corpus_v1.jsonl")
        if corpus_file.exists():
            try:
                chunk_count = 0
                with open(corpus_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            chunk_count += 1
                corpus_stats = {
                    "total_chunks": chunk_count,
                    "file_size": corpus_file.stat().st_size
                }
            except Exception:
                pass
        
        # 벡터 인덱스 상태
        vector_index_stats = {"exists": False, "size": 0}
        index_file = Path("vector_store/index.faiss")
        if index_file.exists():
            vector_index_stats = {
                "exists": True,
                "size": index_file.stat().st_size
            }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "hot_reload": hot_reload_status,
                "processed_files": {
                    "count": len(processed_files),
                    "files": [Path(f).name for f in processed_files[-10:]]  # 최근 10개만
                },
                "corpus": corpus_stats,
                "vector_index": vector_index_stats,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"임베딩 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상태 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/force-reload")
async def force_reload_pipeline():
    """
    파이프라인 강제 리로드
    """
    try:
        from server.hot_reload import force_reload_pipeline
        
        success = force_reload_pipeline()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": success,
                "message": "파이프라인 리로드가 완료되었습니다." if success else "파이프라인 리로드에 실패했습니다."
            }
        )
        
    except Exception as e:
        logger.error(f"강제 리로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"리로드 중 오류가 발생했습니다: {str(e)}")

async def rebuild_vector_index():
    """
    벡터 인덱스 재구축 (백그라운드 작업)
    """
    try:
        logger.info("벡터 인덱스 재구축 시작")
        
        # 코퍼스 구축
        from scripts.build_corpus_from_pdfs import main as build_corpus
        import sys
        
        original_argv = sys.argv.copy()
        sys.argv = [
            "build_corpus_from_pdfs.py",
            "--pdf_dir", "data/pdfs",
            "--out", "data/corpus_v1.jsonl",
            "--chunking", "window",
            "--chunk-size", "500",
            "--chunk-overlap", "100"
        ]
        
        try:
            build_corpus()
        finally:
            sys.argv = original_argv
        
        # 벡터 인덱스 구축
        from scripts.build_vector_index import main as build_index
        
        sys.argv = [
            "build_vector_index.py",
            "--corpus", "data/corpus_v1.jsonl",
            "--backend", "faiss",
            "--outdir", "vector_store"
        ]
        
        try:
            build_index()
        finally:
            sys.argv = original_argv
        
        logger.info("벡터 인덱스 재구축 완료")
        
    except Exception as e:
        logger.error(f"벡터 인덱스 재구축 오류: {str(e)}")

@router.post("/pdf/notify-upload")
async def receive_pdf_notification(request: PDFNotificationRequest):
    """
    백엔드에서 PDF 저장 알림을 받아 자동으로 임베딩을 실행합니다.
    """
    try:
        logger.info(f"PDF 저장 알림 수신: {request.filename}")
        
        # 파일 경로 확인
        file_path = Path(request.file_path)
        if not file_path.exists():
            logger.error(f"❌ 파일이 존재하지 않습니다: {request.file_path}")
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": f"파일이 존재하지 않습니다: {request.filename}"}
            )
        
        # 증분 임베딩 실행
        logger.info(f"자동 임베딩 처리 시작: {request.filename}")
        
        result = subprocess.run([
            "python", "scripts/incremental_embedding.py",
            "--pdf_dir", "data/pdfs"
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logger.info(f"자동 임베딩 처리 완료: {request.filename}")
            
            # 핫 리로드 실행
            hot_reload_manager = get_hot_reload_manager()
            if hot_reload_manager:
                success = hot_reload_manager.force_reload()
                if success:
                    # 메시지는 콜백에서 출력되므로 여기서는 출력하지 않음
                    pass
                else:
                    logger.warning("파이프라인 핫 리로드 실패")
            else:
                logger.warning("핫 리로드 관리자를 찾을 수 없습니다")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success", 
                    "message": f"PDF 자동 임베딩 완료: {request.filename}",
                    "embedding_output": result.stdout
                }
            )
        else:
            logger.error(f"자동 임베딩 처리 실패: {result.stderr}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error", 
                    "message": f"임베딩 처리 실패: {result.stderr}"
                }
            )
            
    except subprocess.TimeoutExpired:
        logger.error(f"임베딩 처리 시간 초과: {request.filename}")
        return JSONResponse(
            status_code=408,
            content={"status": "error", "message": "임베딩 처리 시간 초과"}
        )
    except Exception as e:
        logger.error(f"PDF 알림 처리 실패: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"알림 처리 실패: {str(e)}"}
        )
