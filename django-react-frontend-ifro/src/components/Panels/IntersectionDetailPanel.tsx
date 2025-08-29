import React, { useRef, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { X, Star } from "lucide-react";
import { Intersection, ApiTrafficData, ReportData, TrafficData, TrafficInterpretationResponse } from "../../types/global.types";
import { Button } from "../common/Button";
import { MiniChart } from "../common/MiniChart";
import { usePDFGeneration } from "../../utils/usePDFGeneration";
import { PDFGenerationStatus } from "../PDF/PDFGenerationStatus";
import { AIEnhancedPDFButton } from "../Dashboard/AIEnhancedPDFButton";
import { PDFTemplate } from "../PDF/PDFTemplate";
import { getIntersectionReportData } from "../../api/intersections";



interface IntersectionDetailPanelProps {
  intersection: Intersection;
  favoriteIntersections: number[];
  onToggleFavorite: (intersectionId: number) => void;
  onClose: () => void;
  isFullscreen: boolean;
  trafficStat: {
    average_speed: number | null;
    total_volume: number | null;
  } | null;
  trafficChartData: ApiTrafficData[];
}

export const IntersectionDetailPanel: React.FC<IntersectionDetailPanelProps> = ({
  intersection,
  favoriteIntersections,
  onToggleFavorite,
  onClose,
  isFullscreen,
  trafficStat,
  trafficChartData,
}) => {
  const { t, i18n } = useTranslation();
  const templateRef = useRef<HTMLDivElement>(null);
  const [actualReportData, setActualReportData] = useState<ReportData | null>(null);
  const [isLoadingReportData, setIsLoadingReportData] = useState(false);

  // 컴포넌트 마운트 시 실제 데이터 가져오기
  React.useEffect(() => {
    console.log('Intersection changed to:', intersection.id, 'clearing previous data');
    setActualReportData(null); // 이전 데이터 초기화
    fetchReportData();
  }, [intersection.id]);


  const { status, generatePDF, isSupported } = usePDFGeneration({
    onSuccess: () => console.log("PDF generated successfully!"),
    onError: (error) => console.error("PDF generation failed:", error),
  });

  // 실제 리포트 데이터를 가져오는 함수
  const fetchReportData = async () => {
    console.log(`Fetching report data for intersection ${intersection.id}...`);
    setIsLoadingReportData(true);
    try {
      // 올바른 API 함수 사용 (현재 언어 전달)
      const currentLanguage = i18n.language || 'ko';
      const data = await getIntersectionReportData(intersection.id, undefined, currentLanguage);
      
      console.log('API Response:', data);
      console.log('Traffic Volumes:', data.trafficVolumes);
      
      const newReportData = {
        intersection: {
          ...intersection,
          average_speed: (data as any)?.average_speed || data?.averageSpeed || 0,
          total_traffic_volume: (data as any)?.total_volume || data?.totalVolume || 0,
        },
        datetime: data?.datetime || new Date().toISOString(),
        trafficVolumes: (data as any)?.traffic_volumes || data?.trafficVolumes || {},
        totalVolume: (data as any)?.total_volume || data?.totalVolume || 0,
        averageSpeed: (data as any)?.average_speed || data?.averageSpeed || 0,
        chartData: chartData.map(d => ({ hour: d.hour, speed: d.speed, volume: d.volume })),
        interpretation: (data as any).interpretation?.interpretation || (data as any).interpretation || undefined,
        congestionLevel: (data as any).interpretation?.congestion_level || undefined,
        peakDirection: (data as any).interpretation?.peak_direction || undefined,
      };
      
      console.log('Setting report data:', newReportData);
      setActualReportData(newReportData);
    } catch (error) {
      console.error('Failed to fetch report data:', error);
      // 실패 시 기본 데이터 사용
      setActualReportData(null);
    } finally {
      setIsLoadingReportData(false);
    }
  };

  const isFavorited = favoriteIntersections.includes(intersection.id);

  const displaySpeed = trafficStat?.average_speed ?? 0;
  const displayVolume = trafficStat?.total_volume ?? 0;

  const chartData = trafficChartData.map((d: ApiTrafficData) => ({
    hour: new Date(d.datetime).getHours() + ':00',
    volume: d.total_volume,
    speed: d.average_speed, // speed 속성 추가
  }));

  const reportData: ReportData = {
    intersection: {
      ...intersection,
      average_speed: displaySpeed,
      total_traffic_volume: displayVolume,
    },
    datetime: new Date().toISOString(), // Use current datetime as a placeholder
    trafficVolumes: { N: 0, S: 0, E: 0, W: 0 }, // Placeholder data
    totalVolume: displayVolume,
    averageSpeed: displaySpeed,
    chartData: chartData.map(d => ({ hour: d.hour, speed: d.speed, volume: d.volume })),
    interpretation: undefined,
    congestionLevel: undefined,
    peakDirection: undefined,
  };

  const handleDownloadPDF = async () => {
    if (!templateRef.current) {
      console.error("PDF template component not found.");
      return;
    }

    // 실제 리포트 데이터가 없으면 먼저 가져오기
    if (!actualReportData && !isLoadingReportData) {
      await fetchReportData();
    }

    // 데이터 로딩이 완료될 때까지 기다리기
    if (isLoadingReportData) {
      console.log("Waiting for report data to load...");
      return;
    }

    // 실제 데이터가 있으면 사용하고, 없으면 기본 데이터 사용
    const dataToUse = actualReportData || reportData;
    console.log("Using report data:", dataToUse);
    await generatePDF(dataToUse, templateRef.current);
  };

  return (
    <div className={`h-full p-8 ${isFullscreen ? 'pt-12' : 'pt-20'} relative overflow-y-auto`}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-blue-600">
          {t("traffic.intersections")} {t("traffic.analysis")}
        </h2>
        <div className="flex items-center space-x-2">
          {isSupported && (
            <>
              <AIEnhancedPDFButton 
                reportData={actualReportData || reportData}
                className="bg-blue-600/50 hover:bg-blue-600 text-white transition-all duration-300"
                buttonText="AI PDF"
                timePeriod="24h"
              />
              <Button 
                onClick={handleDownloadPDF} 
                size="sm" 
                className="bg-blue-600/50 hover:bg-blue-600 text-white transition-all duration-300" 
                disabled={status.isGenerating || isLoadingReportData}
              >
                {isLoadingReportData ? "Loading..." : "PDF"}
              </Button>
            </>
          )}
          <Button
            variant={isFavorited ? "default" : "ghost"}
            size="icon"
            onClick={() => onToggleFavorite(intersection.id)}
            className={isFavorited ? "text-yellow-400" : "text-gray-400"}
          >
            <Star size={20} fill={isFavorited ? "currentColor" : "none"} />
          </Button>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close panel">
            <X size={24} className="text-gray-500" />
          </Button>
        </div>
      </div>
      
      <div className="space-y-6">
        <div className="p-6 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">{intersection.name}</h3>
          <div className="grid grid-cols-2 gap-4 my-4">
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">{t("traffic.speed")}</p>
              <p className="text-xl font-bold text-gray-800">{`${displaySpeed.toFixed(1)} km/h`}</p>
            </div>
            <div className="p-4 bg-white rounded-lg shadow-sm">
              <p className="text-sm text-gray-500">{t("traffic.volume")}</p>
              <p className="text-xl font-bold text-gray-800">{`${displayVolume} vph`}</p>
            </div>
          </div>
          
          <div className="w-full h-40 bg-white rounded-lg flex items-center justify-center shadow-sm">
            <MiniChart
              data={chartData}
              dataKey="volume"
              color="rgba(59,130,246,0.4)"
              showAxis={true}
            />
          </div>
        </div>

        <div className="p-6 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">{t("incidents.location")}</h3>
          <div className="flex flex-row items-center space-x-6 text-gray-700 text-sm">
            <span>Lat: <span className="font-medium">{intersection.latitude.toFixed(6)}</span></span>
            <span>Lng: <span className="font-medium">{intersection.longitude.toFixed(6)}</span></span>
          </div>
        </div>
      </div>
      
      {/* PDF Template (Hidden) */}
      <div className="absolute -z-10 -left-[9999px] -top-[9999px]">
        <div ref={templateRef}>
          {actualReportData ? (
            <PDFTemplate reportData={actualReportData} />
          ) : (
            <div>Loading report data...</div>
          )}
        </div>
      </div>
    </div>
  );
};
