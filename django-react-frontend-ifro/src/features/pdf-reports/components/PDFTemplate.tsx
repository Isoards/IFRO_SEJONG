import React from 'react';
import { useTranslation } from 'react-i18next';
import { ReportData, AITrafficAnalysis } from '../../../shared/types/global.types';
import {
  ReportHeader,
  IntersectionInfo,
  TrafficDataTable,
  InterpretationSection,
  ChartSection,
  ReportFooter,
} from './sections';

interface PDFTemplateProps {
  reportData: ReportData;
  chartImage?: string;
  className?: string;
  customTitle?: string;
  customSubtitle?: string;
  recommendations?: string[];
  aiAnalysis?: AITrafficAnalysis;
}

/**
 * Enhanced PDF Template Component
 * This component renders the HTML structure that will be converted to PDF
 * using modular section components for better maintainability
 */
export const PDFTemplate: React.FC<PDFTemplateProps> = ({
  reportData,
  chartImage,
  className = '',
  customTitle,
  customSubtitle,
  recommendations,
  aiAnalysis,
}) => {
  const { t } = useTranslation();
  
  return (
    <div 
      className={`pdf-template bg-white ${className}`} 
      style={{ 
        width: '210mm', 
        minHeight: '297mm',
        padding: '15mm',
        fontFamily: 'Arial, sans-serif',
        fontSize: '14px',
        lineHeight: '1.4',
        color: '#333333',
        boxSizing: 'border-box',
        textRendering: 'optimizeLegibility',
        WebkitFontSmoothing: 'antialiased',
        pageBreakInside: 'avoid',
        orphans: 2,
        widows: 2,
        breakInside: 'avoid'
      }}
      data-pdf-template
    >
      {/* Report Header */}
      <ReportHeader
        title={customTitle}
        subtitle={customSubtitle}
        generatedDate={new Date().toISOString()}
      />

      {/* Intersection Information */}
      <IntersectionInfo
        intersection={reportData.intersection}
        datetime={reportData.datetime}
        totalVolume={reportData.totalVolume}
      />

      {/* Traffic Data Table */}
      <TrafficDataTable
        trafficVolumes={reportData.trafficVolumes}
        totalVolume={reportData.totalVolume}
        averageSpeed={reportData.averageSpeed}
        peakDirection={reportData.peakDirection}
        congestionLevel={reportData.congestionLevel}
      />

      {/* Interpretation Section */}
      <InterpretationSection
        interpretation={reportData.interpretation}
        congestionLevel={reportData.congestionLevel}
        peakDirection={reportData.peakDirection}
        recommendations={recommendations}
        aiAnalysis={aiAnalysis}
      />

      {/* Chart Section */}
      <ChartSection
        chartImage={chartImage}
        chartTitle={t("reports.visualTrafficAnalysis") || "Análisis Visual del Tráfico"}
        chartDescription={t("reports.trafficDataVisualization") || "Representación gráfica de los datos de tráfico analizados"}
      />

      {/* Report Footer */}
      <ReportFooter
        organizationName="WILL"
        systemName={t("reports.intelligentTrafficAnalysisSystem") || "Sistema de Análisis de Tráfico Inteligente"}
        contactInfo={t("reports.contactInfo") || "Para más información, contacte al administrador del sistema"}
      />
    </div>
  );
};

export default PDFTemplate;