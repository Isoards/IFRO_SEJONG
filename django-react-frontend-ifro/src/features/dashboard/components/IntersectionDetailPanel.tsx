import React, { useRef, useState, useEffect } from "react";
import { debugLog } from "../../../shared/utils/debugUtils";
import { useTranslation } from "react-i18next";
import {
  X,
  Star,
  Plus,
  ChevronLeft,
  ChevronRight,
  GripVertical,
} from "lucide-react";
import {
  Intersection,
  ApiTrafficData,
  ReportData,
  TrafficData,
  TrafficInterpretationResponse,
} from "../../../shared/types/global.types";
import { MiniChart } from "../../../shared/components/ui/MiniChart";
import { usePDFGeneration } from "../../../shared/utils/usePDFGeneration";
import { PDFGenerationStatus } from "../../pdf-reports/components/PDFGenerationStatus";
import { AIEnhancedPDFButton } from "./AIEnhancedPDFButton";
import { PDFTemplate } from "../../pdf-reports/components/PDFTemplate";
import { getIntersectionReportData } from "../../../shared/services/intersections";
import { IntersectionProposalSection } from "../../../shared/components/panels/IntersectionProposalSection";
import CreateProposalForm from "../../policy-proposals/components/CreateProposalForm";

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
  onWidthIncrease?: () => void;
  onWidthDecrease?: () => void;
  canIncreaseWidth?: boolean;
  canDecreaseWidth?: boolean;
  onWidthChange?: (widthPercentage: number) => void;
}

export const IntersectionDetailPanel: React.FC<
  IntersectionDetailPanelProps
> = ({
  intersection,
  favoriteIntersections,
  onToggleFavorite,
  onClose,
  isFullscreen,
  trafficStat,
  trafficChartData,
  onWidthIncrease,
  onWidthDecrease,
  canIncreaseWidth = true,
  canDecreaseWidth = true,
  onWidthChange,
}) => {
  const { t, i18n } = useTranslation();
  const templateRef = useRef<HTMLDivElement>(null);
  const [actualReportData, setActualReportData] = useState<ReportData | null>(
    null
  );
  const [isLoadingReportData, setIsLoadingReportData] = useState(false);
  const [showCreateProposal, setShowCreateProposal] = useState(false);
  const [proposalRefreshFunction, setProposalRefreshFunction] = useState<
    (() => void) | null
  >(null);

  // 드래그 리사이저 상태
  const [isDragging, setIsDragging] = useState(false);
  const dragStartX = useRef(0);
  const startWidth = useRef(0);

  // 드래그 시작
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!onWidthChange) return;
    setIsDragging(true);
    dragStartX.current = e.clientX;
    startWidth.current = window.innerWidth * 0.35; // 현재 패널 너비 (35% 기본값)
    e.preventDefault();
  };

  // 드래그 중
  const handleMouseMove = React.useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !onWidthChange) return;

      const deltaX = dragStartX.current - e.clientX; // 왼쪽으로 드래그하면 양수
      const newWidth = startWidth.current + deltaX;
      const widthPercentage = Math.max(
        20,
        Math.min(60, (newWidth / window.innerWidth) * 100)
      );

      onWidthChange(widthPercentage);
    },
    [isDragging, onWidthChange]
  );

  // 드래그 종료
  const handleMouseUp = React.useCallback(() => {
    setIsDragging(false);
  }, []);

  // 드래그 이벤트 리스너 등록/해제
  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "ew-resize";
      document.body.style.userSelect = "none";
    } else {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // 컴포넌트 마운트 시 실제 데이터 가져오기
  React.useEffect(() => {
    debugLog(
      "Intersection changed to:",
      intersection.id,
      "clearing previous data"
    );
    setActualReportData(null); // 이전 데이터 초기화
    fetchReportData();
  }, [intersection.id]);

  const { status, generatePDF, isSupported } = usePDFGeneration({
    onSuccess: () => debugLog("PDF generated successfully!"),
    onError: (error) => console.error("PDF generation failed:", error),
  });

  // 실제 리포트 데이터를 가져오는 함수
  const fetchReportData = async () => {
    debugLog(`Fetching report data for intersection ${intersection.id}...`);
    setIsLoadingReportData(true);
    try {
      // 올바른 API 함수 사용 (현재 언어 전달)
      const currentLanguage = i18n.language || "ko";
      const data = await getIntersectionReportData(
        intersection.id,
        undefined,
        currentLanguage
      );

      debugLog("API Response:", data);
      debugLog("Traffic Volumes:", data.trafficVolumes);

      const newReportData = {
        intersection: {
          ...intersection,
          average_speed:
            (data as any)?.average_speed || data?.averageSpeed || 0,
          total_traffic_volume:
            (data as any)?.total_volume || data?.totalVolume || 0,
        },
        datetime: data?.datetime || new Date().toISOString(),
        trafficVolumes:
          (data as any)?.traffic_volumes || data?.trafficVolumes || {},
        totalVolume: (data as any)?.total_volume || data?.totalVolume || 0,
        averageSpeed: (data as any)?.average_speed || data?.averageSpeed || 0,
        chartData: chartData.map((d) => ({
          hour: d.hour,
          speed: d.speed,
          volume: d.volume,
        })),
        interpretation:
          (data as any).interpretation?.interpretation ||
          (data as any).interpretation ||
          undefined,
        congestionLevel:
          (data as any).interpretation?.congestion_level || undefined,
        peakDirection:
          (data as any).interpretation?.peak_direction || undefined,
      };

      debugLog("Setting report data:", newReportData);
      setActualReportData(newReportData);
    } catch (error) {
      console.error("Failed to fetch report data:", error);
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
    hour: new Date(d.datetime).getHours() + ":00",
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
    chartData: chartData.map((d) => ({
      hour: d.hour,
      speed: d.speed,
      volume: d.volume,
    })),
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
      debugLog("Waiting for report data to load...");
      return;
    }

    // 실제 데이터가 있으면 사용하고, 없으면 기본 데이터 사용
    const dataToUse = actualReportData || reportData;
    debugLog("Using report data:", dataToUse);
    await generatePDF(dataToUse, templateRef.current);
  };

  const handleCreateProposal = () => {
    setShowCreateProposal(true);
  };

  const handleCloseCreateProposal = () => {
    setShowCreateProposal(false);
  };

  const handleProposalSuccess = () => {
    setShowCreateProposal(false);
    // 정책제안 목록 새로고침
    if (proposalRefreshFunction) {
      try {
        (proposalRefreshFunction as () => void)();
      } catch (error) {
        console.error("정책제안 새로고침 중 오류 발생:", error);
      }
    } else {
      console.warn("정책제안 새로고침 함수가 아직 설정되지 않았습니다.");
      // 잠시 후 다시 시도
      setTimeout(() => {
        if (proposalRefreshFunction) {
          try {
            (proposalRefreshFunction as () => void)();
          } catch (error) {
            console.error("정책제안 새로고침 중 오류 발생:", error);
          }
        }
      }, 100);
    }
  };

  return (
    <div className="h-full w-full mx-auto bg-white relative overflow-y-auto flex">
      {/* 드래그 리사이저 */}
      {onWidthChange && (
        <div
          className="absolute left-0 top-0 w-1 h-full bg-gray-300 hover:bg-blue-500 cursor-ew-resize flex items-center justify-center transition-colors z-50"
          onMouseDown={handleMouseDown}
          style={{
            background: isDragging ? "#3b82f6" : undefined,
          }}
        >
          <div className="w-4 h-8 bg-gray-400 hover:bg-blue-500 rounded-r flex items-center justify-center">
            <GripVertical size={12} className="text-white" />
          </div>
        </div>
      )}

      <div className="flex-1 p-6 pt-4 overflow-y-auto">
        {/* 드래그 오버레이 */}
        {isDragging && (
          <div className="fixed inset-0 z-40" style={{ cursor: "ew-resize" }} />
        )}

        {/* 헤더 영역 */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold text-blue-600 mb-1 truncate">
              {t("traffic.intersections")} {t("traffic.analysis")}
            </h2>
            <p className="text-xs text-gray-500">
              교차로 실시간 교통 상황 및 분석 데이터
            </p>
          </div>

          {/* 액션 버튼 그룹 */}
          <div className="flex items-center gap-2 ml-4 flex-shrink-0">
            {/* 정책제안 버튼 */}
            <button
              onClick={handleCreateProposal}
              className="flex items-center gap-2 px-3 py-2 rounded-lg border border-green-400 text-green-600 hover:text-green-700 hover:bg-green-50 hover:border-green-500 transition-all duration-200"
              title={t("policy.createProposal") || "정책제안 작성"}
            >
              <Plus size={16} />
              <span className="text-sm font-medium">정책제안</span>
            </button>

            {/* PDF 버튼들 */}
            {isSupported && (
              <div className="flex items-center gap-1">
                <AIEnhancedPDFButton
                  reportData={actualReportData || reportData}
                  className="flex items-center justify-center h-8 rounded-lg text-purple-600 hover:text-purple-700 hover:bg-purple-50 transition-all duration-200 text-xs font-medium bg-transparent shadow-none min-w-0 py-0 space-x-0 border border-purple-400 hover:border-purple-500"
                  buttonText="AI PDF"
                  timePeriod="24h"
                />
                <button
                  onClick={handleDownloadPDF}
                  className="flex items-center justify-center w-8 h-8 rounded-lg border border-blue-400 text-blue-600 hover:text-blue-700 hover:bg-blue-50 hover:border-blue-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-medium"
                  disabled={status.isGenerating || isLoadingReportData}
                  title="PDF 다운로드"
                >
                  {isLoadingReportData ? "..." : "PDF"}
                </button>
              </div>
            )}

            {/* 즐겨찾기 버튼 */}
            <button
              onClick={() => onToggleFavorite(intersection.id)}
              className={`flex items-center justify-center w-8 h-8 rounded-lg border transition-all duration-200 ${
                isFavorited
                  ? "text-yellow-500 bg-yellow-50 hover:bg-yellow-100 border-yellow-400 hover:border-yellow-500"
                  : "text-yellow-400 hover:text-yellow-500 hover:bg-yellow-50 border-yellow-300 hover:border-yellow-400"
              }`}
              title={
                isFavorited
                  ? t("favorites.remove") || "즐겨찾기 해제"
                  : t("favorites.add") || "즐겨찾기 추가"
              }
            >
              <Star size={16} fill={isFavorited ? "currentColor" : "none"} />
            </button>

            {/* 닫기 버튼 */}
            <button
              onClick={onClose}
              aria-label="Close panel"
              className="flex items-center justify-center w-8 h-8 rounded-lg border border-red-400 text-red-500 hover:text-red-700 hover:bg-red-50 hover:border-red-500 transition-all duration-200"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="space-y-6">
          {/* 교차로 정보 카드 */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-4">
            <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              {intersection.name}
            </h3>

            {/* 통계 그리드 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              <div className="bg-white rounded-lg p-3 border border-blue-100 shadow-sm">
                <div className="text-center">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {t("traffic.speed")}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {displaySpeed.toFixed(1)}
                  </p>
                  <p className="text-xs text-gray-500">km/h</p>
                </div>
              </div>

              <div className="bg-white rounded-lg p-3 border border-blue-100 shadow-sm">
                <div className="text-center">
                  <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    {t("traffic.volume")}
                  </p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {displayVolume}
                  </p>
                  <p className="text-xs text-gray-500">vph</p>
                </div>
              </div>
            </div>

            {/* 차트 영역 */}
            <div className="bg-white rounded-lg p-3 border border-blue-100 shadow-sm">
              <h4 className="text-sm font-semibold text-gray-800 mb-2">
                시간별 교통량 추이
              </h4>
              <div className="w-full h-40 overflow-hidden">
                <MiniChart
                  data={chartData}
                  dataKey="volume"
                  color="rgba(59,130,246,0.4)"
                  showAxis={true}
                />
              </div>
            </div>
          </div>

          {/* 위치 정보 카드 */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
              {t("incidents.location")}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  위도 (Latitude)
                </p>
                <p className="text-lg font-mono font-semibold text-gray-900">
                  {intersection.latitude.toFixed(6)}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  경도 (Longitude)
                </p>
                <p className="text-lg font-mono font-semibold text-gray-900">
                  {intersection.longitude.toFixed(6)}
                </p>
              </div>
            </div>
          </div>

          {/* 정책제안 섹션 */}
          <IntersectionProposalSection
            intersection={intersection}
            onRefresh={setProposalRefreshFunction}
          />
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

        {/* 정책제안 작성 모달 */}
        {showCreateProposal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto m-4">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <h2 className="text-xl font-bold text-gray-800">
                  정책제안 작성 - {intersection.name}
                </h2>
                <button
                  onClick={handleCloseCreateProposal}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X size={20} className="text-gray-500" />
                </button>
              </div>
              <div className="p-6">
                <CreateProposalForm
                  preselectedIntersectionId={intersection.id}
                  onClose={handleCloseCreateProposal}
                  onSuccess={handleProposalSuccess}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
