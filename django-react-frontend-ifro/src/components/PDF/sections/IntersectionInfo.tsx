import React from 'react';
import { useTranslation } from 'react-i18next';
import { Intersection } from '../../../types/global.types';

interface IntersectionInfoProps {
  intersection: Intersection;
  datetime: string;
  totalVolume: number;
  className?: string;
}

export const IntersectionInfo: React.FC<IntersectionInfoProps> = ({
  intersection,
  datetime,
  totalVolume,
  className = '',
}) => {
  const { t, i18n } = useTranslation();
  
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const locale = i18n.language === 'ko' ? 'ko-KR' : 'es-PE';
    return date.toLocaleDateString(locale, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatTrafficVolume = (volume: number): string => {
    if (volume === undefined || volume === null || isNaN(volume)) {
      return '0';
    }
    return volume.toLocaleString('es-PE');
  };

  return (
    <section className={className} style={{ marginBottom: '32px' }}>
      <h2 style={{
        fontSize: '24px',
        fontWeight: '600',
        color: '#1f2937',
        marginBottom: '16px',
        borderLeft: '4px solid #3b82f6',
        paddingLeft: '16px',
        margin: '0 0 16px 0'
      }}>
        {t("reports.intersectionInfo") || "Información del Cruce"}
      </h2>
      <div style={{
        background: 'linear-gradient(to right, #eff6ff, #e0e7ff)',
        padding: '24px',
        borderRadius: '8px',
        border: '1px solid #bfdbfe'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          <div>
            <div style={{ marginBottom: '16px' }}>
              <p style={{ 
                fontSize: '14px', 
                color: '#6b7280', 
                fontWeight: '500', 
                margin: '0 0 2px 0',
                lineHeight: '1.1',
                verticalAlign: 'top'
              }}>{t("reports.intersectionName") || "Nombre del Cruce"}:</p>
              <p style={{ 
                fontSize: '18px', 
                fontWeight: '600', 
                color: '#1f2937', 
                margin: '0',
                lineHeight: '1.2',
                verticalAlign: 'top'
              }}>{intersection.name}</p>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <p style={{ 
                fontSize: '14px', 
                color: '#6b7280', 
                fontWeight: '500', 
                margin: '0 0 2px 0',
                lineHeight: '1.1',
                verticalAlign: 'top'
              }}>{t("reports.dateTime") || "Fecha y Hora"}:</p>
              <p style={{ 
                fontSize: '18px', 
                fontWeight: '600', 
                color: '#1f2937', 
                margin: '0',
                lineHeight: '1.2',
                verticalAlign: 'top'
              }}>{formatDate(datetime)}</p>
            </div>
          </div>
          <div>
            <div style={{ marginBottom: '16px' }}>
              <p style={{ 
                fontSize: '14px', 
                color: '#6b7280', 
                fontWeight: '500', 
                margin: '0 0 2px 0',
                lineHeight: '1.1',
                verticalAlign: 'top'
              }}>{t("reports.coordinates") || "Coordenadas"}:</p>
              <p style={{ 
                fontSize: '18px', 
                fontWeight: '600', 
                color: '#1f2937', 
                margin: '0',
                lineHeight: '1.2',
                verticalAlign: 'top'
              }}>
                {intersection.latitude?.toFixed(6) || 'N/A'}, {intersection.longitude?.toFixed(6) || 'N/A'}
              </p>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <p style={{ 
                fontSize: '14px', 
                color: '#6b7280', 
                fontWeight: '500', 
                margin: '0 0 2px 0',
                lineHeight: '1.1',
                verticalAlign: 'top'
              }}>{t("reports.totalVolume") || "Volumen Total"}:</p>
              <p style={{ 
                fontSize: '18px', 
                fontWeight: '600', 
                color: '#2563eb', 
                margin: '0',
                lineHeight: '1.2',
                verticalAlign: 'top'
              }}>
                {formatTrafficVolume(totalVolume)} {t("reports.vehicles") || "vehículos"}
              </p>
            </div>
          </div>
        </div>
        
        {/* Additional intersection details if available */}
        <div style={{
          marginTop: '16px',
          paddingTop: '16px',
          borderTop: '1px solid #bfdbfe'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <div>
              <p style={{ 
                fontSize: '14px', 
                color: '#6b7280', 
                fontWeight: '500', 
                margin: '0 0 2px 0',
                lineHeight: '1.1',
                verticalAlign: 'top'
              }}>{t("reports.intersectionId") || "ID del Cruce"}:</p>
              <p style={{ 
                fontSize: '16px', 
                color: '#1f2937', 
                margin: '0',
                lineHeight: '1.2',
                verticalAlign: 'top'
              }}>#{intersection.id}</p>
            </div>
            <div>
              <p style={{ 
                fontSize: '14px', 
                color: '#6b7280', 
                fontWeight: '500', 
                margin: '0 0 2px 0',
                lineHeight: '1.1',
                verticalAlign: 'top'
              }}>{t("reports.averageSpeed") || "Velocidad Promedio Registrada"}:</p>
              <p style={{ 
                fontSize: '16px', 
                color: '#1f2937', 
                margin: '0',
                lineHeight: '1.2',
                verticalAlign: 'top'
              }}>{intersection.average_speed?.toFixed(1) || 'N/A'} km/h</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};