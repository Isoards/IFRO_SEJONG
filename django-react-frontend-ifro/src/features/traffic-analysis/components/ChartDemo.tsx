import React, { useState } from "react";
import { debugLog } from "../../../shared/utils/debugUtils";
import {
  TrafficVolumeBarChart,
  TrafficTimeLineChart,
  TrafficAnalysisChart,
  ResponsiveTrafficChart,
  ChartType,
} from "./index";
import {
  TrafficVolumeData,
  TrafficData,
} from "../../../shared/types/global.types";

// Sample data for demonstration
const sampleVolumeData: TrafficVolumeData = {
  N: 1250,
  S: 980,
  E: 1450,
  W: 1120,
};

const sampleTimeData: TrafficData[] = [
  { hour: "06:00", volume: 450, speed: 45 },
  { hour: "07:00", volume: 850, speed: 35 },
  { hour: "08:00", volume: 1200, speed: 25 },
  { hour: "09:00", volume: 950, speed: 40 },
  { hour: "10:00", volume: 750, speed: 50 },
  { hour: "11:00", volume: 680, speed: 55 },
  { hour: "12:00", volume: 920, speed: 45 },
  { hour: "13:00", volume: 1100, speed: 35 },
  { hour: "14:00", volume: 1350, speed: 30 },
  { hour: "15:00", volume: 1450, speed: 25 },
  { hour: "16:00", volume: 1600, speed: 20 },
  { hour: "17:00", volume: 1750, speed: 18 },
  { hour: "18:00", volume: 1650, speed: 22 },
  { hour: "19:00", volume: 1200, speed: 35 },
  { hour: "20:00", volume: 850, speed: 45 },
  { hour: "21:00", volume: 600, speed: 55 },
];

export const ChartDemo: React.FC = () => {
  const [selectedChart, setSelectedChart] = useState<ChartType>("bar");
  const [generatedImages, setGeneratedImages] = useState<
    Record<string, string>
  >({});

  const handleChartReady = (chartType: string) => (imageData: string) => {
    setGeneratedImages((prev) => ({
      ...prev,
      [chartType]: imageData,
    }));
    debugLog(
      `Chart image generated for ${chartType}:`,
      imageData.substring(0, 50) + "..."
    );
  };

  const downloadImage = (chartType: string) => {
    const imageData = generatedImages[chartType];
    if (!imageData) return;

    const link = document.createElement("a");
    link.download = `traffic-chart-${chartType}.png`;
    link.href = imageData;
    link.click();
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-8 text-center">
        Demostración de Componentes de Gráficos de Tráfico
      </h1>

      {/* Chart Type Selector */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">
          Selector de Tipo de Gráfico
        </h2>
        <div className="flex flex-wrap gap-2">
          {(["bar", "line", "combined", "analysis"] as ChartType[]).map(
            (type) => (
              <button
                key={type}
                onClick={() => setSelectedChart(type)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedChart === type
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            )
          )}
        </div>
      </div>

      {/* Responsive Chart Demo */}
      <div className="mb-12">
        <h2 className="text-xl font-semibold mb-4">Gráfico Responsivo</h2>
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <ResponsiveTrafficChart
            volumeData={sampleVolumeData}
            timeData={sampleTimeData}
            chartType={selectedChart}
            onChartReady={handleChartReady(`responsive-${selectedChart}`)}
            responsive={true}
          />
          {generatedImages[`responsive-${selectedChart}`] && (
            <div className="mt-4 text-center">
              <button
                onClick={() => downloadImage(`responsive-${selectedChart}`)}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                Descargar Imagen del Gráfico
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Individual Chart Components */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Bar Chart */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <TrafficVolumeBarChart
            data={sampleVolumeData}
            title="Gráfico de Barras - Volumen por Dirección"
            onChartReady={handleChartReady("bar")}
          />
          {generatedImages["bar"] && (
            <div className="mt-4 text-center">
              <button
                onClick={() => downloadImage("bar")}
                className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
              >
                Descargar
              </button>
            </div>
          )}
        </div>

        {/* Line Chart */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <TrafficTimeLineChart
            data={sampleTimeData}
            title="Gráfico de Líneas - Variación Temporal"
            onChartReady={handleChartReady("line")}
            showVolume={true}
            showSpeed={true}
          />
          {generatedImages["line"] && (
            <div className="mt-4 text-center">
              <button
                onClick={() => downloadImage("line")}
                className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
              >
                Descargar
              </button>
            </div>
          )}
        </div>

        {/* Combined Chart */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <TrafficAnalysisChart
            data={sampleTimeData}
            title="Gráfico Combinado - Análisis Completo"
          />
          {generatedImages["combined"] && (
            <div className="mt-4 p-2 border rounded">
              <img
                src={generatedImages["combined"]}
                alt="Combined Chart Preview"
              />
            </div>
          )}
        </div>

        {/* Volume Only Chart */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <TrafficAnalysisChart
            data={sampleTimeData}
            title="Gráfico de Volumen - Solo Barras"
          />
          {generatedImages["volume-only"] && (
            <div className="mt-4 p-2 border rounded">
              <img
                src={generatedImages["volume-only"]}
                alt="Volume Chart Preview"
              />
            </div>
          )}
        </div>
      </div>

      {/* Data Display */}
      <div className="mt-12 grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h3 className="text-lg font-semibold mb-3">
            Datos de Volumen por Dirección
          </h3>
          <pre className="text-sm text-gray-700 overflow-x-auto">
            {JSON.stringify(sampleVolumeData, null, 2)}
          </pre>
        </div>

        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <h3 className="text-lg font-semibold mb-3">
            Datos Temporales (Muestra)
          </h3>
          <pre className="text-sm text-gray-700 overflow-x-auto max-h-64 overflow-y-auto">
            {JSON.stringify(sampleTimeData.slice(0, 5), null, 2)}
            <div className="text-center text-gray-500 mt-2">
              ... y {sampleTimeData.length - 5} más
            </div>
          </pre>
        </div>
      </div>
    </div>
  );
};
