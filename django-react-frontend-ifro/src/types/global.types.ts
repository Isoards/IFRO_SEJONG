export type Coordinates = {
  lat: number;
  lng: number;
};

export interface Intersection {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  total_traffic_volume?: number | null;
  average_speed?: number;
  datetime?: string;
}

export type ApiTrafficData = {
  intersection_id: number;
  datetime: string;
  total_volume: number;
  average_speed: number;
};

export type TrafficData = {
  hour: string;
  speed: number;
  volume: number;
};

export type Incident = {
  id: number;
  incident_number: number;
  ticket_number: number;
  incident_type: string;
  type: string;
  incident_detail_type: string;
  location_name: string;
  district: string;
  managed_by: string;
  assigned_to: string;
  description: string;
  operator: string;
  status: string;
  registered_at: string;
  last_status_update: string;
  day: number;
  month: number;
  year: number;
  intersection: number;
  intersection_name: string;
  latitude: number;
  longitude: number;
};

// PDF Report Types
export type PDFConfig = {
  format: "A4" | "Letter";
  orientation: "portrait" | "landscape";
  margins: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
  quality: number;
};

export type TrafficVolumeData = {
  N: number;
  S: number;
  E: number;
  W: number;
};

export type ReportData = {
  intersection: Intersection;
  datetime: string;
  trafficVolumes: TrafficVolumeData;
  totalVolume: number;
  averageSpeed: number;
  interpretation?: string;
  congestionLevel?: string;
  peakDirection?: string;
  chartData?: TrafficData[];
};

export type PDFGenerationStatus = {
  isGenerating: boolean;
  progress: number;
  error: string | null;
  completed: boolean;
};

// Traffic Interpretation API Types
export type TrafficInterpretationRequest = {
  intersection_id: number;
  datetime: string;
  traffic_volumes: TrafficVolumeData;
  total_volume: number;
  average_speed: number;
};

export type CongestionLevel = "low" | "moderate" | "high" | "very_high";
export type TrafficDirection = "N" | "S" | "E" | "W";

export type AnalysisSummary = {
  busiest_direction: string;
  traffic_condition: string;
  speed_assessment: string;
};

export type TrafficInterpretationResponse = {
  interpretation: string;
  congestion_level: CongestionLevel;
  peak_direction: TrafficDirection;
  analysis_summary: AnalysisSummary;
};

// AI Traffic Analysis Types
export type AITrafficAnalysis = {
  analysis: string;
  congestion_level: CongestionLevel;
  peak_direction: string;
  recommendations: string[];
  trends: string[];
  insights: string[];
  peak_hours?: string[];
  improvement_suggestions?: string[];
  ai_generated: boolean;
  timestamp: string;
  is_sample_data?: boolean;
  error?: string;
};

export type AIAnalysisResponse = {
  intersection_id: number;
  time_period: string;
  analysis: AITrafficAnalysis;
  generated_at: string;
};

// Enhanced Report Data with AI Analysis
export type EnhancedReportData = ReportData & {
  aiAnalysis?: AITrafficAnalysis;
};

// Favorite Analysis Types
export type FavoriteAnalysis = {
  id: number;
  intersectionId: number;
  intersectionName: string;
  dateTime: string;
  createdAt: string;
  analysisData?: {
    totalVolume: number;
    averageSpeed: number;
    chartData: TrafficData[];
  };
};

// Favorite Flow Types
export type FavoriteFlow = {
  id: number;
  fromIntersectionId: number;
  toIntersectionId: number;
  fromIntersectionName: string;
  toIntersectionName: string;
  distance: number;
  travelTime: number;
  dateTime: string;
  createdAt: string;
  flowData?: {
    averageVolume: number;
    averageSpeed: number;
    trafficFlow: number;
  };
};

// 즐겨찾기 및 조회수 관련 타입들
export interface IntersectionStats {
  intersection_id: number;
  intersection_name: string;
  view_count: number;
  favorite_count: number;
  last_viewed?: string;
}

export interface ViewRecordResponse {
  success: boolean;
  view_count: number;
  message: string;
}

export interface FavoriteStatus {
  is_favorite: boolean;
  favorite_count: number;
}

export interface FavoriteToggleResponse {
  success: boolean;
  is_favorite: boolean;
  favorite_count: number;
  message: string;
}

// 관리자 통계 관련 타입들
export interface TopArea {
  rank: number;
  area: string;
  views?: number;
  favorites?: number;
  ai_reports?: number;
  change?: number;
  growth?: number;
}

export interface AdminStats {
  top_viewed_areas: TopArea[];
  top_favorite_areas: TopArea[];
  top_ai_report_areas: TopArea[];
  total_views: number;
  total_favorites: number;
  total_ai_reports: number;
}

// 정책제안/문의 관련 타입들
export type ProposalCategory =
  | "traffic_signal"
  | "road_safety"
  | "traffic_flow"
  | "infrastructure"
  | "policy"
  | "other";

export type ProposalStatus =
  | "pending"
  | "under_review"
  | "in_progress"
  | "completed"
  | "rejected";

export type ProposalPriority = "low" | "medium" | "high" | "urgent";

export interface PolicyProposal {
  id: number;
  title: string;
  description: string;
  category: ProposalCategory;
  priority: ProposalPriority;
  status: ProposalStatus;
  location?: string;
  intersection_id?: number;
  intersection_name?: string;
  coordinates?: Coordinates;
  submitted_by: number;
  submitted_by_name: string;
  submitted_by_email: string;
  created_at: string;
  updated_at: string;
  admin_response?: string;
  admin_response_date?: string;
  admin_response_by?: string;
  attachments?: ProposalAttachment[];
  tags?: string[];
  votes_count?: number;
  views_count?: number;
}

export interface ProposalAttachment {
  id: number;
  file_name: string;
  file_url: string;
  file_size: number;
  uploaded_at: string;
}

export interface CreateProposalRequest {
  title: string;
  description: string;
  category: ProposalCategory;
  priority: ProposalPriority;
  location?: string;
  intersection_id?: number;
  coordinates?: Coordinates;
  tags?: string[];
}

export interface UpdateProposalStatusRequest {
  status: ProposalStatus;
  admin_response?: string;
}

export interface ProposalListResponse {
  results: PolicyProposal[];
  count: number;
  next?: string;
  previous?: string;
}

export interface ProposalFilters {
  category?: ProposalCategory;
  status?: ProposalStatus;
  priority?: ProposalPriority;
  intersection_id?: number;
  search?: string;
  submitted_by?: number;
  date_from?: string;
  date_to?: string;
}
