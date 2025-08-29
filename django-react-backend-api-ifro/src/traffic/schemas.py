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