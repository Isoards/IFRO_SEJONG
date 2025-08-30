import React from 'react';
import { useTranslation } from 'react-i18next';

interface ChartSectionProps {
  chartImage?: string;
  chartTitle?: string;
  chartDescription?: string;
  className?: string;
}

export const ChartSection: React.FC<ChartSectionProps> = ({
  chartImage,
  chartTitle,
  chartDescription,
  className = '',
}) => {
  const { t } = useTranslation();
  
  if (!chartImage) {
    return null;
  }
  
  const defaultTitle = t("reports.trafficDataVisualization") || 'Visualización de Datos de Tráfico';

  return (
    <section className={`mb-8 ${className}`}>
      <h2 className="text-2xl font-semibold text-gray-800 mb-4 border-l-4 border-purple-500 pl-4">
        {t("reports.dataVisualization") || "Visualización de Datos"}
      </h2>
      
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        {/* Chart Header */}
        <div className="bg-purple-50 px-6 py-4 border-b border-purple-200">
          <h3 className="text-lg font-semibold text-gray-800">{chartTitle || defaultTitle}</h3>
          {chartDescription && (
            <p className="text-sm text-gray-600 mt-1">{chartDescription}</p>
          )}
        </div>
        
        {/* Chart Container */}
        <div className="p-6">
          <div className="flex justify-center bg-gray-50 p-4 rounded-lg">
            <img 
              src={chartImage} 
              alt={t("reports.trafficChart") || "Gráfico de Tráfico"}
              className="max-w-full h-auto rounded shadow-lg"
              style={{ maxHeight: '500px', maxWidth: '100%' }}
            />
          </div>
          
          {/* Chart Caption */}
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600">
              <strong>{t("reports.figure1") || "Figura 1"}:</strong> {t("reports.chartCaption") || "Análisis visual de los datos de tráfico del cruce seleccionado. Los gráficos muestran la distribución del volumen de tráfico por dirección y su variación temporal."}
            </p>
          </div>
        </div>
      </div>

      {/* Chart Analysis Notes */}
      <div className="mt-4 bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
        <h4 className="text-md font-semibold text-gray-800 mb-2">{t("reports.visualizationNotes") || "Notas sobre la Visualización"}</h4>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>• {t("reports.dataRepresentsVolume") || "Los datos representan el volumen de tráfico registrado en el período especificado"}</li>
          <li>• {t("reports.directionsNomenclature") || "Las direcciones se muestran según la nomenclatura: NS (Norte-Sur), SN (Sur-Norte), EW (Este-Oeste), WE (Oeste-Este)"}</li>
          <li>• {t("reports.colorsIdentifyPatterns") || "Los colores en el gráfico facilitan la identificación de patrones y tendencias"}</li>
          <li>• {t("reports.visualizationComplements") || "Esta visualización complementa los datos numéricos presentados en las tablas anteriores"}</li>
        </ul>
      </div>
    </section>
  );
};