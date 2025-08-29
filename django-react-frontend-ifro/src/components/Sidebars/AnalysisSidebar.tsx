import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Search, Star } from "lucide-react";
import { Intersection } from "../../types/global.types";
import { DateTimePicker } from "../common/DateTimePicker";
import { MiniChart } from "../common/MiniChart";
import CalendarModal from "../common/CalendarModal";
import { Button } from "../common/Button";

interface AnalysisSidebarProps {
  selectedIntersection: Intersection | null;
  onIntersectionClick: (intersection: Intersection) => void;
  currentDate: Date;
  setCurrentDate: (date: Date) => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  intersections: Intersection[];
  activeNav: string;
  favoriteIntersections: number[];
  onToggleFavorite: (intersectionId: number) => void;
}

export const AnalysisSidebar: React.FC<AnalysisSidebarProps> = ({
  selectedIntersection,
  onIntersectionClick,
  currentDate,
  setCurrentDate,
  searchTerm,
  setSearchTerm,
  intersections,
  activeNav,
  favoriteIntersections,
  onToggleFavorite,
}) => {
  const { t } = useTranslation();
  const [encryptionEnabled, setEncryptionEnabled] = useState(false);
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  const [visibleCount, setVisibleCount] = useState(10); // 초기 10개만 표시
  const [isLoading, setIsLoading] = useState(false);
  const [isNowMode, setIsNowMode] = useState(false);
  // 각 교차로별 chartData를 필요할 때만 관리
  const [chartDataMap, setChartDataMap] = useState<
    Record<number, { hour: string; speed: number; volume: number }[]>
  >({});

  useEffect(() => {
    const updateEncryptionStatus = () => {
      const savedEncryption = localStorage.getItem("encryptionEnabled");
      setEncryptionEnabled(savedEncryption === "true");
    };

    updateEncryptionStatus(); // Initial check

    window.addEventListener("storage", updateEncryptionStatus); // Listen for changes

    return () => {
      window.removeEventListener("storage", updateEncryptionStatus); // Clean up
    };
  }, []);

  const formatFullDate = (date: Date) => {
    const yyyy = date.getFullYear();
    const mm = (date.getMonth() + 1).toString().padStart(2, "0");
    const dd = date.getDate().toString().padStart(2, "0");
    const hh = date.getHours().toString().padStart(2, "0");
    const min = isNowMode
      ? date.getMinutes().toString().padStart(2, "0")
      : (Math.floor(date.getMinutes() / 5) * 5).toString().padStart(2, "0");
    return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
  };

  // NOW 버튼 클릭 핸들러
  const handleStartNowMode = () => {
    if (isNowMode) {
      // 이미 NOW 모드일 때는 해제
      setIsNowMode(false);
    } else {
      // NOW 모드 활성화
      setIsNowMode(true);
      const now = new Date();
      setCurrentDate(now);
    }
  };

  // 날짜 범위 선택 핸들러
  const handleDateRangeSelect = (startDate: Date, endDate: Date) => {
    setCurrentDate(startDate);
    setIsCalendarOpen(false);
    // NOW 모드는 오직 NOW 버튼으로만 해제
  };

  // 즐겨찾기 모드에 따른 교차로 필터링
  const getFilteredIntersections = () => {
    let points = intersections;

    // 즐겨찾기 모드일 때는 즐겨찾기된 교차로만 표시
    if (activeNav === "favorites") {
      points = intersections.filter((intersection) =>
        favoriteIntersections.includes(intersection.id)
      );
    }

    // 검색어 필터링
    return points.filter((intersection) =>
      intersection.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const filteredIntersections = getFilteredIntersections();

  // 현재 보여줄 교차로들만 필터링 (선택된 항목을 최상단으로)
  const visibleIntersections = useMemo(() => {
    let items = filteredIntersections.slice(0, visibleCount);

    // 선택된 교차로가 있고 현재 visible 범위에 없다면, 맨 위에 추가
    if (selectedIntersection) {
      const isInVisible = items.some(
        (item) => item.id === selectedIntersection.id
      );
      if (!isInVisible) {
        // 선택된 항목이 filteredIntersections에 있는지 확인
        const selectedExists = filteredIntersections.some(
          (item) => item.id === selectedIntersection.id
        );
        if (selectedExists) {
          // 선택된 항목을 맨 위에 추가하고, 중복 제거
          items = [
            selectedIntersection,
            ...items.filter((item) => item.id !== selectedIntersection.id),
          ];
        }
      }
    }

    return items;
  }, [filteredIntersections, visibleCount, selectedIntersection]);

  // 무한 스크롤 로직
  const loadMore = useCallback(() => {
    if (visibleCount < filteredIntersections.length && !isLoading) {
      setIsLoading(true);
      setTimeout(() => {
        setVisibleCount((prev) =>
          Math.min(prev + 10, filteredIntersections.length)
        );
        setIsLoading(false);
      }, 100); // 부드러운 로딩을 위한 지연
    }
  }, [visibleCount, filteredIntersections.length, isLoading]);

  // 스크롤 이벤트 핸들러
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
      if (scrollHeight - scrollTop <= clientHeight * 1.5) {
        loadMore();
      }
    },
    [loadMore]
  );

  // 각 교차로별로 데이터가 없으면 useEffect로 생성
  useEffect(() => {
    const newChartData: Record<
      number,
      { hour: string; speed: number; volume: number }[]
    > = {};
    visibleIntersections.forEach((intersection) => {
      if (!chartDataMap[intersection.id]) {
        const arr = Array.from({ length: 24 }, (_, i) => ({
          hour: `${i}:00`,
          speed: 0,
          volume: Math.floor(1000 + Math.random() * 2000),
        }));
        newChartData[intersection.id] = arr;
      }
    });

    if (Object.keys(newChartData).length > 0) {
      setChartDataMap((prev) => ({ ...prev, ...newChartData }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visibleIntersections, currentDate]);

  // 검색어나 필터 변경 시 visibleCount 리셋
  useEffect(() => {
    setVisibleCount(10);
  }, [searchTerm, activeNav]);

  // NOW 모드일 때 실시간 업데이트
  useEffect(() => {
    if (!isNowMode) return;

    const interval = setInterval(() => {
      const now = new Date();
      // NOW 모드일 때는 부모의 setCurrentDate를 직접 호출하지 않고 내부적으로만 업데이트
      setCurrentDate(now);
    }, 1000); // 1초마다 업데이트

    return () => clearInterval(interval);
  }, [isNowMode, setCurrentDate]);

  // 헤더 제목 결정 (현재 사용하지 않음)
  // const getHeaderTitle = () => {
  //   if (activeNav === "favorites") {
  //     return "Favorites";
  //   }
  //   return "Intersection Analysis";
  // };

  return (
    <aside className="w-[400px] bg-white flex flex-col border-r border-gray-200 z-10 h-screen">
      <div className="flex-1 flex flex-col overflow-y-auto">
        <header className="px-4 py-4 border-b border-gray-200">
          <div className="px-2 space-y-4">
            <div>
              <h2 className="text-lg font-bold text-blue-600 tracking-wide">
                {t("traffic.analysis")}
              </h2>
              <p className="text-xs text-gray-500">
                Encryption Enabled: {encryptionEnabled ? "On" : "Off"}
              </p>
            </div>
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                size={20}
              />
              <input
                type="text"
                placeholder={
                  activeNav === "favorites"
                    ? t("common.search") +
                      " " +
                      t("navigation.favorites") +
                      "..."
                    : t("common.search") + "..."
                }
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-gray-100 border-transparent rounded-md py-2 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            <div className="flex justify-between items-center gap-2">
              <p className="text-m font-bold text-gray-700 tracking-wide whitespace-nowrap flex-shrink-0 min-w-0">
                {formatFullDate(currentDate)}
              </p>
              <div className="flex gap-1">
                <Button
                  variant={isNowMode ? "default" : "outline"}
                  size="sm"
                  onClick={handleStartNowMode}
                  className={`text-xs px-3 py-1.5 flex-shrink-0 font-semibold transition-all duration-200 ${
                    isNowMode
                      ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-md hover:shadow-lg transform hover:scale-105 border-0"
                      : "border-gray-300 text-gray-600 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50"
                  }`}
                >
                  {isNowMode ? (
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                      NOW
                    </span>
                  ) : (
                    "NOW"
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCalendarOpen(true)}
                  disabled={isNowMode}
                  className={`text-xs px-2 py-1 flex-shrink-0 transition-all duration-200 ${
                    isNowMode
                      ? "border-gray-200 text-gray-400 cursor-not-allowed opacity-50"
                      : "border-gray-300 text-gray-600 hover:border-gray-400 hover:text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  {t("navigation.settings")}
                </Button>
              </div>
            </div>
            {activeNav === "map" && (
              <div className="flex justify-center pt-2">
                <DateTimePicker
                  currentDate={currentDate}
                  setCurrentDate={setCurrentDate}
                  enableRealTimeUpdate={isNowMode}
                  updateInterval={5}
                  isNowMode={isNowMode}
                />
              </div>
            )}
          </div>
        </header>

        <div
          className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50"
          onScroll={handleScroll}
        >
          <div className="flex justify-between items-center mb-2">
            {activeNav === "favorites" && (
              <span className="text-xs text-gray-400 px-2">
                {visibleIntersections.length} / {filteredIntersections.length}{" "}
                items
              </span>
            )}
          </div>

          {filteredIntersections.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {activeNav === "favorites" ? (
                <div>
                  <Star className="mx-auto mb-2 text-gray-300" size={32} />
                  <p className="text-sm">No favorites yet</p>
                  <p className="text-xs mt-1">
                    Click the star icon to add favorites
                  </p>
                </div>
              ) : (
                <p className="text-sm">No intersections found</p>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {visibleIntersections.map((intersection) => {
                const isSelected = selectedIntersection?.id === intersection.id;
                return (
                  <div
                    key={intersection.id}
                    id={`intersection-${intersection.id}`}
                  >
                    <div
                      className={`bg-white rounded-lg shadow-sm cursor-pointer transition-all border-l-4 ${
                        isSelected
                          ? "border-blue-500 bg-blue-50"
                          : "border-transparent hover:bg-gray-100"
                      }`}
                      onClick={() => onIntersectionClick(intersection)}
                    >
                      {/* Header Section */}
                      <div className="p-3 border-b border-gray-100">
                        <div className="flex items-center">
                          <h4
                            className="font-bold text-sm text-gray-800 break-words whitespace-normal"
                            style={{ overflowWrap: "break-word" }}
                          >
                            {intersection.name}
                          </h4>
                        </div>
                      </div>
                      {/* Content Section */}
                      <div className="p-3">
                        <div className="mt-2 w-full h-24 rounded-lg bg-gray-100 flex items-center justify-center">
                          <div className="w-full h-full">
                            <MiniChart
                              data={chartDataMap[intersection.id] || []}
                              dataKey="volume"
                              color="rgba(59,130,246,0.4)"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* 로딩 인디케이터 */}
              {isLoading && (
                <div className="text-center py-4">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                  <p className="text-xs text-gray-500 mt-2">Loading more...</p>
                </div>
              )}

              {/* 더 이상 로드할 항목이 없을 때 */}
              {visibleCount >= filteredIntersections.length &&
                filteredIntersections.length > 0 && (
                  <div className="text-center py-4">
                    <p className="text-xs text-gray-400">All items loaded</p>
                  </div>
                )}
            </div>
          )}
        </div>
        <CalendarModal
          isOpen={isCalendarOpen}
          onClose={() => setIsCalendarOpen(false)}
          onDateRangeSelect={handleDateRangeSelect}
        />
      </div>
    </aside>
  );
};
