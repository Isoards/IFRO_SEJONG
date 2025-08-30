import React from 'react';
import { useTranslation } from 'react-i18next';
import { TrafficVolumeData } from '../../../../shared/types/global.types';

interface TrafficDataTableProps {
  trafficVolumes: TrafficVolumeData;
  totalVolume: number;
  averageSpeed: number;
  peakDirection?: string;
  congestionLevel?: string;
  className?: string;
}

const DIRECTION_LABELS = {
  N: 'North (N)',
  S: 'South (S)', 
  E: 'East (E)',
  W: 'West (W)'
};

export const TrafficDataTable: React.FC<TrafficDataTableProps> = ({
  trafficVolumes,
  totalVolume,
  averageSpeed,
  peakDirection,
  congestionLevel,
  className = '',
}) => {
  const { t } = useTranslation();
  
  const formatTrafficVolume = (volume: number): string => {
    if (volume === undefined || volume === null || isNaN(volume)) {
      return '0';
    }
    return volume.toLocaleString('es-PE');
  };

  const getPercentage = (volume: number): string => {
    if (volume === undefined || volume === null || isNaN(volume) || totalVolume === 0) {
      return '0.0';
    }
    return ((volume / totalVolume) * 100).toFixed(1);
  };

  return (
    <section className={className} style={{ 
      marginBottom: '48px', // Increased margin for better page breaks
      pageBreakInside: 'avoid'
    }}>
      <h2 style={{
        fontSize: '24px',
        fontWeight: '600',
        color: '#1f2937',
        marginBottom: '24px', // Increased margin
        borderLeft: '4px solid #10b981',
        paddingLeft: '16px',
        margin: '0 0 24px 0'
      }}>
        {t("reports.trafficData") || "Datos de Tráfico"}
      </h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* Traffic Volumes by Direction */}
        <div style={{
          backgroundColor: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <div style={{
            backgroundColor: '#f0fdf4',
            padding: '12px 16px',
            borderBottom: '1px solid #bbf7d0'
          }}>
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              color: '#1f2937',
              margin: '0'
            }}>{t("reports.volumeByDirection") || "Volumen por Dirección"}</h3>
          </div>
          <div style={{ padding: '16px' }}>
            <div>
              {trafficVolumes && Object.entries(trafficVolumes).length > 0 ? 
                Object.entries(trafficVolumes).map(([direction, volume], index) => (
                <div key={direction} style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  marginBottom: index < (trafficVolumes ? Object.entries(trafficVolumes).length : 0) - 1 ? '12px' : '0'
                }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                    <div style={{
                      width: '12px',
                      height: '12px',
                      backgroundColor: '#3b82f6',
                      borderRadius: '50%',
                      marginRight: '12px',
                      marginTop: '2px' // Align with text baseline
                    }}></div>
                    <span style={{
                      color: '#374151',
                      fontWeight: '500',
                      lineHeight: '1.2',
                      verticalAlign: 'top'
                    }}>
                      {DIRECTION_LABELS[direction as keyof typeof DIRECTION_LABELS]}
                    </span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{
                      fontSize: '18px',
                      fontWeight: 'bold',
                      color: '#1f2937',
                      margin: '0'
                    }}>
                      {formatTrafficVolume(volume)}
                    </div>
                    <div style={{
                      fontSize: '14px',
                      color: '#6b7280',
                      margin: '0'
                    }}>
                      {getPercentage(volume)}%
                    </div>
                  </div>
                </div>
              )) : (
                <div style={{
                  padding: '24px',
                  textAlign: 'center',
                  color: '#6b7280',
                  fontSize: '14px'
                }}>
                  {t("reports.noTrafficData") || "No hay datos de tráfico disponibles"}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Summary Statistics */}
        <div style={{
          backgroundColor: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <div style={{
            backgroundColor: '#eff6ff',
            padding: '12px 16px',
            borderBottom: '1px solid #bfdbfe'
          }}>
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              color: '#1f2937',
              margin: '0'
            }}>{t("reports.summaryStatistics") || "Estadísticas Resumen"}</h3>
          </div>
          <div style={{ padding: '16px' }}>
            <div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                padding: '12px',
                backgroundColor: '#f9fafb',
                borderRadius: '8px',
                marginBottom: '16px'
              }}>
                <span style={{ 
                  color: '#374151', 
                  fontWeight: '500',
                  lineHeight: '1.2',
                  paddingTop: '2px'
                }}>{t("reports.totalVolume") || "Volumen Total"}:</span>
                <span style={{
                  fontSize: '20px',
                  fontWeight: 'bold',
                  color: '#2563eb',
                  lineHeight: '1.2'
                }}>
                  {formatTrafficVolume(totalVolume || 0)}
                </span>
              </div>
              
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                padding: '12px',
                backgroundColor: '#f9fafb',
                borderRadius: '8px',
                marginBottom: '16px'
              }}>
                <span style={{ 
                  color: '#374151', 
                  fontWeight: '500',
                  lineHeight: '1.2',
                  paddingTop: '2px'
                }}>{t("reports.averageSpeed") || "Velocidad Promedio"}:</span>
                <span style={{
                  fontSize: '20px',
                  fontWeight: 'bold',
                  color: '#10b981',
                  lineHeight: '1.2'
                }}>
                  {(averageSpeed || 0).toFixed(1)} km/h
                </span>
              </div>
              
              {peakDirection && (
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  padding: '12px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  marginBottom: '16px'
                }}>
                  <span style={{ 
                    color: '#374151', 
                    fontWeight: '500',
                    lineHeight: '1.2',
                    paddingTop: '1px'
                  }}>{t("reports.peakDirection") || "Dirección Pico"}:</span>
                  <span style={{
                    fontSize: '18px',
                    fontWeight: 'bold',
                    color: '#7c3aed',
                    textTransform: 'capitalize',
                    lineHeight: '1.2'
                  }}>
                    {peakDirection}
                  </span>
                </div>
              )}
              
              {congestionLevel && (
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  padding: '12px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px'
                }}>
                  <span style={{ 
                    color: '#374151', 
                    fontWeight: '500',
                    lineHeight: '1.2',
                    paddingTop: '4px'
                  }}>{t("reports.congestionLevel") || "Nivel de Congestión"}:</span>
                  <span style={{
                    padding: '6px 12px',
                    borderRadius: '9999px',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    textTransform: 'capitalize',
                    backgroundColor: congestionLevel === 'low' ? '#dcfce7' : congestionLevel === 'high' ? '#fee2e2' : '#fef3c7',
                    color: congestionLevel === 'low' ? '#166534' : congestionLevel === 'high' ? '#991b1b' : '#92400e',
                    lineHeight: '1.2'
                  }}>
                    {congestionLevel}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Traffic Flow Summary Table */}
      <div style={{
        marginTop: '32px',
        marginBottom: '32px',
        backgroundColor: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        overflow: 'hidden',
        pageBreakInside: 'avoid', // CSS hint for page break avoidance
        breakInside: 'avoid' // Alternative CSS property
      }}>
        <div style={{
          backgroundColor: '#f9fafb',
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <h3 style={{
            fontSize: '18px',
            fontWeight: '600',
            color: '#1f2937',
            margin: '0'
          }}>{t("reports.trafficFlowSummary") || "Resumen de Flujo de Tráfico"}</h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ backgroundColor: '#f3f4f6' }}>
              <tr>
                <th style={{
                  padding: '12px 16px',
                  textAlign: 'left',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#374151'
                }}>{t("reports.direction") || "Dirección"}</th>
                <th style={{
                  padding: '12px 16px',
                  textAlign: 'right',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#374151'
                }}>{t("reports.volume") || "Volumen"}</th>
                <th style={{
                  padding: '12px 16px',
                  textAlign: 'right',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#374151'
                }}>{t("reports.percentage") || "Porcentaje"}</th>
                <th style={{
                  padding: '12px 16px',
                  textAlign: 'center',
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#374151'
                }}>{t("reports.status") || "Estado"}</th>
              </tr>
            </thead>
            <tbody>
              {trafficVolumes && Object.entries(trafficVolumes).map(([direction, volume], index) => {
                const percentage = parseFloat(getPercentage(volume));
                const isHighVolume = percentage > 30;
                return (
                  <tr key={direction} style={{
                    borderTop: index > 0 ? '1px solid #e5e7eb' : 'none'
                  }}>
                    <td style={{
                      padding: '12px 16px',
                      fontSize: '14px',
                      color: '#1f2937',
                      fontWeight: '500'
                    }}>
                      {DIRECTION_LABELS[direction as keyof typeof DIRECTION_LABELS]}
                    </td>
                    <td style={{
                      padding: '12px 16px',
                      fontSize: '14px',
                      color: '#1f2937',
                      textAlign: 'right',
                      fontFamily: 'monospace'
                    }}>
                      {formatTrafficVolume(volume)}
                    </td>
                    <td style={{
                      padding: '12px 16px',
                      fontSize: '14px',
                      color: '#1f2937',
                      textAlign: 'right',
                      fontFamily: 'monospace'
                    }}>
                      {percentage}%
                    </td>
                    <td style={{
                      padding: '12px 16px',
                      textAlign: 'center'
                    }}>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '9999px',
                        fontSize: '12px',
                        fontWeight: '500',
                        backgroundColor: isHighVolume ? '#fee2e2' : '#dcfce7',
                        color: isHighVolume ? '#991b1b' : '#166534'
                      }}>
                        {isHighVolume ? (t("reports.high") || "Alto") : (t("reports.normal") || "Normal")}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};