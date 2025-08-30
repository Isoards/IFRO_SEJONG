import React, { useState, useRef, useEffect } from "react";
import { debugLog } from "../../../shared/utils/debugUtils";
import { useTranslation } from "react-i18next";
import { PDFTemplate } from "../../pdf-reports/components/PDFTemplate";
import { usePDFGeneration } from "../../../shared/utils/usePDFGeneration";
import { generateAITrafficAnalysis } from "../../../shared/services/intersections";
import {
  ReportData,
  AITrafficAnalysis,
} from "../../../shared/types/global.types";

interface AIEnhancedPDFButtonProps {
  reportData: ReportData;
  className?: string;
  buttonText?: string;
  timePeriod?: string;
  disabled?: boolean;
}

/**
 * AI Enhanced PDF Button Component
 * A button that generates PDF reports with AI analysis
 */
export const AIEnhancedPDFButton: React.FC<AIEnhancedPDFButtonProps> = ({
  reportData,
  className = "",
  buttonText,
  timePeriod = "24h",
  disabled = false,
}) => {
  const { t, i18n } = useTranslation();
  const templateRef = useRef<HTMLDivElement>(null);
  const [aiAnalysis, setAiAnalysis] = useState<AITrafficAnalysis | null>(null);
  const [isLoadingAI, setIsLoadingAI] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [shouldGeneratePDF, setShouldGeneratePDF] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState(i18n.language || "ko");

  const { status, generatePDF, isSupported } = usePDFGeneration({
    config: {
      format: "A4",
      orientation: "portrait",
      quality: 1.0,
    },
    onSuccess: () => {
      debugLog("AI Enhanced PDF generated successfully!");
    },
    onError: (error) => {
      console.error("AI Enhanced PDF generation failed:", error);
    },
  });

  const loadAIAnalysis = async (): Promise<AITrafficAnalysis | null> => {
    if (!reportData.intersection?.id) {
      console.warn("No intersection ID available for AI analysis");
      return null;
    }

    setIsLoadingAI(true);
    setAiError(null);

    try {
      // 현재 언어 설정 가져오기
      const currentLanguage = i18n.language || "ko";
      debugLog(
        "Loading AI analysis for intersection:",
        reportData.intersection.id,
        "in language:",
        currentLanguage
      );

      const response = await generateAITrafficAnalysis(
        reportData.intersection.id,
        timePeriod,
        currentLanguage
      );

      if (!response || !response.analysis) {
        throw new Error("AI 분석 응답이 올바르지 않습니다.");
      }

      const analysis = response.analysis;
      debugLog("AI Analysis loaded successfully:", analysis);
      setAiAnalysis(analysis);
      return analysis;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "AI 분석 생성에 실패했습니다.";
      setAiError(errorMessage);
      console.error("AI Analysis Error:", error);

      // 사용자에게 더 친화적인 오류 메시지 제공
      if (
        errorMessage.includes("timeout") ||
        errorMessage.includes("시간이 초과")
      ) {
        setAiError(
          "AI 분석 요청 시간이 초과되었습니다. 네트워크 상태를 확인하고 다시 시도해주세요."
        );
      } else if (
        errorMessage.includes("API 키") ||
        errorMessage.includes("서비스에 문제")
      ) {
        setAiError(
          "AI 분석 서비스 설정에 문제가 있습니다. 관리자에게 문의해주세요."
        );
      }

      return null;
    } finally {
      setIsLoadingAI(false);
    }
  };

  // 언어가 바뀌면 AI 분석 초기화
  useEffect(() => {
    if (currentLanguage !== i18n.language) {
      debugLog("Language changed from", currentLanguage, "to", i18n.language);
      setCurrentLanguage(i18n.language || "ko");
      setAiAnalysis(null); // AI 분석 초기화
    }
  }, [i18n.language, currentLanguage]);

  // 교차로가 변경되면 AI 분석 상태 초기화
  useEffect(() => {
    debugLog("Intersection changed, clearing AI analysis cache");
    setAiAnalysis(null);
    setAiError(null);
    setShouldGeneratePDF(false);
  }, [reportData.intersection?.id]);

  // AI 분석이 완료되면 PDF 생성
  useEffect(() => {
    if (shouldGeneratePDF && aiAnalysis && templateRef.current) {
      debugLog("Generating PDF with AI analysis:", aiAnalysis);
      // AI 분석 데이터를 reportData에 포함시켜 PDF 생성
      const enhancedReportData = {
        ...reportData,
        aiAnalysis: aiAnalysis,
      };
      generatePDF(enhancedReportData, templateRef.current);
      setShouldGeneratePDF(false);
    }
  }, [aiAnalysis, shouldGeneratePDF, generatePDF, reportData]);

  const handleGenerateAIPDF = async () => {
    if (!templateRef.current || !isSupported) {
      console.error(
        "PDF generation not supported or template element not found"
      );
      return;
    }

    try {
      // AI 분석이 이미 있고 같은 교차로인 경우에만 재사용
      if (aiAnalysis && reportData.intersection?.id) {
        debugLog(
          "Using existing AI analysis for intersection:",
          reportData.intersection.id
        );
        const enhancedReportData = {
          ...reportData,
          aiAnalysis: aiAnalysis,
        };
        await generatePDF(enhancedReportData, templateRef.current);
        return;
      }

      // AI 분석 로드
      debugLog("Loading AI analysis...");
      const currentAiAnalysis = await loadAIAnalysis();

      if (currentAiAnalysis) {
        debugLog("AI Analysis loaded:", currentAiAnalysis);
        setAiAnalysis(currentAiAnalysis);
        setShouldGeneratePDF(true); // useEffect에서 PDF 생성하도록 플래그 설정
      } else {
        console.warn("No AI analysis available, generating PDF without AI");
        // AI 분석 없이 기본 PDF 생성
        await generatePDF(reportData, templateRef.current);
      }
    } catch (error) {
      console.error("Error generating AI enhanced PDF:", error);
    }
  };

  const getButtonText = () => {
    if (buttonText) return buttonText;

    if (isLoadingAI) return t("reports.loadingAI") || "Loading AI...";
    if (status.isGenerating) return t("reports.generating") || "Generating...";
    if (status.completed) return t("reports.downloadAIPDF") || "AI PDF";

    return t("reports.downloadAIPDF") || "AI PDF";
  };

  const getStatusIcon = () => {
    if (isLoadingAI || status.isGenerating) {
      return (
        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
      );
    } else if (status.completed) {
      return <span className="text-green-400">✓</span>;
    } else if (status.error) {
      return <span className="text-red-400">⚠</span>;
    }
    return null; // 이모티콘 제거
  };

  const isButtonDisabled =
    disabled || !isSupported || isLoadingAI || status.isGenerating;

  if (!isSupported) {
    return (
      <div className={`ai-pdf-button-container ${className}`}>
        <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded text-sm">
          {t("reports.browserNotSupported") ||
            "PDF generation not supported in this browser"}
        </div>
      </div>
    );
  }

  return (
    <div className={`ai-pdf-button-container ${className}`}>
      {/* AI Error Display */}
      {aiError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded text-sm mb-2">
          {aiError}
        </div>
      )}

      {/* Main Button */}
      <button
        onClick={handleGenerateAIPDF}
        disabled={isButtonDisabled}
        className={`
          flex items-center justify-center space-x-1 transition-all duration-200
          ${
            className ||
            "px-3 py-1.5 rounded-md text-sm font-medium min-w-[80px] bg-purple-600 hover:bg-purple-700 text-white border border-purple-600"
          }
          ${
            isButtonDisabled
              ? "!bg-gray-300 !text-gray-500 !border-gray-300 cursor-not-allowed opacity-50"
              : className
              ? "" // className이 있으면 기본 스타일 적용하지 않음
              : status.completed
              ? "bg-purple-600 hover:bg-purple-700 text-white border-purple-600"
              : "bg-purple-600 hover:bg-purple-700 text-white border-purple-600"
          }
        `}
        aria-label={getButtonText()}
        title={getButtonText()}
      >
        {getStatusIcon()}
        <span
          className={`whitespace-nowrap ${className ? "text-xs" : "text-sm"}`}
        >
          {getButtonText()}
        </span>
      </button>

      {/* Hidden PDF Template */}
      <div style={{ position: "absolute", left: "-9999px", top: "-9999px" }}>
        <div ref={templateRef}>
          <PDFTemplate
            reportData={reportData}
            aiAnalysis={aiAnalysis || undefined}
          />
        </div>
      </div>
    </div>
  );
};

export default AIEnhancedPDFButton;
