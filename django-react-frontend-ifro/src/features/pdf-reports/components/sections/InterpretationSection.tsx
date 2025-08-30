import React from "react";
import { useTranslation } from "react-i18next";
import { AITrafficAnalysis } from "../../../../shared/types/global.types";

interface InterpretationSectionProps {
  interpretation?: string;
  congestionLevel?: string;
  peakDirection?: string;
  recommendations?: string[];
  aiAnalysis?: AITrafficAnalysis;
  className?: string;
}

export const InterpretationSection: React.FC<InterpretationSectionProps> = ({
  interpretation,
  congestionLevel,
  peakDirection,
  recommendations,
  aiAnalysis,
  className = "",
}) => {
  const { t } = useTranslation();

  // AI 분석 결과를 보고서 형식으로 포맷팅하는 함수
  const formatAIAnalysis = (analysisText: string) => {
    // 불필요한 접두사 제거
    let cleanText = analysisText.replace(
      /^reports\.aiAnalysis\s*"analysis":\s*"?/,
      ""
    );
    cleanText = cleanText.replace(/^"analysis":\s*"?/, "");
    cleanText = cleanText.replace(/^analysis:\s*"?/, "");

    // 문단 분리 및 정리
    const paragraphs = cleanText.split(/\n\n+/).filter((p) => p.trim());

    return paragraphs.map((paragraph, index) => {
      const trimmedParagraph = paragraph.trim();

      // 제목 형식 감지 (**텍스트:** 형식)
      if (trimmedParagraph.includes("**") && trimmedParagraph.includes(":")) {
        const parts = trimmedParagraph.split(/\*\*(.*?)\*\*:/);
        if (parts.length >= 3) {
          const title = parts[1];
          const content = parts[2].trim();

          return (
            <div key={index} className="mb-4">
              <h4 className="text-md font-semibold text-indigo-700 mb-2 flex items-center">
                📋 {title}
              </h4>
              {formatParagraphContent(content)}
            </div>
          );
        }
      }

      // 일반 문단
      return (
        <div key={index} className="mb-3">
          {formatParagraphContent(trimmedParagraph)}
        </div>
      );
    });
  };

  // 문단 내용을 포맷팅하는 함수
  const formatParagraphContent = (content: string) => {
    // 리스트 항목 처리 (* 또는 - 로 시작하는 항목들)
    if (content.includes("\n*") || content.includes("\n-")) {
      const lines = content.split("\n");
      const elements: React.ReactNode[] = [];
      let currentParagraph = "";

      lines.forEach((line, lineIndex) => {
        const trimmedLine = line.trim();

        if (trimmedLine.startsWith("*") || trimmedLine.startsWith("-")) {
          // 이전 문단이 있으면 추가
          if (currentParagraph.trim()) {
            elements.push(
              <p key={`p-${lineIndex}`} className="mb-2 text-gray-800">
                {formatInlineText(currentParagraph.trim())}
              </p>
            );
            currentParagraph = "";
          }

          // 리스트 항목 추가
          const listContent = trimmedLine.replace(/^[*-]\s*/, "");
          elements.push(
            <div
              key={`li-${lineIndex}`}
              className="flex items-start space-x-2 mb-2 ml-4"
            >
              <span className="flex-shrink-0 w-2 h-2 bg-indigo-400 rounded-full mt-2"></span>
              <span className="text-gray-800">
                {formatInlineText(listContent)}
              </span>
            </div>
          );
        } else if (trimmedLine) {
          currentParagraph += (currentParagraph ? " " : "") + trimmedLine;
        }
      });

      // 마지막 문단 처리
      if (currentParagraph.trim()) {
        elements.push(
          <p key="final-p" className="mb-2 text-gray-800">
            {formatInlineText(currentParagraph.trim())}
          </p>
        );
      }

      return <div>{elements}</div>;
    }

    // 일반 문단 처리
    return (
      <p className="text-gray-800 leading-relaxed">
        {formatInlineText(content)}
      </p>
    );
  };

  // 인라인 텍스트 포맷팅 (볼드, 이탤릭 등)
  const formatInlineText = (text: string) => {
    // **볼드** 텍스트 처리
    const parts = text.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        return (
          <strong key={index} className="font-semibold text-indigo-800">
            {part}
          </strong>
        );
      }
      return part;
    });
  };

  if (
    !interpretation &&
    !congestionLevel &&
    !peakDirection &&
    !recommendations?.length &&
    !aiAnalysis
  ) {
    return null;
  }

  const getCongestionIcon = (level?: string) => {
    switch (level?.toLowerCase()) {
      case "bajo":
      case "low":
        return "🟢";
      case "medio":
      case "medium":
        return "🟡";
      case "alto":
      case "high":
        return "🔴";
      default:
        return "⚪";
    }
  };

  const getCongestionDescription = (level?: string) => {
    switch (level?.toLowerCase()) {
      case "bajo":
      case "low":
        return (
          t("reports.lowCongestionDesc") ||
          "El tráfico fluye con normalidad. No se observan congestiones significativas."
        );
      case "medio":
      case "medium":
      case "moderate":
        return (
          t("reports.mediumCongestionDesc") ||
          "Se observa un nivel moderado de congestión. El tráfico puede experimentar algunas demoras."
        );
      case "alto":
      case "high":
        return (
          t("reports.highCongestionDesc") ||
          "Nivel alto de congestión. Se recomienda considerar rutas alternativas."
        );
      default:
        return (
          t("reports.unknownCongestionDesc") ||
          "Nivel de congestión no determinado."
        );
    }
  };

  const translateCongestionLevel = (level?: string) => {
    switch (level?.toLowerCase()) {
      case "low":
        return t("reports.low") || "Bajo";
      case "moderate":
        return t("reports.moderate") || "Moderado";
      case "high":
        return t("reports.high") || "Alto";
      case "medium":
        return t("reports.medium") || "Medio";
      default:
        return level || "";
    }
  };

  const translateInterpretation = (text?: string) => {
    if (!text) return "";

    // 백엔드에서 오는 특정 해석 텍스트들을 번역
    if (text.includes("Análisis basado en datos reales disponibles")) {
      return t("reports.realDataAnalysis") || text;
    }

    // 다른 일반적인 해석 텍스트들도 필요에 따라 추가 가능
    return text;
  };

  return (
    <section
      className={`mb-8 ${className}`}
      style={{ pageBreakInside: "avoid" }}
    >
      <h2 className="text-2xl font-semibold text-gray-800 mb-4 border-l-4 border-yellow-500 pl-4">
        {t("reports.analysisAndInterpretation") || "Análisis e Interpretación"}
      </h2>

      <div className="space-y-4">
        {/* Main Interpretation */}
        {interpretation && (
          <div
            className="bg-blue-50 p-6 rounded-lg border-l-4 border-blue-400"
            style={{ pageBreakInside: "avoid", marginBottom: "1rem" }}
          >
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">📊</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  {t("reports.mainInterpretation") ||
                    "Interpretación Principal"}
                </h3>
                <p className="text-gray-800 leading-relaxed">
                  {translateInterpretation(interpretation)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Congestion Analysis */}
        {congestionLevel && (
          <div
            className="bg-yellow-50 p-6 rounded-lg border-l-4 border-yellow-400"
            style={{ pageBreakInside: "avoid", marginBottom: "1rem" }}
          >
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 text-2xl">
                {getCongestionIcon(congestionLevel)}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  {t("reports.congestionAnalysis") || "Análisis de Congestión"}{" "}
                  - {t("reports.level") || "Nivel"}{" "}
                  {translateCongestionLevel(congestionLevel)}
                </h3>
                <p className="text-gray-800 leading-relaxed">
                  {getCongestionDescription(congestionLevel)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Peak Direction Analysis */}
        {peakDirection && (
          <div
            className="bg-purple-50 p-6 rounded-lg border-l-4 border-purple-400"
            style={{ pageBreakInside: "avoid", marginBottom: "1rem" }}
          >
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">🎯</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  {t("reports.peakDirectionFlow") || "Dirección de Mayor Flujo"}
                </h3>
                <p className="text-gray-800 leading-relaxed">
                  {t("reports.peakDirectionDescription", {
                    direction: peakDirection,
                  }) ||
                    `La dirección ${peakDirection} presenta el mayor volumen de tráfico en el período analizado. Esta información es útil para la planificación de semáforos y gestión del tráfico.`}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && (
          <div
            className="bg-green-50 p-6 rounded-lg border-l-4 border-green-400"
            style={{ pageBreakInside: "avoid", marginBottom: "1rem" }}
          >
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">💡</span>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-800 mb-3">
                  {t("reports.recommendations") || "Recomendaciones"}
                </h3>
                <ul className="space-y-2">
                  {recommendations.map((recommendation, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2"></span>
                      <span className="text-gray-800 leading-relaxed">
                        {recommendation}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* AI Analysis Section - Split into smaller sections */}
        {aiAnalysis && (
          <>
            {/* AI Main Analysis Header with Sample Data Notice */}
            <div className="mb-2" style={{ pageBreakInside: "avoid" }}>
              <div className="flex items-start space-x-3 mb-3">
                <div className="flex-shrink-0 w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">🤖</span>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800">
                    {t("reports.aiAnalysis") || "Análisis Inteligente con IA"}
                  </h3>
                  {/* Sample Data Notice */}
                  {aiAnalysis?.is_sample_data && (
                    <div className="mt-2 p-2 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                      <div className="flex items-center">
                        <span className="text-yellow-600 text-sm font-medium">
                          ⚠️
                        </span>
                        <span className="ml-2 text-yellow-800 text-sm">
                          {t("reports.sampleDataNotice") ||
                            "이 분석은 시연용 샘플 데이터를 기반으로 작성되었습니다."}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* AI Analysis as formatted report */}
            {aiAnalysis?.analysis &&
              typeof aiAnalysis.analysis === "string" && (
                <div
                  className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-lg border-l-4 border-indigo-500 mb-4"
                  style={{ pageBreakInside: "avoid" }}
                >
                  <div
                    className="text-gray-800"
                    style={{
                      wordWrap: "break-word",
                      hyphens: "auto",
                      lineHeight: "1.6",
                    }}
                  >
                    {formatAIAnalysis(aiAnalysis.analysis)}
                  </div>
                </div>
              )}

            {/* AI Insights - Unified section */}
            {aiAnalysis?.insights &&
              Array.isArray(aiAnalysis.insights) &&
              aiAnalysis.insights.length > 0 && (
                <div
                  className="bg-indigo-50 p-6 rounded-lg border-l-4 border-indigo-400 mb-4"
                  style={{ pageBreakInside: "avoid" }}
                >
                  <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center">
                    🔍 {t("reports.aiInsights") || "Insights Clave"}
                  </h4>
                  <ul className="space-y-2">
                    {aiAnalysis.insights
                      .filter(
                        (insight) => insight && typeof insight === "string"
                      )
                      .map((insight, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="flex-shrink-0 w-2 h-2 bg-indigo-400 rounded-full mt-2"></span>
                          <span
                            className="text-gray-700"
                            style={{
                              wordWrap: "break-word",
                              hyphens: "auto",
                              lineHeight: "1.5",
                            }}
                          >
                            {insight}
                          </span>
                        </li>
                      ))}
                  </ul>
                </div>
              )}

            {/* AI Trends - Unified section */}
            {aiAnalysis?.trends &&
              Array.isArray(aiAnalysis.trends) &&
              aiAnalysis.trends.length > 0 && (
                <div
                  className="bg-purple-50 p-6 rounded-lg border-l-4 border-purple-400 mb-4"
                  style={{ pageBreakInside: "avoid" }}
                >
                  <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center">
                    📈 {t("reports.aiTrends") || "Tendencias Identificadas"}
                  </h4>
                  <ul className="space-y-2">
                    {aiAnalysis.trends
                      .filter((trend) => trend && typeof trend === "string")
                      .map((trend, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="flex-shrink-0 w-2 h-2 bg-purple-400 rounded-full mt-2"></span>
                          <span
                            className="text-gray-700"
                            style={{
                              wordWrap: "break-word",
                              hyphens: "auto",
                              lineHeight: "1.5",
                            }}
                          >
                            {trend}
                          </span>
                        </li>
                      ))}
                  </ul>
                </div>
              )}

            {/* AI Recommendations - Unified section */}
            {aiAnalysis?.recommendations &&
              Array.isArray(aiAnalysis.recommendations) &&
              aiAnalysis.recommendations.length > 0 && (
                <div
                  className="bg-green-50 p-6 rounded-lg border-l-4 border-green-400 mb-4"
                  style={{ pageBreakInside: "avoid" }}
                >
                  <h4 className="text-md font-semibold text-gray-700 mb-3 flex items-center">
                    💡 {t("reports.aiRecommendations") || "Recomendaciones IA"}
                  </h4>
                  <ul className="space-y-2">
                    {aiAnalysis.recommendations
                      .filter((rec) => rec && typeof rec === "string")
                      .map((recommendation, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <span className="flex-shrink-0 w-2 h-2 bg-green-400 rounded-full mt-2"></span>
                          <span
                            className="text-gray-700"
                            style={{
                              wordWrap: "break-word",
                              hyphens: "auto",
                              lineHeight: "1.5",
                            }}
                          >
                            {recommendation}
                          </span>
                        </li>
                      ))}
                  </ul>
                </div>
              )}

            {/* Peak Hours - Separate section */}
            {aiAnalysis?.peak_hours &&
              Array.isArray(aiAnalysis.peak_hours) &&
              aiAnalysis.peak_hours.length > 0 && (
                <div
                  className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-400 mb-4"
                  style={{ pageBreakInside: "avoid" }}
                >
                  <h4 className="text-md font-semibold text-gray-700 mb-2">
                    ⏰ {t("reports.peakHours") || "Horas Pico Identificadas"}
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {aiAnalysis.peak_hours
                      .filter((hour) => hour && typeof hour === "string")
                      .map((hour, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full"
                        >
                          {hour}
                        </span>
                      ))}
                  </div>
                </div>
              )}

            {/* AI Generated Timestamp */}
            {aiAnalysis?.timestamp && (
              <div
                className="text-xs text-gray-500 mb-4 p-2 bg-gray-50 rounded"
                style={{ pageBreakInside: "avoid" }}
              >
                {t("reports.aiGeneratedAt") || "Análisis generado por IA el"}:{" "}
                {new Date(aiAnalysis?.timestamp || Date.now()).toLocaleString()}
              </div>
            )}
          </>
        )}

        {/* Key Insights Summary */}
        <div
          className="bg-gray-50 p-6 rounded-lg border border-gray-200"
          style={{ pageBreakInside: "avoid", marginTop: "2rem" }}
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-3">
            {t("reports.keyInsights") || "Puntos Clave del Análisis"}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(congestionLevel || aiAnalysis?.congestion_level) && (
              <div className="flex items-center space-x-2">
                <span className="text-lg">
                  {getCongestionIcon(
                    congestionLevel || aiAnalysis?.congestion_level
                  )}
                </span>
                <span className="text-sm text-gray-700">
                  {t("reports.congestion") || "Congestión"}:{" "}
                  <strong className="capitalize">
                    {translateCongestionLevel(
                      congestionLevel || aiAnalysis?.congestion_level
                    )}
                  </strong>
                </span>
              </div>
            )}
            {(peakDirection || aiAnalysis?.peak_direction) && (
              <div className="flex items-center space-x-2">
                <span className="text-lg">🎯</span>
                <span className="text-sm text-gray-700">
                  {t("reports.peakDirectionShort") || "Dirección pico"}:{" "}
                  <strong>{peakDirection || aiAnalysis?.peak_direction}</strong>
                </span>
              </div>
            )}
            <div className="flex items-center space-x-2">
              <span className="text-lg">📈</span>
              <span className="text-sm text-gray-700">
                {t("reports.analysis") || "Análisis"}:{" "}
                <strong>{t("reports.completed") || "Completado"}</strong>
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-lg">{aiAnalysis ? "🤖" : "⏰"}</span>
              <span className="text-sm text-gray-700">
                {t("reports.status") || "Estado"}:{" "}
                <strong>
                  {aiAnalysis
                    ? t("reports.aiEnhanced") || "Mejorado con IA"
                    : t("reports.updated") || "Actualizado"}
                </strong>
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
