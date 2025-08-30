from ninja import Schema, Field
from typing import Optional, List
from datetime import datetime

class IntersectionSchema(Schema):
    id: int
    name: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime

class TrafficVolumeSchema(Schema):
    id: int
    intersection: int
    intersection_name: Optional[str]
    datetime: datetime
    direction: str
    volume: int
    is_simulated: bool
    created_at: datetime
    updated_at: datetime

class TotalTrafficVolumeSchema(Schema):
    datetime: datetime
    total_volume: int
    average_speed: float

class TotalTrafficVolumeFullSchema(Schema):
    id: int
    name: str
    latitude: float
    longitude: float
    total_volume: int
    average_speed: float
    datetime: datetime

class IncidentSchema(Schema):
    id: int
    incident_number: Optional[int]
    ticket_number: Optional[int]
    incident_type: str
    incident_detail_type: Optional[str]
    location_name: Optional[str]
    district: str
    managed_by: str
    assigned_to: str
    description: Optional[str]
    operator: Optional[str]
    status: str
    registered_at: datetime
    last_status_update: datetime
    day: Optional[int]
    month: Optional[int]
    year: Optional[int]
    intersection: Optional[int]
    intersection_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

class IntersectionMapDataSchema(Schema):
    id: int
    name: str
    latitude: float
    longitude: float
    traffic_volumes: List[dict]

class IntersectionLatestVolumeSchema(Schema):
    id: int
    name: str
    latitude: float
    longitude: float
    total_volume: Optional[int]
    average_speed: Optional[float]
    datetime: Optional[datetime]

class TrafficDataSchema(Schema):
    intersection_id: int
    datetime: datetime
    total_volume: int
    average_speed: float

class AllIntersectionsTrafficDataSchema(Schema):
    intersection_id: int
    timestamp: datetime
    total_volume: int

# Traffic Interpretation Schemas with Enhanced Validation
class TrafficVolumeDataSchema(Schema):
    """Schema for traffic volume data by direction"""
    N: int = Field(..., ge=0, description="North traffic volume")
    S: int = Field(..., ge=0, description="South traffic volume") 
    E: int = Field(..., ge=0, description="East traffic volume")
    W: int = Field(..., ge=0, description="West traffic volume")

class TrafficInterpretationRequestSchema(Schema):
    """Schema for traffic interpretation request with validation"""
    intersection_id: int = Field(..., gt=0, description="Valid intersection ID")
    datetime: str = Field(..., min_length=1, description="ISO format datetime string")
    traffic_volumes: TrafficVolumeDataSchema = Field(..., description="Traffic volumes by direction")
    total_volume: int = Field(..., ge=0, description="Total traffic volume")
    average_speed: float = Field(..., ge=0, le=200, description="Average speed in km/h")

class AnalysisSummarySchema(Schema):
    """Schema for traffic analysis summary"""
    busiest_direction: str = Field(..., description="Direction with highest traffic")
    traffic_condition: str = Field(..., description="Overall traffic condition")
    speed_assessment: str = Field(..., description="Speed condition assessment")

class TrafficInterpretationResponseSchema(Schema):
    """Schema for traffic interpretation response"""
    interpretation: str = Field(..., description="Generated interpretation text")
    congestion_level: str = Field(..., description="Congestion level (low/moderate/high/very_high)")
    peak_direction: str = Field(..., description="Direction with peak traffic")
    analysis_summary: AnalysisSummarySchema = Field(..., description="Analysis summary")

class TrafficInterpretationSchema(Schema):
    """Schema for stored traffic interpretation"""
    id: int
    intersection_id: int
    datetime: datetime
    interpretation_text: str
    congestion_level: str
    peak_direction: str
    created_at: datetime

# Report Data Schemas
class IntersectionInfoSchema(Schema):
    """Schema for intersection basic information"""
    id: int
    name: str
    latitude: float
    longitude: float

class InterpretationDataSchema(Schema):
    """Schema for interpretation data in reports"""
    interpretation: str
    congestion_level: str
    peak_direction: str

class ReportDataSchema(Schema):
    """Schema for comprehensive report data"""
    intersection: IntersectionInfoSchema
    datetime: Optional[str]
    traffic_volumes: TrafficVolumeDataSchema
    total_volume: int
    average_speed: float
    interpretation: Optional[InterpretationDataSchema]
    generated_at: str

# 즐겨찾기 및 조회수 관련 스키마들
class IntersectionStatsSchema(Schema):
    """교차로 통계 스키마"""
    view_count: int
    favorite_count: int
    last_viewed: Optional[datetime]

class ViewRecordResponseSchema(Schema):
    """조회 기록 응답 스키마"""
    success: bool
    view_count: int
    message: str

class FavoriteStatusSchema(Schema):
    """즐겨찾기 상태 스키마"""
    is_favorite: bool
    favorite_count: int

class FavoriteToggleResponseSchema(Schema):
    """즐겨찾기 토글 응답 스키마"""
    success: bool
    is_favorite: bool
    favorite_count: int
    message: str

# 관리자 통계 관련 스키마들
class TopAreaSchema(Schema):
    """TOP 지역 스키마"""
    rank: int
    area: str
    views: Optional[int] = None
    favorites: Optional[int] = None
    ai_reports: Optional[int] = None
    change: Optional[int] = None
    growth: Optional[int] = None

class AdminStatsSchema(Schema):
    """관리자 통계 스키마"""
    top_viewed_areas: List[TopAreaSchema]
    top_favorite_areas: List[TopAreaSchema]
    top_ai_report_areas: List[TopAreaSchema]
    total_views: int
    total_favorites: int
    total_ai_reports: int

class IntersectionStatsListSchema(Schema):
    """교차로 통계 목록 스키마"""
    intersection_id: int
    intersection_name: str
    view_count: int
    favorite_count: int
    ai_report_count: int
    last_viewed: Optional[datetime]
    last_ai_report: Optional[datetime]

# Error Response Schemas
class ValidationErrorSchema(Schema):
    """Schema for validation error responses"""
    error: bool = True
    message: str
    code: str = "VALIDATION_ERROR"
    details: dict = {}

class ServiceErrorSchema(Schema):
    """Schema for service error responses"""
    error: bool = True
    message: str
    code: str
    details: dict = {}

# 정책제안 관련 스키마들
class CoordinatesSchema(Schema):
    """좌표 스키마"""
    lat: float
    lng: float

class ProposalAttachmentSchema(Schema):
    """정책제안 첨부파일 스키마"""
    id: int
    file_name: str
    file_url: str
    file_size: int
    uploaded_at: datetime

class PolicyProposalSchema(Schema):
    """정책제안 상세 스키마"""
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    location: Optional[str] = None
    intersection_id: Optional[int] = None
    intersection_name: Optional[str] = None
    coordinates: Optional[CoordinatesSchema] = None
    submitted_by: int
    submitted_by_name: str
    submitted_by_email: str
    created_at: datetime
    updated_at: datetime
    admin_response: Optional[str] = None
    admin_response_date: Optional[datetime] = None
    admin_response_by: Optional[str] = None
    attachments: List[ProposalAttachmentSchema] = []
    tags: List[str] = []
    votes_count: int = 0
    views_count: int = 0

class CreateProposalRequestSchema(Schema):
    """정책제안 생성 요청 스키마"""
    title: str = Field(..., min_length=5, max_length=200, description="제목 (5-200자)")
    description: str = Field(..., min_length=20, max_length=2000, description="내용 (20-2000자)")
    category: str = Field(..., description="카테고리")
    priority: str = Field(default="medium", description="우선순위")
    location: Optional[str] = Field(None, max_length=500, description="위치 설명")
    intersection_id: Optional[int] = Field(None, description="관련 교차로 ID")
    coordinates: Optional[CoordinatesSchema] = Field(None, description="좌표")
    tags: Optional[List[str]] = Field(default=[], description="태그 목록")

class UpdateProposalRequestSchema(Schema):
    """정책제안 수정 요청 스키마 (제안자용)"""
    title: Optional[str] = Field(None, min_length=5, max_length=200, description="제목")
    description: Optional[str] = Field(None, min_length=20, max_length=2000, description="내용")
    category: Optional[str] = Field(None, description="카테고리")
    priority: Optional[str] = Field(None, description="우선순위")
    location: Optional[str] = Field(None, max_length=500, description="위치 설명")
    intersection_id: Optional[int] = Field(None, description="관련 교차로 ID")
    coordinates: Optional[CoordinatesSchema] = Field(None, description="좌표")
    tags: Optional[List[str]] = Field(None, description="태그 목록")

class UpdateProposalStatusRequestSchema(Schema):
    """정책제안 상태 업데이트 요청 스키마 (관리자용)"""
    status: str = Field(..., description="상태")
    admin_response: Optional[str] = Field(None, description="관리자 답변")

class ProposalListResponseSchema(Schema):
    """정책제안 목록 응답 스키마"""
    results: List[PolicyProposalSchema]
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None

class ProposalVoteRequestSchema(Schema):
    """정책제안 투표 요청 스키마"""
    vote_type: str = Field(..., description="투표 타입 (up/down)")

class ProposalVoteResponseSchema(Schema):
    """정책제안 투표 응답 스키마"""
    votes_count: int
    user_vote: Optional[str] = None

class ProposalStatsSchema(Schema):
    """정책제안 통계 스키마"""
    total_proposals: int
    pending_proposals: int
    completed_proposals: int
    proposals_by_category: dict
    proposals_by_status: dict
    monthly_proposals: List[dict]

class ProposalByCategorySchema(Schema):
    """카테고리별 정책제안 수 스키마"""
    category: str
    count: int

class ProposalByIntersectionSchema(Schema):
    """교차로별 정책제안 수 스키마"""
    intersection_id: int
    intersection_name: str
    count: int