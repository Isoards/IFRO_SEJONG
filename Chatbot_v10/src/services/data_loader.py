"""
초기 데이터 로더 서비스
서버 시작 시 data/ 디렉토리의 파일들을 자동으로 학습하여 온톨로지를 구축합니다.

v5.3: 도메인/사용자 데이터 분리
- data/domain/ : 기본 도메인 지식 (공통, 우선 학습)
- data/user/   : 사용자 전용 데이터 (개인화, 이후 학습)
"""
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Set, Optional

from src.services.ontology_service import OntologyService
from src.services.llm_service import LLMService
from src.services.parser_service import ParserService
from src.services.extraction_service import ExtractionService
from src.services.entity_service import EntityService
from src.shared.logging import get_logger

logger = get_logger(__name__)


class DataLoader:
    """
    초기 데이터 로딩 및 학습 담당
    
    기능:
    1. data/domain/, data/user/ 디렉토리 순차 스캔
    2. .ingested_files 기록 관리 (중복 학습 방지)
    3. 텍스트/문서 파싱 및 온톨로지 학습 실행
    
    학습 순서:
    1. domain/ 폴더 (기본 도메인 지식)
    2. user/ 폴더 (사용자 전용 데이터)
    """
    
    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}
    
    def __init__(self, ontology_service: OntologyService, llm_service: LLMService):
        self.ontology_service = ontology_service
        self.llm_service = llm_service
        
        # 필요한 서비스들 초기화
        self.parser_service = ParserService()
        self.extraction_service = ExtractionService(llm_service)
        
        # EntityService는 EntityValidator가 필요함
        from src.validators.entity_validator import EntityValidator
        from src.validators.fragment_validator import FragmentValidator
        
        self.entity_validator = EntityValidator()
        self.fragment_validator = FragmentValidator(llm_service=llm_service)
        self.entity_service = EntityService(llm_service, self.entity_validator)
        
        # 데이터 경로 (v5.3: 폴더 분리)
        self.data_dir = Path("data")
        self.domain_dir = self.data_dir / "domain"
        self.user_dir = self.data_dir / "user"
        self.ingested_record_path = self.data_dir / ".ingested_files"
        
        # 로드된 파일 목록 캐시
        self.ingested_files: Set[str] = set()
        self._load_ingested_record()
        
        # 폴더 생성 (없으면)
        self._ensure_directories()

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.domain_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)

    def _load_ingested_record(self):
        """이미 학습된 파일 목록 로드"""
        if self.ingested_record_path.exists():
            try:
                with open(self.ingested_record_path, "r", encoding="utf-8") as f:
                    self.ingested_files = set(line.strip() for line in f if line.strip())
            except Exception as e:
                logger.warning("failed_to_load_ingested_record", error=str(e))

    def _save_ingested_record(self):
        """학습된 파일 목록 저장"""
        try:
            with open(self.ingested_record_path, "w", encoding="utf-8") as f:
                for filename in sorted(self.ingested_files):
                    f.write(f"{filename}\n")
        except Exception as e:
            logger.error("failed_to_save_ingested_record", error=str(e))

    def _get_files_in_dir(self, directory: Path) -> List[Path]:
        """디렉토리에서 지원되는 파일 목록 반환"""
        if not directory.exists():
            return []
        
        files = []
        for f in directory.iterdir():
            if f.is_file() and not f.name.startswith("."):
                if f.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    files.append(f)
        return files

    def _get_record_key(self, file_path: Path, category: str) -> str:
        """학습 기록용 키 생성 (category:filename 형식)"""
        return f"{category}:{file_path.name}"

    async def load_initial_data(self):
        """
        초기 데이터 로딩 메인 프로세스
        
        순서:
        1. domain/ 폴더 먼저 학습 (기본 지식)
        2. user/ 폴더 이후 학습 (사용자 데이터)
        """
        total_loaded = 0
        
        # 1. Domain 데이터 로드 (우선순위 높음)
        domain_count = await self._load_from_directory(self.domain_dir, "domain")
        total_loaded += domain_count
        
        # 2. User 데이터 로드
        user_count = await self._load_from_directory(self.user_dir, "user")
        total_loaded += user_count
        
        # 3. 레거시: data/ 루트의 파일도 처리 (하위 호환)
        legacy_files = self._get_files_in_dir(self.data_dir)
        legacy_count = 0
        for file_path in legacy_files:
            record_key = self._get_record_key(file_path, "legacy")
            if record_key not in self.ingested_files:
                try:
                    await self._ingest_file(file_path, "legacy")
                    self.ingested_files.add(record_key)
                    self._save_ingested_record()
                    legacy_count += 1
                    logger.info("file_ingested_successfully", 
                               category="legacy", filename=file_path.name)
                except Exception as e:
                    logger.error("file_ingestion_failed", 
                                category="legacy", filename=file_path.name, error=str(e))
        total_loaded += legacy_count
        
        logger.info("initial_data_load_completed", 
                   domain_count=domain_count,
                   user_count=user_count,
                   legacy_count=legacy_count,
                   total=total_loaded)

    async def _load_from_directory(self, directory: Path, category: str) -> int:
        """특정 디렉토리에서 파일 로드"""
        if not directory.exists():
            logger.info("data_dir_not_found", path=str(directory), category=category)
            return 0

        files = self._get_files_in_dir(directory)
        new_files = [
            f for f in files 
            if self._get_record_key(f, category) not in self.ingested_files
        ]
        
        if not new_files:
            logger.info("no_new_files_to_ingest", category=category)
            return 0
            
        logger.info("starting_data_load", category=category, file_count=len(new_files))
        
        loaded_count = 0
        for file_path in new_files:
            try:
                await self._ingest_file(file_path, category)
                record_key = self._get_record_key(file_path, category)
                self.ingested_files.add(record_key)
                self._save_ingested_record()  # 하나씩 성공할 때마다 저장
                loaded_count += 1
                logger.info("file_ingested_successfully", 
                           category=category, filename=file_path.name)
            except Exception as e:
                logger.error("file_ingestion_failed", 
                            category=category, filename=file_path.name, error=str(e))
        
        return loaded_count

    async def load_domain_data(self):
        """도메인 데이터만 로드 (API 호출용)"""
        return await self._load_from_directory(self.domain_dir, "domain")

    async def load_user_data(self):
        """사용자 데이터만 로드 (API 호출용)"""
        return await self._load_from_directory(self.user_dir, "user")

    async def _ingest_file(self, file_path: Path, category: str = "unknown"):
        """단일 파일 학습 프로세스"""
        logger.debug("ingesting_file", path=str(file_path), category=category)
        
        # 1. 파일 파싱
        parse_result = await self.parser_service.parse_file(str(file_path))
        if not parse_result.success:
            raise Exception(f"Parse failed: {parse_result.error}")
            
        doc = parse_result.data
        
        # 2. 정보 추출 (Extraction)
        extraction_result = await self.extraction_service.extract_from_document(doc)
        if not extraction_result.success:
            raise Exception(f"Extraction failed: {extraction_result.error}")
            
        fragments, entity_candidates = extraction_result.data
        logger.debug("extracted_info", 
                    filename=file_path.name, 
                    category=category,
                    fragments=len(fragments), 
                    candidates=len(entity_candidates))
        
        # 3. Fragment 검증 (v5.3 추가: APPROVED로 변경해야 Relation 생성됨)
        from config.constants import ValidationStatus
        validated_fragments = []
        for fragment in fragments:
            try:
                validation_result = await self.fragment_validator.validate(fragment)
                if validation_result.is_valid:
                    fragment.validation_status = ValidationStatus.APPROVED
                    fragment.validation_score = validation_result.score
                    validated_fragments.append(fragment)
                else:
                    logger.debug("fragment_validation_rejected",
                                subject=fragment.subject,
                                object=fragment.object,
                                reasons=validation_result.reasons)
            except Exception as e:
                logger.warning("fragment_validation_error", error=str(e))
                # 검증 에러 시에도 일단 포함 (관대한 정책)
                fragment.validation_status = ValidationStatus.APPROVED
                validated_fragments.append(fragment)
        
        logger.info("fragments_validated",
                   filename=file_path.name,
                   total=len(fragments),
                   approved=len(validated_fragments))
        
        # 4. 엔티티 해결 (Entity Resolution)
        entity_result = await self.entity_service.resolve_candidates(entity_candidates)
        entities = entity_result.data if entity_result.success else []
        
        # 5. 온톨로지에 엔티티 추가 및 맵핑 생성
        entity_map = {}
        for entity in entities:
            # 카테고리를 엔티티 메타데이터에 추가
            if not entity.properties:
                entity.properties = {}
            entity.properties["source_category"] = category
            
            # 영속화 옵션 켜고 추가
            await self.ontology_service.add_entity(entity, persist=True)
            entity_map[entity.canonical_name.lower()] = entity
            for alias in entity.aliases:
                entity_map[alias.lower()] = entity
                
        # 6. 관계 구축 (Relation Building) - validated_fragments 사용
        relation_result = await self.ontology_service.build_relations_from_fragments(
            validated_fragments, entity_map
        )
        
        if not relation_result.success:
            raise Exception(f"Relation build failed: {relation_result.error}")
            
        relations = relation_result.data
        logger.info("knowledge_graph_updated", 
                   filename=file_path.name,
                   category=category,
                   entities_added=len(entities), 
                   relations_built=len(relations))

    def get_ingested_summary(self) -> Dict[str, List[str]]:
        """학습된 파일 요약 반환"""
        summary = {"domain": [], "user": [], "legacy": []}
        
        for record in self.ingested_files:
            if ":" in record:
                category, filename = record.split(":", 1)
                if category in summary:
                    summary[category].append(filename)
                else:
                    summary["legacy"].append(record)
            else:
                summary["legacy"].append(record)
        
        return summary
