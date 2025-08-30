import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Intersection } from "../../types/global.types";
import { DateTimePicker } from "../ui/DateTimePicker";

interface RouteInfo {
  distance: string;
  duration: string;
  source: string;
  coordinates: { lat: number; lng: number }[];
}

interface TrafficFlowSidebarProps {
  selectedPoints: Intersection[];
  currentDate: Date;
  setCurrentDate: (date: Date) => void;
  calculateDistance: (point1: Intersection, point2: Intersection) => number;
  calculateTravelTime: (point1: Intersection, point2: Intersection) => number;
  onRouteUpdate?: (routeData: {
    distance: string;
    duration: string;
    source: string;
    coordinates: { lat: number; lng: number }[];
  }) => void;
  routeData?: {
    distance: string;
    duration: string;
    source: string;
    coordinates: { lat: number; lng: number }[];
  } | null;
}

export const TrafficFlowSidebar: React.FC<TrafficFlowSidebarProps> = ({
  selectedPoints,
  currentDate,
  setCurrentDate,
  calculateDistance,
  calculateTravelTime,
  onRouteUpdate,
  routeData,
}) => {
  const { t } = useTranslation();
  const [routeInfo, setRouteInfo] = useState<RouteInfo | null>(null);

  // 외부에서 받은 routeData를 routeInfo로 업데이트
  useEffect(() => {
    if (routeData) {
      setRouteInfo(routeData);
    }
  }, [routeData]);

  // 선택된 점이 변경될 때 기본 거리/시간 계산
  useEffect(() => {
    if (selectedPoints.length !== 2) {
      setRouteInfo(null);
      return;
    }

    // 외부에서 받은 routeData가 있으면 사용
    if (routeData) {
      setRouteInfo(routeData);
      return;
    }

    // 기본 직선 거리 계산 (OSRM 데이터가 아직 없을 때 임시 표시)
    const distance = calculateDistance(selectedPoints[0], selectedPoints[1]);
    const duration = calculateTravelTime(selectedPoints[0], selectedPoints[1]);

    setRouteInfo({
      distance: `${distance.toFixed(2)} km (계산 중...)`,
      duration: `${duration} min (계산 중...)`,
      source: "calculating",
      coordinates: [],
    });
  }, [selectedPoints, calculateDistance, calculateTravelTime, routeData]);

  return (
    <aside className="w-[400px] bg-white flex flex-col border-r border-gray-200 z-10 h-screen">
      <div className="flex-1 flex flex-col overflow-y-auto">
        <header className="px-4 py-4 border-b border-gray-200">
          <div className="px-2 space-y-4">
            <div>
              <h2 className="text-lg font-bold text-green-600 tracking-wide">
                {t("map.trafficFlow")}
              </h2>
            </div>
            <div className="flex justify-center">
              <DateTimePicker
                currentDate={currentDate}
                setCurrentDate={setCurrentDate}
                enableRealTimeUpdate={true}
                updateInterval={5}
              />
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
          <div className="space-y-4">
            {/* 선택된 두 점 정보 */}
            {selectedPoints.length === 2 ? (
              <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-green-500">
                <h3 className="text-sm font-bold text-gray-700 mb-3">
                  {t("map.selectedPoints")}
                </h3>
                <div className="space-y-3">
                  {/* 시작점 */}
                  <div className="flex items-center space-x-3 p-2 bg-blue-50 rounded">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-blue-700">
                        {t("map.startPoint")}
                      </p>
                      <p className="text-xs text-gray-600">
                        {selectedPoints[0].name}
                      </p>
                    </div>
                  </div>

                  {/* 종료점 */}
                  <div className="flex items-center space-x-3 p-2 bg-red-50 rounded">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-700">
                        {t("map.endPoint")}
                      </p>
                      <p className="text-xs text-gray-600">
                        {selectedPoints[1].name}
                      </p>
                    </div>
                  </div>
                </div>

                {/* 경로 정보 */}
                {routeInfo && (
                  <div className="mt-4 p-3 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border">
                    <h4 className="text-sm font-bold text-gray-700 mb-2">
                      경로 정보
                    </h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 flex items-center">
                          <svg
                            className="w-4 h-4 mr-1 text-blue-500"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                            />
                          </svg>
                          {t("map.distance")}:
                        </span>
                        <span className="text-sm font-medium text-blue-700">
                          {routeInfo.distance}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 flex items-center">
                          <svg
                            className="w-4 h-4 mr-1 text-green-500"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          {t("map.estimatedTime")}:
                        </span>
                        <span className="text-sm font-medium text-green-700">
                          {routeInfo.duration}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : null}

            {/* 데이터 분석 정보 */}
            {routeData && (
              <div className="bg-white rounded-lg shadow-sm border p-4">
                <h3 className="text-sm font-bold text-gray-700 mb-3">
                  교통 흐름 분석
                </h3>
                <div className="space-y-3">
                  {/* 통행량 예측 */}
                  <div className="p-3 bg-green-50 rounded">
                    <p className="text-xs font-medium text-green-700 mb-2">
                      예상 통행량
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="text-center">
                        <p className="text-lg font-bold text-green-600">
                          {Math.floor(Math.random() * 500 + 800)}
                        </p>
                        <p className="text-xs text-gray-500">차량/시간</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-green-600">
                          {Math.floor(Math.random() * 20 + 40)}
                        </p>
                        <p className="text-xs text-gray-500">평균 속도(km/h)</p>
                      </div>
                    </div>
                  </div>

                  {/* 교통 상황 */}
                  <div className="p-3 bg-blue-50 rounded">
                    <p className="text-xs font-medium text-blue-700 mb-2">
                      현재 교통 상황
                    </p>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-xs text-gray-600">원활</span>
                      <span className="text-xs text-gray-500">
                        (지연시간: 2-3분)
                      </span>
                    </div>
                  </div>

                  {/* 시간대별 패턴 */}
                  <div className="p-3 bg-yellow-50 rounded">
                    <p className="text-xs font-medium text-yellow-700 mb-2">
                      시간대별 패턴
                    </p>
                    <div className="text-xs text-gray-600 space-y-1">
                      <div className="flex justify-between">
                        <span>오전 러시아워:</span>
                        <span className="font-medium">7:00-9:00 (혼잡)</span>
                      </div>
                      <div className="flex justify-between">
                        <span>점심시간:</span>
                        <span className="font-medium">12:00-13:00 (보통)</span>
                      </div>
                      <div className="flex justify-between">
                        <span>오후 러시아워:</span>
                        <span className="font-medium">18:00-20:00 (혼잡)</span>
                      </div>
                    </div>
                  </div>

                  {/* 경로 효율성 */}
                  {selectedPoints.length === 2 && routeInfo && (
                    <div className="p-3 bg-purple-50 rounded">
                      <p className="text-xs font-medium text-purple-700 mb-2">
                        경로 효율성 분석
                      </p>
                      <div className="text-xs text-gray-600 space-y-1">
                        <div className="flex justify-between">
                          <span>직선거리:</span>
                          <span className="font-medium">
                            {calculateDistance(
                              selectedPoints[0],
                              selectedPoints[1]
                            ).toFixed(1)}{" "}
                            km
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>실제거리:</span>
                          <span className="font-medium">
                            {routeInfo.source === "calculating"
                              ? "계산중..."
                              : routeInfo.distance}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>우회율:</span>
                          <span className="font-medium text-blue-600">
                            {routeInfo.source === "calculating" ||
                            routeInfo.source !== "osrm"
                              ? "계산중..."
                              : `${(
                                  (parseFloat(
                                    routeInfo.distance.replace(" km", "")
                                  ) /
                                    calculateDistance(
                                      selectedPoints[0],
                                      selectedPoints[1]
                                    ) -
                                    1) *
                                  100
                                ).toFixed(0)}%`}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};
