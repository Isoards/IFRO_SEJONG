"""
문서 관리 API
계획서 2.1: Boundary Layer – 구조 보존형 Parser
"""
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel, Field

from src.services.parser_service import ParserService
from src.services.extraction_service import ExtractionService
from src.services.entity_service import EntityService
from src.services.llm_service import LLMService
from src.validators.entity_validator import EntityValidator
from src.domain.fragments import StructuredDoc, Fragment
from src.domain.entities import Entity

router = APIRouter(prefix="/documents", tags=["Documents"])


# === Request/Response Models ===

class DocumentUploadResponse(BaseModel):
    """문서 업로드 응답"""
    document_id: str
    title: Optional[str]
    block_count: int
    fragment_count: int
    entity_count: int
    message: str


class TextInputRequest(BaseModel):
    """텍스트 입력 요청"""
    content: str = Field(min_length=10, description="분석할 텍스트")
    source_name: str = Field(default="direct_input", description="출처 이름")


class DocumentResponse(BaseModel):
    """문서 정보 응답"""
    id: str
    source_path: str
    source_type: str
    title: Optional[str]
    block_count: int
    fragment_count: int
    processed: bool


class ExtractionResultResponse(BaseModel):
    """추출 결과 응답"""
    document_id: str
    fragments: List[dict]
    entities: List[dict]


# === Dependencies ===

def get_parser_service() -> ParserService:
    return ParserService()


def get_llm_service() -> LLMService:
    return LLMService()


def get_entity_validator() -> EntityValidator:
    return EntityValidator()


def get_extraction_service(
    llm: LLMService = Depends(get_llm_service)
) -> ExtractionService:
    return ExtractionService(llm)


def get_entity_service(
    llm: LLMService = Depends(get_llm_service),
    validator: EntityValidator = Depends(get_entity_validator)
) -> EntityService:
    return EntityService(llm, validator)


# === Endpoints ===

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    parser: ParserService = Depends(get_parser_service),
    extraction: ExtractionService = Depends(get_extraction_service),
    entity_service: EntityService = Depends(get_entity_service)
):
    """
    문서 업로드 및 처리
    
    1. 파일 저장
    2. 구조 파싱 (Boundary Layer)
    3. Fragment 추출 (Extraction Layer)
    4. Entity Resolution
    """
    # 임시 파일 저장
    temp_dir = Path("./temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    file_path = temp_dir / file.filename
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 1. 문서 파싱
        parse_result = await parser.parse_file(str(file_path))
        
        if not parse_result.success:
            raise HTTPException(
                status_code=400,
                detail=parse_result.error
            )
        
        doc = parse_result.data
        
        # 2. Fragment/Entity 추출
        extraction_result = await extraction.extract_from_document(doc)
        
        if not extraction_result.success:
            raise HTTPException(
                status_code=500,
                detail=extraction_result.error
            )
        
        fragments, entity_candidates = extraction_result.data
        
        # 3. Entity Resolution
        entity_result = await entity_service.resolve_candidates(entity_candidates)
        
        entities = entity_result.data if entity_result.success else []
        
        return DocumentUploadResponse(
            document_id=doc.id,
            title=doc.title,
            block_count=len(doc.blocks),
            fragment_count=len(fragments),
            entity_count=len(entities),
            message="문서 처리 완료"
        )
        
    finally:
        # 임시 파일 정리
        if file_path.exists():
            file_path.unlink()


@router.post("/text", response_model=ExtractionResultResponse)
async def process_text(
    request: TextInputRequest,
    parser: ParserService = Depends(get_parser_service),
    extraction: ExtractionService = Depends(get_extraction_service),
    entity_service: EntityService = Depends(get_entity_service)
):
    """
    텍스트 직접 처리
    
    파일 업로드 없이 텍스트 입력으로 Fragment/Entity 추출
    """
    # 1. 텍스트 파싱
    parse_result = await parser.parse_text_content(
        request.content,
        request.source_name
    )
    
    if not parse_result.success:
        raise HTTPException(status_code=400, detail=parse_result.error)
    
    doc = parse_result.data
    
    # 2. Fragment/Entity 추출
    extraction_result = await extraction.extract_from_document(doc)
    
    if not extraction_result.success:
        raise HTTPException(status_code=500, detail=extraction_result.error)
    
    fragments, entity_candidates = extraction_result.data
    
    # 3. Entity Resolution
    entity_result = await entity_service.resolve_candidates(entity_candidates)
    entities = entity_result.data if entity_result.success else []
    
    return ExtractionResultResponse(
        document_id=doc.id,
        fragments=[f.model_dump() for f in fragments],
        entities=[e.model_dump() for e in entities]
    )


@router.get("/supported-formats")
async def get_supported_formats():
    """지원하는 파일 형식 조회"""
    return {
        "formats": [
            {"extension": ".pdf", "description": "PDF 문서"},
            {"extension": ".docx", "description": "Microsoft Word 문서"},
            {"extension": ".doc", "description": "Microsoft Word 문서 (구버전)"},
            {"extension": ".html", "description": "HTML 문서"},
            {"extension": ".htm", "description": "HTML 문서"},
            {"extension": ".md", "description": "Markdown 문서"},
            {"extension": ".txt", "description": "텍스트 파일"},
        ]
    }
