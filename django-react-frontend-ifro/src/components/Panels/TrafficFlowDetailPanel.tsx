import React from "react";
import { useTranslation } from "react-i18next";
import { Intersection, FavoriteFlow } from "../../types/global.types";
import { Star } from "lucide-react";

interface TrafficFlowDetailPanelProps {
  selectedPoints: Intersection[];
  onClose: () => void;
  onClearAnalysis?: () => void; // 분석 정보와 마커를 지우는 함수
  calculateDistance: (point1: Intersection, point2: Intersection) => number;
  calculateTravelTime: (point1: Intersection, point2: Intersection) => number;
  isFullscreen?: boolean;
  onAddFlowToFavorites?: (flow: FavoriteFlow) => void;
  favoriteFlows?: FavoriteFlow[];
}

export const TrafficFlowDetailPanel: React.FC<TrafficFlowDetailPanelProps> = ({
  selectedPoints,
  onClose,
  onClearAnalysis,
  calculateDistance,
  calculateTravelTime,
  isFullscreen = false,
  onAddFlowToFavorites,
  favoriteFlows = [],
}) => {
  const { t } = useTranslation();

  // 현재 플로우가 즐겨찾기에 있는지 확인
  const isCurrentFlowFavorited =
    selectedPoints.length === 2 &&
    favoriteFlows.some(
      (flow) =>
        flow.fromIntersectionId === selectedPoints[0].id &&
        flow.toIntersectionId === selectedPoints[1].id
    );

  // 플로우를 즐겨찾기에 추가하는 함수
  const handleAddFlowToFavorites = () => {
    if (onAddFlowToFavorites && selectedPoints.length === 2) {
      const [from, to] = selectedPoints;

      const flow: FavoriteFlow = {
        id: Date.now(), // 임시 ID (실제로는 서버에서 생성)
        fromIntersectionId: from.id,
        toIntersectionId: to.id,
        fromIntersectionName: from.name,
        toIntersectionName: to.name,
        distance: calculateDistance(from, to),
        travelTime: calculateTravelTime(from, to),
        dateTime: new Date().toISOString(),
        createdAt: new Date().toISOString(),
        flowData: {
          averageVolume: Math.floor(Math.random() * 1000) + 500, // 임시 데이터
          averageSpeed: Math.floor(Math.random() * 20) + 30, // 임시 데이터
          trafficFlow: Math.floor(Math.random() * 100) + 50, // 임시 데이터
        },
      };
      onAddFlowToFavorites(flow);
    }
  };

  // Close 버튼 클릭 시 분석 정보와 마커를 지우는 함수
  const handleClose = () => {
    if (onClearAnalysis) {
      onClearAnalysis(); // 분석 정보와 마커 지우기
    }
    onClose(); // 패널 닫기
  };

  return (
    <div className="h-full w-full max-w-2xl mx-auto p-4 pt-3 bg-white relative overflow-y-auto">
      {/* 헤더 영역 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex-1">
          <h2 className="text-xl font-bold text-green-600 mb-1">
            {t("map.trafficFlow")} {t("traffic.analysis")}
          </h2>
          <p className="text-sm text-gray-600">
            {selectedPoints.length === 2
              ? `${t("map.routeAnalysis")}: ${selectedPoints[0].name} → ${
                  selectedPoints[1].name
                }`
              : t("map.selectTwoPointsDesc")}
          </p>
        </div>
        {/* 버튼 영역 */}
        <div className="flex items-center space-x-1 ml-4">
          {onAddFlowToFavorites && selectedPoints.length === 2 && (
            <button
              onClick={handleAddFlowToFavorites}
              className={`inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
                isCurrentFlowFavorited
                  ? "bg-primary text-primary-foreground hover:bg-primary/90 text-yellow-400"
                  : "hover:bg-accent hover:text-accent-foreground text-gray-400"
              }`}
              title={
                isCurrentFlowFavorited
                  ? "즐겨찾기 해제"
                  : "플로우를 즐겨찾기에 추가"
              }
            >
              <Star
                size={16}
                fill={isCurrentFlowFavorited ? "currentColor" : "none"}
              />
            </button>
          )}
          <button
            onClick={handleClose}
            aria-label="Close panel"
            className="inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground"
          >
            <svg
              className="w-4 h-4 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      {selectedPoints.length === 2 ? (
        <div className="space-y-4">
          {/* 경로 개요 */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-base font-semibold text-gray-800 mb-3">
              {t("map.routeOverview")}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <p className="text-xs text-gray-500">{t("map.distance")}</p>
                <p className="text-lg font-bold text-green-600">
                  {calculateDistance(
                    selectedPoints[0],
                    selectedPoints[1]
                  ).toFixed(2)}{" "}
                  km
                </p>
              </div>
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <p className="text-xs text-gray-500">
                  {t("map.estTravelTime")}
                </p>
                <p className="text-lg font-bold text-blue-600">
                  {calculateTravelTime(selectedPoints[0], selectedPoints[1])}{" "}
                  min
                </p>
              </div>
            </div>
          </div>

          {/* 시간대별 통행량 예측 */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-base font-semibold text-gray-800 mb-3">
              {t("map.hourlyTrafficVolume")}
            </h3>
            <div className="space-y-2">
              {[
                "6-9 AM",
                "9-12 PM",
                "12-3 PM",
                "3-6 PM",
                "6-9 PM",
                "9-12 AM",
              ].map((timeSlot, index) => (
                <div key={index} className="p-3 bg-white rounded-lg shadow-sm">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-xs font-medium text-gray-800">
                        {timeSlot}
                      </p>
                      <p className="text-xs text-gray-500">
                        {t("map.congestionLevel")}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-green-600">
                        {Math.floor(Math.random() * 300 + 500)} vph
                      </p>
                      <div className="flex items-center space-x-1">
                        <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                        <span className="text-xs text-gray-500">Smooth</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 교통 패턴 분석 */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-base font-semibold text-gray-800 mb-3">
              {t("map.trafficPatternAnalysis")}
            </h3>
            <div className="space-y-3">
              <div className="p-3 bg-white rounded-lg shadow-sm">
                <h4 className="text-xs font-medium text-gray-800 mb-2">
                  {t("map.peakHours")}
                </h4>
                <div className="flex space-x-4">
                  <div className="text-center">
                    <p className="text-sm font-bold text-orange-600">08:00</p>
                    <p className="text-xs text-gray-500">
                      {t("map.morningPeak")}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-red-600">18:00</p>
                    <p className="text-xs text-gray-500">
                      {t("map.eveningPeak")}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-white rounded-lg shadow-sm">
                <h4 className="text-xs font-medium text-gray-800 mb-2">
                  {t("map.weeklyPattern")}
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-2">
                  {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(
                    (day, index) => {
                      const trafficPercentage = Math.random() * 60 + 40;
                      const trafficValue = Math.floor(trafficPercentage * 10); // 400-1000 범위의 값
                      return (
                        <div key={index} className="text-center">
                          <p className="text-xs text-gray-500 mb-1">{day}</p>
                          <div className="w-full bg-gray-200 rounded-full h-1.5 mb-1">
                            <div
                              className="bg-green-500 h-1.5 rounded-full"
                              style={{
                                width: `${trafficPercentage}%`,
                              }}
                            ></div>
                          </div>
                          <p className="text-xs font-medium text-gray-700">
                            {trafficValue}
                          </p>
                        </div>
                      );
                    }
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 대안 경로 */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h3 className="text-base font-semibold text-gray-800 mb-3">
              {t("map.alternativeRoutes")}
            </h3>
            <div className="space-y-2">
              {[
                {
                  name: t("map.highwayRoute"),
                  distance: 12.5,
                  time: 15,
                  traffic: t("map.smooth"),
                },
                {
                  name: t("map.cityRoadRoute"),
                  distance: 8.2,
                  time: 25,
                  traffic: t("map.congested"),
                },
                {
                  name: t("map.bypassRoute"),
                  distance: 15.1,
                  time: 18,
                  traffic: t("map.moderate"),
                },
              ].map((route, index) => (
                <div
                  key={index}
                  className="p-3 bg-white rounded-lg shadow-sm border-l-4 border-blue-500"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-xs font-medium text-gray-800">
                        {route.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {route.distance}km • {route.time}min
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          route.traffic === "Smooth" ||
                          route.traffic === t("map.smooth")
                            ? "bg-green-100 text-green-700"
                            : route.traffic === "Congested" ||
                              route.traffic === t("map.congested")
                            ? "bg-red-100 text-red-700"
                            : "bg-yellow-100 text-yellow-700"
                        }`}
                      >
                        {route.traffic}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-6">
          <p className="text-sm text-gray-500">
            {t("map.selectTwoPointsDesc")}
          </p>
        </div>
      )}
    </div>
  );
};
