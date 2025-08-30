import React, { useRef, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { X, Star, Plus } from "lucide-react";
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

  // 컴포넌트 마운트 시 실제 데이터 가져오기
  React.useEffect(() => {
    console.log(
      "Intersection changed to:",
      intersection.id,
      "clearing previous data"
    );
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
      const currentLanguage = i18n.language || "ko";
      const data = await getIntersectionReportData(
        intersection.id,
        undefined,
        currentLanguage
      );

      console.log("API Response:", data);
      console.log("Traffic Volumes:", data.trafficVolumes);

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

      console.log("Setting report data:", newReportData);
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
      console.log("Waiting for report data to load...");
      return;
    }

    // 실제 데이터가 있으면 사용하고, 없으면 기본 데이터 사용
    const dataToUse = actualReportData || reportData;
    console.log("Using report data:", dataToUse);
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
    <div className="h-full w-full max-w-2xl mx-auto p-4 pt-3 bg-white relative overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <h2 className="text-xl font-bold text-blue-600 mb-1">
            {t("traffic.intersections")} {t("traffic.analysis")}
          </h2>
        </div>
        <div className="flex items-center space-x-1 ml-4">
          <button
            onClick={handleCreateProposal}
            className="inline-flex items-center justify-center h-8 px-3 bg-green-600/50 hover:bg-green-600 text-white transition-all duration-300 rounded-md text-xs font-medium"
            title="정책제안 작성"
          >
            <Plus size={14} className="mr-1" />
            정책제안
          </button>
          {isSupported && (
            <>
              <AIEnhancedPDFButton
                reportData={actualReportData || reportData}
                className="bg-blue-600/50 hover:bg-blue-600 text-white transition-all duration-300 text-xs h-8 px-2 rounded-md inline-flex items-center justify-center"
                buttonText="AI PDF"
                timePeriod="24h"
              />
              <button
                onClick={handleDownloadPDF}
                className="inline-flex items-center justify-center h-8 px-2 bg-blue-600/50 hover:bg-blue-600 text-white transition-all duration-300 rounded-md text-xs font-medium disabled:opacity-50 disabled:pointer-events-none"
                disabled={status.isGenerating || isLoadingReportData}
              >
                {isLoadingReportData ? "Loading..." : "PDF"}
              </button>
            </>
          )}
          <button
            onClick={() => onToggleFavorite(intersection.id)}
            className={`inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
              isFavorited
                ? "bg-primary text-primary-foreground hover:bg-primary/90 text-yellow-400"
                : "hover:bg-accent hover:text-accent-foreground text-gray-400"
            }`}
            title={isFavorited ? "즐겨찾기 해제" : "즐겨찾기 추가"}
          >
            <Star size={16} fill={isFavorited ? "currentColor" : "none"} />
          </button>
          <button
            onClick={onClose}
            aria-label="Close panel"
            className="inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="text-base font-semibold text-gray-800 mb-2">
            {intersection.name}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-3">
            <div className="p-3 bg-white rounded-lg shadow-sm">
              <p className="text-xs text-gray-500">{t("traffic.speed")}</p>
              <p className="text-lg font-bold text-gray-800">{`${displaySpeed.toFixed(
                1
              )} km/h`}</p>
            </div>
            <div className="p-3 bg-white rounded-lg shadow-sm">
              <p className="text-xs text-gray-500">{t("traffic.volume")}</p>
              <p className="text-lg font-bold text-gray-800">{`${displayVolume} vph`}</p>
            </div>
          </div>

          <div className="w-full h-32 bg-white rounded-lg flex items-center justify-center shadow-sm">
            <MiniChart
              data={chartData}
              dataKey="volume"
              color="rgba(59,130,246,0.4)"
              showAxis={true}
            />
          </div>
        </div>

        <div className="p-4 bg-gray-50 rounded-lg">
          <h3 className="text-base font-semibold text-gray-800 mb-3">
            {t("incidents.location")}
          </h3>
          <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-6 text-gray-700 text-sm">
            <span>
              Lat:{" "}
              <span className="font-medium">
                {intersection.latitude.toFixed(6)}
              </span>
            </span>
            <span>
              Lng:{" "}
              <span className="font-medium">
                {intersection.longitude.toFixed(6)}
              </span>
            </span>
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
  );
};
