import React from "react";
import { useTranslation } from "react-i18next";
import { Intersection } from "../../types/global.types";
import { DateTimePicker } from "../common/DateTimePicker";

interface TrafficFlowSidebarProps {
  selectedPoints: Intersection[];
  currentDate: Date;
  setCurrentDate: (date: Date) => void;
  calculateDistance: (point1: Intersection, point2: Intersection) => number;
  calculateTravelTime: (point1: Intersection, point2: Intersection) => number;
}

export const TrafficFlowSidebar: React.FC<TrafficFlowSidebarProps> = ({
  selectedPoints,
  currentDate,
  setCurrentDate,
  calculateDistance,
  calculateTravelTime,
}) => {
  const { t } = useTranslation();

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
                      <p className="text-xs text-gray-500">
                        Coordinates: {selectedPoints[0].latitude.toFixed(4)},{" "}
                        {selectedPoints[0].longitude.toFixed(4)}
                      </p>
                    </div>
                  </div>

                  {/* 연결선 */}
                  <div className="flex justify-center">
                    <div className="w-0.5 h-8 bg-green-500"></div>
                  </div>

                  {/* 끝점 */}
                  <div className="flex items-center space-x-3 p-2 bg-red-50 rounded">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-700">
                        {t("map.endPoint")}
                      </p>
                      <p className="text-xs text-gray-600">
                        {selectedPoints[1].name}
                      </p>
                      <p className="text-xs text-gray-500">
                        Coordinates: {selectedPoints[1].latitude.toFixed(4)},{" "}
                        {selectedPoints[1].longitude.toFixed(4)}
                      </p>
                    </div>
                  </div>

                  {/* 거리 계산 */}
                  <div className="mt-4 p-3 bg-gray-50 rounded">
                    <p className="text-xs text-gray-600 mb-2">
                      {t("map.routeInformation")}
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-500">Distance:</span>
                        <span className="ml-1 font-medium">
                          {calculateDistance(
                            selectedPoints[0],
                            selectedPoints[1]
                          ).toFixed(2)}{" "}
                          km
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Est. Time:</span>
                        <span className="ml-1 font-medium">
                          {calculateTravelTime(
                            selectedPoints[0],
                            selectedPoints[1]
                          )}{" "}
                          min
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-gray-300">
                <h3 className="text-sm font-bold text-gray-700 mb-3">
                  {t("map.selectTwoPointsTitle")}
                </h3>
                <p className="text-xs text-gray-500">
                  {t("map.selectTwoPointsDesc")}
                </p>
                <div className="mt-3 bg-blue-50 p-3 rounded">
                  <p className="text-xs text-blue-700">
                    {t("map.clickFirstPoint")}
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    {t("map.clickSecondPoint")}
                  </p>
                </div>
              </div>
            )}

            {/* 분석 정보 (두 점이 선택된 경우에만) */}
            {selectedPoints.length === 2 && (
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <h3 className="text-sm font-bold text-gray-700 mb-3">
                  {t("map.routeAnalysis")}
                </h3>
                <div className="space-y-3">
                  {/* 통행량 예측 */}
                  <div className="p-3 bg-green-50 rounded">
                    <p className="text-xs font-medium text-green-700 mb-2">
                      {t("map.trafficVolumePrediction")}
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="text-center">
                        <p className="text-lg font-bold text-green-600">
                          {Math.floor(Math.random() * 500 + 800)} vph
                        </p>
                        <p className="text-xs text-gray-500">
                          {t("map.averageVolume")}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-green-600">
                          {Math.floor(Math.random() * 20 + 40)} km/h
                        </p>
                        <p className="text-xs text-gray-500">
                          {t("map.averageSpeed")}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 교통 상황 */}
                  <div className="p-3 bg-yellow-50 rounded">
                    <p className="text-xs font-medium text-yellow-700 mb-2">
                      {t("map.trafficCondition")}
                    </p>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-xs text-gray-600">
                        {t("map.smooth")}
                      </span>
                      <span className="text-xs text-gray-500">
                        ({t("map.estTime")}: 8-12 min)
                      </span>
                    </div>
                  </div>

                  {/* 주의사항 */}
                  <div className="p-3 bg-orange-50 rounded">
                    <p className="text-xs font-medium text-orange-700 mb-2">
                      {t("map.notes")}
                    </p>
                    <ul className="text-xs text-gray-600 space-y-1">
                      <li>• {t("map.congestionExpected")}</li>
                      <li>• {t("map.touristIncrease")}</li>
                      <li>• {t("map.speedChanges")}</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
};
