import React, { useRef, useState, useEffect } from "react";
import { debugLog } from "../../../shared/utils/debugUtils";
import { useTranslation } from "react-i18next";
import { Intersection, FavoriteFlow } from "../../../shared/types/global.types";
import { Star, X, Plus, GripVertical } from "lucide-react";
import {
  addTrafficFlowFavorite,
  removeTrafficFlowFavorite,
  recordTrafficFlowAccess,
} from "../../../shared/services/intersections";

interface TrafficFlowDetailPanelProps {
  selectedPoints: Intersection[];
  onClose: () => void;
  onClearAnalysis?: () => void; // 분석 정보와 마커를 지우는 함수
  calculateDistance: (point1: Intersection, point2: Intersection) => number;
  calculateTravelTime: (point1: Intersection, point2: Intersection) => number;
  isFullscreen?: boolean;
  onAddFlowToFavorites?: (flow: FavoriteFlow) => void;
  favoriteFlows?: FavoriteFlow[];
  onWidthIncrease?: () => void;
  onWidthDecrease?: () => void;
  canIncreaseWidth?: boolean;
  canDecreaseWidth?: boolean;
  onWidthChange?: (widthPercentage: number) => void;
  routeData?: {
    distance: string;
    duration: string;
    source: string;
    coordinates: { lat: number; lng: number }[];
  } | null;
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
  onWidthIncrease,
  onWidthDecrease,
  canIncreaseWidth = true,
  canDecreaseWidth = true,
  onWidthChange,
  routeData,
}) => {
  const { t } = useTranslation();

  // 드래그 리사이저 상태
  const [isDragging, setIsDragging] = useState(false);
  const dragStartX = useRef(0);
  const startWidth = useRef(0);

  // 드래그 시작
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!onWidthChange) return;
    setIsDragging(true);
    dragStartX.current = e.clientX;
    startWidth.current = window.innerWidth * 0.35; // 현재 패널 너비 (35% 기본값)
    e.preventDefault();
  };

  // 드래그 중
  const handleMouseMove = React.useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !onWidthChange) return;

      const deltaX = dragStartX.current - e.clientX; // 왼쪽으로 드래그하면 양수
      const newWidth = startWidth.current + deltaX;
      const widthPercentage = Math.max(
        20,
        Math.min(60, (newWidth / window.innerWidth) * 100)
      );

      onWidthChange(widthPercentage);
    },
    [isDragging, onWidthChange]
  );

  // 드래그 종료
  const handleMouseUp = React.useCallback(() => {
    setIsDragging(false);
  }, []);

  // 드래그 이벤트 리스너 등록/해제
  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "ew-resize";
      document.body.style.userSelect = "none";
    } else {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // 중복 호출 방지를 위한 ref (세션 동안 기록된 경로들을 저장)
  const accessRecordedRef = React.useRef<Set<string>>(new Set());

  // 교통 흐름 경로 접근 기록 (컴포넌트가 마운트되고 두 교차로가 선택되었을 때)
  React.useEffect(() => {
    if (selectedPoints.length === 2) {
      const [from, to] = selectedPoints;
      const routeKey = `${from.id}-${to.id}`;

      // 이미 기록된 경로인지 확인 (중복 방지)
      if (accessRecordedRef.current.has(routeKey)) {
        debugLog(`이미 기록된 경로입니다: ${routeKey}`);
        return;
      }

      // 접근 기록 API 호출
      debugLog(`새로운 경로 접근 기록 시작: ${routeKey}`);
      recordTrafficFlowAccess(from.id, to.id)
        .then((result) => {
          debugLog(
            `교통 흐름 경로 접근 기록 완료: ${from.name} → ${to.name}`,
            result
          );
          accessRecordedRef.current.add(routeKey); // 기록 완료 표시
        })
        .catch((error) => {
          console.error("교통 흐름 접근 기록 중 오류:", error);
        });
    }
  }, [selectedPoints]);

  // 현재 플로우가 즐겨찾기에 있는지 확인
  const isCurrentFlowFavorited =
    selectedPoints.length === 2 &&
    favoriteFlows.some(
      (flow) =>
        flow.fromIntersectionId === selectedPoints[0].id &&
        flow.toIntersectionId === selectedPoints[1].id
    );

  // 플로우를 즐겨찾기에 추가하는 함수
  const handleAddFlowToFavorites = async () => {
    if (selectedPoints.length === 2) {
      const [from, to] = selectedPoints;

      try {
        if (isCurrentFlowFavorited) {
          // 즐겨찾기 제거
          debugLog(`즐겨찾기 제거 시도: ${from.id} → ${to.id}`);
          const result = await removeTrafficFlowFavorite(from.id, to.id);
          debugLog(`교통 흐름 즐겨찾기 제거 완료:`, result);
          debugLog(`경로: ${from.name} → ${to.name}`);
        } else {
          // 즐겨찾기 추가
          const routeName = `${from.name} → ${to.name}`;
          debugLog(
            `즐겨찾기 추가 시도: ${from.id} → ${to.id}, 이름: ${routeName}`
          );
          const result = await addTrafficFlowFavorite(
            from.id,
            to.id,
            routeName
          );
          debugLog(`교통 흐름 즐겨찾기 추가 완료:`, result);
          debugLog(`경로: ${routeName}`);
        }

        // 로컬 상태도 업데이트 (Dashboard의 함수 호출)
        if (onAddFlowToFavorites) {
          // routeData가 있고 계산이 완료된 경우 해당 데이터 사용, 없으면 기본 계산 함수 사용
          const distance =
            routeData && routeData.source !== "calculating"
              ? parseFloat(
                  routeData.distance
                    .replace(" km", "")
                    .replace("(계산 중...)", "")
                )
              : calculateDistance(from, to);
          const travelTime =
            routeData && routeData.source !== "calculating"
              ? parseInt(
                  routeData.duration
                    .replace(" min", "")
                    .replace("(계산 중...)", "")
                )
              : calculateTravelTime(from, to);

          const flow: FavoriteFlow = {
            id: Date.now(), // 임시 ID (실제로는 서버에서 생성)
            fromIntersectionId: from.id,
            toIntersectionId: to.id,
            fromIntersectionName: from.name,
            toIntersectionName: to.name,
            distance: distance,
            travelTime: travelTime,
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
      } catch (error) {
        console.error("교통 흐름 즐겨찾기 처리 중 오류:", error);
        alert("즐겨찾기 처리 중 오류가 발생했습니다. 다시 시도해주세요.");
      }
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
    <div className="h-full w-full mx-auto bg-white relative overflow-y-auto flex">
      {/* 드래그 리사이저 */}
      {onWidthChange && (
        <div
          className="absolute left-0 top-0 w-1 h-full bg-gray-300 hover:bg-green-500 cursor-ew-resize flex items-center justify-center transition-colors z-50"
          onMouseDown={handleMouseDown}
          style={{
            background: isDragging ? "#10b981" : undefined,
          }}
        >
          <div className="w-4 h-8 bg-gray-400 hover:bg-green-500 rounded-r flex items-center justify-center">
            <GripVertical size={12} className="text-white" />
          </div>
        </div>
      )}

      <div className="flex-1 p-6 pt-4 overflow-y-auto">
        {/* 드래그 오버레이 */}
        {isDragging && (
          <div className="fixed inset-0 z-40" style={{ cursor: "ew-resize" }} />
        )}

        {/* 헤더 영역 */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold text-green-600 mb-1 truncate">
              {t("map.trafficFlow")} {t("traffic.analysis")}
            </h2>
            <p className="text-xs text-gray-500">
              {selectedPoints.length === 2
                ? `${t("map.routeAnalysis")}: ${selectedPoints[0].name} → ${
                    selectedPoints[1].name
                  }`
                : t("map.selectTwoPointsDesc")}
            </p>
          </div>

          {/* 액션 버튼 그룹 */}
          <div className="flex items-center gap-2 ml-4 flex-shrink-0">
            {/* 즐겨찾기 버튼 */}
            {selectedPoints.length === 2 && (
              <button
                onClick={handleAddFlowToFavorites}
                className={`flex items-center justify-center w-8 h-8 rounded-lg border transition-all duration-200 ${
                  isCurrentFlowFavorited
                    ? "text-yellow-500 bg-yellow-50 hover:bg-yellow-100 border-yellow-400 hover:border-yellow-500"
                    : "text-yellow-400 hover:text-yellow-500 hover:bg-yellow-50 border-yellow-300 hover:border-yellow-400"
                }`}
                title={
                  isCurrentFlowFavorited
                    ? t("favorites.remove") || "즐겨찾기 해제"
                    : t("favorites.addToFavorites") ||
                      "플로우를 즐겨찾기에 추가"
                }
              >
                <Star
                  size={16}
                  fill={isCurrentFlowFavorited ? "currentColor" : "none"}
                />
              </button>
            )}

            {/* 닫기 버튼 */}
            <button
              onClick={handleClose}
              aria-label="Close panel"
              className="flex items-center justify-center w-8 h-8 rounded-lg border border-red-400 text-red-500 hover:text-red-700 hover:bg-red-50 hover:border-red-500 transition-all duration-200"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        {selectedPoints.length === 2 ? (
          <div className="space-y-6">
            {/* 경로 개요 카드 */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-100 rounded-xl p-4">
              <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                {t("map.routeOverview")}
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="bg-white rounded-lg p-3 border border-green-100 shadow-sm">
                  <div className="text-center">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                      {t("map.distance")}
                    </p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {routeData && routeData.source !== "calculating"
                        ? routeData.distance.replace(" km", "")
                        : calculateDistance(
                            selectedPoints[0],
                            selectedPoints[1]
                          ).toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">
                      km{" "}
                      {routeData && routeData.source === "calculating"
                        ? "(계산 중...)"
                        : ""}
                    </p>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-3 border border-green-100 shadow-sm">
                  <div className="text-center">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                      {t("map.estTravelTime")}
                    </p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {routeData && routeData.source !== "calculating"
                        ? routeData.duration.replace(" min", "")
                        : calculateTravelTime(
                            selectedPoints[0],
                            selectedPoints[1]
                          )}
                    </p>
                    <p className="text-xs text-gray-500">
                      min{" "}
                      {routeData && routeData.source === "calculating"
                        ? "(계산 중...)"
                        : ""}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* 시간대별 통행량 예측 카드 */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                {t("map.hourlyTrafficVolume")}
              </h3>
              <div className="space-y-3">
                {[
                  {
                    time: "6-9 AM",
                    volume: Math.floor(Math.random() * 300 + 500),
                    level: "원활",
                  },
                  {
                    time: "9-12 PM",
                    volume: Math.floor(Math.random() * 300 + 400),
                    level: "보통",
                  },
                  {
                    time: "12-3 PM",
                    volume: Math.floor(Math.random() * 300 + 450),
                    level: "보통",
                  },
                  {
                    time: "3-6 PM",
                    volume: Math.floor(Math.random() * 300 + 600),
                    level: "혼잡",
                  },
                  {
                    time: "6-9 PM",
                    volume: Math.floor(Math.random() * 300 + 550),
                    level: "혼잡",
                  },
                  {
                    time: "9-12 AM",
                    volume: Math.floor(Math.random() * 300 + 300),
                    level: "원활",
                  },
                ].map((timeSlot, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {timeSlot.time}
                        </p>
                        <p className="text-xs text-gray-500">
                          {t("map.congestionLevel")}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-green-600">
                          {timeSlot.volume} vph
                        </p>
                        <div className="flex items-center justify-end space-x-1">
                          <div
                            className={`w-2 h-2 rounded-full ${
                              timeSlot.level === "원활"
                                ? "bg-green-500"
                                : timeSlot.level === "보통"
                                ? "bg-yellow-500"
                                : "bg-red-500"
                            }`}
                          ></div>
                          <span className="text-xs text-gray-500">
                            {timeSlot.level}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 교통 패턴 분석 카드 */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                {t("map.trafficPatternAnalysis")}
              </h3>
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-orange-50 to-red-50 border border-orange-100 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-gray-800 mb-3">
                    {t("map.peakHours")}
                  </h4>
                  <div className="flex justify-around">
                    <div className="text-center">
                      <p className="text-xl font-bold text-orange-600">08:00</p>
                      <p className="text-xs text-gray-500">
                        {t("map.morningPeak")}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold text-red-600">18:00</p>
                      <p className="text-xs text-gray-500">
                        {t("map.eveningPeak")}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-gray-800 mb-3">
                    {t("map.weeklyPattern")}
                  </h4>
                  <div className="grid grid-cols-7 gap-2">
                    {["월", "화", "수", "목", "금", "토", "일"].map(
                      (day, index) => {
                        const trafficPercentage = Math.random() * 60 + 40;
                        const trafficValue = Math.floor(trafficPercentage * 10);
                        return (
                          <div key={index} className="text-center">
                            <p className="text-xs text-gray-500 mb-1">{day}</p>
                            <div className="w-full bg-gray-200 rounded-full h-2 mb-1">
                              <div
                                className="bg-green-500 h-2 rounded-full transition-all duration-300"
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

            {/* 대안 경로 카드 */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                {t("map.alternativeRoutes")}
              </h3>
              <div className="space-y-3">
                {/* 현재 선택된 경로를 첫 번째로 표시 */}
                <div className="bg-blue-50 rounded-lg p-4 border-l-4 border-blue-500">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        현재 선택된 경로 (추천)
                      </p>
                      <p className="text-xs text-gray-500">
                        {routeData && routeData.source !== "calculating"
                          ? `${routeData.distance} • ${routeData.duration}`
                          : `${calculateDistance(
                              selectedPoints[0],
                              selectedPoints[1]
                            ).toFixed(1)}km • ${calculateTravelTime(
                              selectedPoints[0],
                              selectedPoints[1]
                            )}분 (계산중...)`}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs px-3 py-1 rounded-full font-medium bg-blue-100 text-blue-700">
                        {routeData && routeData.source === "osrm"
                          ? "원활"
                          : "분석중"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 기타 대안 경로들 */}
                {[
                  {
                    name: t("map.highwayRoute") || "고속도로 경로",
                    distance: 12.5,
                    time: 15,
                    traffic: "원활",
                    color: "green",
                  },
                  {
                    name: t("map.cityRoadRoute") || "시내도로 경로",
                    distance: 8.2,
                    time: 25,
                    traffic: "혼잡",
                    color: "red",
                  },
                  {
                    name: t("map.bypassRoute") || "우회도로 경로",
                    distance: 15.1,
                    time: 18,
                    traffic: "보통",
                    color: "yellow",
                  },
                ].map((route, index) => (
                  <div
                    key={index}
                    className={`bg-gray-50 rounded-lg p-4 border-l-4 ${
                      route.color === "green"
                        ? "border-green-500"
                        : route.color === "red"
                        ? "border-red-500"
                        : "border-yellow-500"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {route.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {route.distance}km • {route.time}분
                        </p>
                      </div>
                      <div className="text-right">
                        <span
                          className={`text-xs px-3 py-1 rounded-full font-medium ${
                            route.color === "green"
                              ? "bg-green-100 text-green-700"
                              : route.color === "red"
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
          <div className="text-center py-12">
            <div className="bg-gray-50 rounded-xl p-8 border border-gray-200">
              <div className="w-16 h-16 bg-gray-200 rounded-full mx-auto mb-4 flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                교차로 선택 필요
              </h3>
              <p className="text-sm text-gray-500">
                {t("map.selectTwoPointsDesc")}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
