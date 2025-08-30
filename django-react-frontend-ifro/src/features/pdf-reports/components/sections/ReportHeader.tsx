import React from 'react';
import { useTranslation } from 'react-i18next';

interface ReportHeaderProps {
  title?: string;
  subtitle?: string;
  generatedDate?: string;
  className?: string;
}

export const ReportHeader: React.FC<ReportHeaderProps> = ({
  title,
  subtitle,
  generatedDate,
  className = '',
}) => {
  const { t, i18n } = useTranslation();

  const defaultTitle = t("reports.trafficReportTitle") || "Reporte de Tráfico - WILL";
  const defaultSubtitle = t("reports.intelligentTrafficAnalysisSystem") || "Sistema de Análisis de Tráfico Inteligente";

  const formatDate = (dateString?: string): string => {
    const date = dateString ? new Date(dateString) : new Date();
    const locale = i18n.language === 'ko' ? 'ko-KR' : 'es-PE';
    return date.toLocaleDateString(locale, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <header
      className={className}
      style={{
        marginBottom: '32px',
        borderBottom: '2px solid #d1d5db',
        paddingBottom: '16px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{
            fontSize: '28px',
            fontWeight: 'bold',
            color: '#1f2937',
            margin: '0 0 8px 0',
            lineHeight: '1.1',
            verticalAlign: 'top'
          }}>
            {title || defaultTitle}
          </h1>
          <div style={{ color: '#6b7280' }}>
            <p style={{
              fontSize: '18px',
              margin: '0 0 4px 0',
              lineHeight: '1.2',
              verticalAlign: 'top'
            }}>{subtitle || defaultSubtitle}</p>
            <p style={{
              fontSize: '14px',
              margin: '0',
              lineHeight: '1.2',
              verticalAlign: 'top'
            }}>{t("reports.generatedOn") || "Generado el"}: {formatDate(generatedDate)}</p>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <img
            src="/WILL_logo.svg"
            alt="WILL"
            style={{ height: '32px', width: 'auto' }}
          />
        </div>
      </div>
    </header>
  );
};