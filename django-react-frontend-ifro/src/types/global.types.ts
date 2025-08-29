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
  format: 'A4' | 'Letter';
  orientation: 'portrait' | 'landscape';
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
