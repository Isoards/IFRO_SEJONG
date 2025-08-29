import React, { useState, useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { NavBar } from "../Navigation/NavBar";
import { AnalysisSidebar } from "../Sidebars/AnalysisSidebar";
import { FavoritesSidebar } from "../Sidebars/FavoritesSidebar";
import { TrafficFlowSidebar } from "../Sidebars/TrafficFlowSidebar";
import { IncidentSidebar } from "../Sidebars/IncidentSidebar";
import { GoogleMapWrapper } from "./GoogleMapWrapper";
import { IntersectionDetailPanel } from "../Panels/IntersectionDetailPanel";
import { IncidentDetailPanel } from "../Panels/IncidentDetailPanel";
import { TrafficFlowDetailPanel } from "../Panels/TrafficFlowDetailPanel";
import { TableauDashboard } from "../Panels/TableauDashboard";
import { Intersection, Incident } from "../../types/global.types";
import { Map as MapIcon, Star } from "lucide-react";
import {
  getTrafficIntersections,
  getIntersectionTrafficStat,
  getLatestIntersectionTrafficData, // 1. API 함수 import
} from "../../api/intersections";
import { getIncidents } from "../../api/incidents";
import { calculateAllIntersectionTraffic } from "../../utils/intersectionUtils";
import { ChatBotButton } from "../common/ChatBotButton";
import { debugLog } from "../../utils/debugUtils";

export default function Dashboard() {
  const { t } = useTranslation();
  const [selectedIntersection, setSelectedIntersection] =
    useState<Intersection | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(
    null
  );
  const [intersections, setIntersections] = useState<Intersection[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [activeNav, setActiveNav] = useState("map");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [searchTerm, setSearchTerm] = useState("");
  const [favoriteIntersections, setFavoriteIntersections] = useState<number[]>(
    []
  );
  const [favoriteIncidents] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [trafficStat, setTrafficStat] = useState<any>(null);
  const [trafficChartData, setTrafficChartData] = useState<any[]>([]); // 2. 차트 데이터 상태 추가

  // 교차로 간 통행량 데이터 상태
  const [intersectionTrafficData, setIntersectionTrafficData] = useState<
    Array<{
      source: Intersection;
      nearest: Intersection[];
      trafficData: Array<{
        target: Intersection;
        distance: number;
        averageVolume: number;
        averageSpeed: number;
        trafficFlow: number;
      }>;
    }>
  >([]);

  // 세분화 버튼 상태 관리
  const [activeTrafficView, setActiveTrafficView] = useState<
    "analysis" | "flow" | "incidents" | "favorites"
  >("analysis");
  const [selectedPoints, setSelectedPoints] = useState<Intersection[]>([]);

  // 뷰 변경 핸들러 - 뷰 변경 시 선택된 점들 초기화
  const handleTrafficViewChange = useCallback(
    (view: "analysis" | "flow" | "incidents" | "favorites") => {
      debugLog.log(
        `Traffic view changing from ${activeTrafficView} to ${view}`
      );
      setActiveTrafficView(view);

      // 교차로 간 뷰가 아닌 다른 뷰(analysis, incidents, favorites)로 전환할 때 선택된 점들 초기화
      if (view === "analysis" || view === "incidents" || view === "favorites") {
        debugLog.log(`Clearing selected points for ${view} view`);
        setSelectedPoints([]);
      }

      // 단순 교차로 뷰로 전환할 때 선택된 교차로 초기화
      if (view === "analysis") {
        setSelectedIntersection(null);
      }
    },
    [activeTrafficView]
  );

  // activeTrafficView가 변경될 때 선택된 항목들과 패널 상태 초기화
  useEffect(() => {
    if (activeTrafficView === "analysis") {
      setSelectedIntersection(null);
      setSelectedIncident(null);
      setShowIntersectionPanel(false);
      setShowIncidentPanel(false);
      setShowRoutePanel(false);
    } else if (activeTrafficView === "incidents") {
      setSelectedIntersection(null);
      setSelectedPoints([]);
      setShowIntersectionPanel(false);
      setShowRoutePanel(false);
    } else if (activeTrafficView === "favorites") {
      setSelectedPoints([]);
      setShowRoutePanel(false);
    } else if (activeTrafficView === "flow") {
      setSelectedIntersection(null);
      setSelectedIncident(null);
      setShowIntersectionPanel(false);
      setShowIncidentPanel(false);
    }
    // 다른 뷰로 전환할 때 선택된 점들 초기화
    if (activeTrafficView !== "flow") {
      setSelectedPoints([]);
    }
  }, [activeTrafficView]);

  // 교차로 데이터 로드
  useEffect(() => {
    const loadIntersections = async () => {
      try {
        const data = await getTrafficIntersections();
        setIntersections(data);

        // 교차로 간 통행량 데이터 계산
        // if (data.length > 0) {
        //   const trafficData = calculateAllIntersectionTraffic(data);
        //   setIntersectionTrafficData(trafficData);
        //   // 초기값은 아무것도 선택하지 않음
        // }
      } catch (error) {
        console.error("교차로 데이터 로드 실패:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadIntersections();
  }, []);

  // 사고 데이터 로드
  useEffect(() => {
    let mounted = true;

    const loadIncidents = async () => {
      try {
        const data = await getIncidents();
        if (mounted) {
          console.log("Loaded incidents:", data);
          setIncidents(data);
        }
      } catch (error) {
        if (mounted) {
          console.error("Failed to load incident data:", error);
        }
      }
    };

    loadIncidents();
    return () => {
      mounted = false;
    };
  }, []);

  // 로컬 스토리지에서 즐겨찾기 불러오기 (초기화 시)
  useEffect(() => {
    const savedFavorites = localStorage.getItem("favoriteIntersections");
    if (savedFavorites) {
      setFavoriteIntersections(JSON.parse(savedFavorites));
    }
  }, []);

  // 즐겨찾기 변경 시 로컬 스토리지에 저장
  useEffect(() => {
    localStorage.setItem(
      "favoriteIntersections",
      JSON.stringify(favoriteIntersections)
    );
  }, [favoriteIntersections]);

  // 즐겨찾기 토글 함수
  const handleToggleFavorite = useCallback((intersectionId: number) => {
    setFavoriteIntersections((prev) => {
      if (prev.includes(intersectionId)) {
        return prev.filter((id) => id !== intersectionId);
      } else {
        return [...prev, intersectionId];
      }
    });
  }, []);

  // 사고 즐겨찾기 토글 함수 (현재 사용하지 않음)
  // const handleToggleFavoriteIncident = useCallback((incidentId: number) => {
  //   setFavoriteIncidents((prev) => {
  //     if (prev.includes(incidentId)) {
  //       return prev.filter((id) => id !== incidentId);
  //     } else {
  //       return [...prev, incidentId];
  //     }
  //   });
  // }, []);

  const handleIntersectionClick = useCallback(
    async (intersection: Intersection) => {
      setSelectedIntersection(intersection);
      setSelectedIncident(null); // 교차로 선택 시 incident 선택 해제

      // 교통 통계 데이터 로드
      try {
        const datetime = intersection.datetime || new Date().toISOString();
        console.log(
          `Loading traffic stats for intersection ${intersection.id} at ${datetime}`
        );
        const stats = await getIntersectionTrafficStat(
          intersection.id,
          datetime
        );
        console.log("Loaded traffic stats:", stats);
        setTrafficStat(stats);

        // 3. 최근 10개 데이터 로드 로직 추가
        const chartData = await getLatestIntersectionTrafficData(
          intersection.id,
          10
        );
        setTrafficChartData(chartData);
      } catch (error) {
        console.error("Failed to load traffic stats or chart data:", error);
        setTrafficStat(null);
        setTrafficChartData([]); // 에러 발생 시 차트 데이터 초기화
      }

      // 사이드바에서 해당 항목으로 스크롤
      setTimeout(() => {
        const element = document.getElementById(
          `intersection-${intersection.id}`
        );
        if (element) {
          element.scrollIntoView({
            behavior: "smooth",
            block: "center",
            inline: "nearest",
          });
          // 잠시 강조 효과
          element.style.transition = "background-color 0.3s ease";
          element.style.backgroundColor = "#fef3c7"; // 노란색 강조
          setTimeout(() => {
            element.style.backgroundColor = "";
          }, 1500);
        }
      }, 100); // 다시 100ms로 단축 (선택된 항목이 이제 항상 맨 위에 있음)
    },
    []
  );

  const [incidentMapCenter, setIncidentMapCenter] = useState<{
    lat: number;
    lng: number;
  } | null>(null);

  const handleIncidentClick = useCallback(
    (incident: Incident) => {
      setSelectedIncident(incident);
      setSelectedIntersection(null); // incident 선택 시 교차로 선택 해제

      // 사이드바에서 해당 항목으로 스크롤
      setTimeout(() => {
        const element = document.getElementById(`incident-${incident.id}`);
        if (element) {
          element.scrollIntoView({
            behavior: "smooth",
            block: "center",
            inline: "nearest",
          });
          // 잠시 강조 효과
          element.style.transition = "background-color 0.3s ease";
          element.style.backgroundColor = "#fef3c7"; // 노란색 강조
          setTimeout(() => {
            element.style.backgroundColor = "";
          }, 1500);
        }
      }, 100);

      // 위경도 정보로 지도 이동
      let lat = incident.latitude;
      let lng = incident.longitude;
      if (
        (lat === undefined || lng === undefined) &&
        intersections.length > 0
      ) {
        const found = intersections.find(
          (i) => i.name === incident.intersection_name
        );
        if (found) {
          lat = found.latitude;
          lng = found.longitude;
        }
      }
      if (lat !== undefined && lng !== undefined) {
        setIncidentMapCenter({ lat, lng });
      }
    },
    [intersections]
  );

  // 네비게이션 변경 시 검색어 초기화
  const handleNavChange = useCallback((nav: string) => {
    setActiveNav(nav);
    setSearchTerm("");

    // tableau로 변경할 때 모든 detail panel 닫기
    if (nav === "tableau") {
      setShowIntersectionPanel(false);
      setShowIncidentPanel(false);
      setShowRoutePanel(false);
      setTimeout(() => {
        setSelectedIntersection(null);
        setSelectedIncident(null);
        setSelectedPoints([]);
      }, 300);
    }
  }, []);

  // detail panel을 즉시 닫는 함수
  const handleCloseDetailPanels = useCallback(() => {
    setShowIntersectionPanel(false);
    setShowIncidentPanel(false);
    setShowRoutePanel(false);
    setTimeout(() => {
      setSelectedIntersection(null);
      setSelectedIncident(null);
      setSelectedPoints([]);
    }, 300);
  }, []);

  const [isDetailPanelFullscreen] = useState(false);

  useEffect(() => {
    if (selectedIntersection && currentDate) {
      const fetchStat = async () => {
        const isoDate = currentDate.toISOString();
        const stat = await getIntersectionTrafficStat(
          selectedIntersection.id,
          isoDate
        );
        setTrafficStat(
          stat
            ? {
                average_speed: stat.average_speed ?? null,
                total_volume: stat.total_volume ?? null,
              }
            : { average_speed: null, total_volume: null }
        );
      };
      fetchStat();
    } else {
      setTrafficStat(null);
    }
  }, [selectedIntersection, currentDate]);

  // 거리 계산 함수 (Haversine 공식)
  const calculateDistance = (
    point1: Intersection,
    point2: Intersection
  ): number => {
    const R = 6371; // 지구의 반지름 (km)
    const dLat = ((point2.latitude - point1.latitude) * Math.PI) / 180;
    const dLon = ((point2.longitude - point1.longitude) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((point1.latitude * Math.PI) / 180) *
        Math.cos((point2.latitude * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  // 이동 시간 계산 함수 (평균 속도 40km/h 가정)
  const calculateTravelTime = (
    point1: Intersection,
    point2: Intersection
  ): number => {
    const distance = calculateDistance(point1, point2);
    const averageSpeed = 40; // km/h
    return Math.round((distance / averageSpeed) * 60); // 분 단위
  };

  const [showIncidentPanel, setShowIncidentPanel] = useState(false);

  useEffect(() => {
    if (selectedIncident) setShowIncidentPanel(true);
  }, [selectedIncident]);

  const handleCloseIncidentPanel = () => {
    setShowIncidentPanel(false);
    setTimeout(() => setSelectedIncident(null), 300); // 애니메이션 시간 후 unmount
  };

  const [showIntersectionPanel, setShowIntersectionPanel] = useState(false);

  useEffect(() => {
    if (selectedIntersection) setShowIntersectionPanel(true);
  }, [selectedIntersection]);

  const handleCloseIntersectionPanel = () => {
    setShowIntersectionPanel(false);
    setTimeout(() => setSelectedIntersection(null), 300);
  };

  const [showRoutePanel, setShowRoutePanel] = useState(false);

  useEffect(() => {
    if (selectedPoints.length === 2) setShowRoutePanel(true);
  }, [selectedPoints]);

  const handleCloseRoutePanel = () => {
    setShowRoutePanel(false);
    setTimeout(() => setSelectedPoints([]), 300);
  };

  // 컴포넌트 마운트 시 스타일 추가
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = `
      @keyframes slideUp {
        from {
          opacity: 0;
          transform: translateY(20px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .animate-slideUp {
        animation: slideUp 0.3s ease-out;
      }

      .map-container {
        overflow: hidden;
        position: relative;
        height: 100%;
        width: 100%;
      }

      .dashboard-active .gm-style {
        overflow: hidden !important;
      }

      .dashboard-active .gm-style-moc {
        overflow: hidden !important;
      }

      .map-scroll-disabled {
        overflow: hidden !important;
        touch-action: none;
        -webkit-overflow-scrolling: auto;
      }

      .dashboard-active body {
        overflow: hidden !important;
      }

      .dashboard-active html {
        overflow: hidden !important;
      }

      .dashboard-active #root {
        overflow: hidden !important;
      }

      .dashboard-active .gm-style-moc,
      .dashboard-active .gm-style-mtc,
      .dashboard-active .gm-style-mcc {
        overflow: hidden !important;
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  if (isLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <p className="text-gray-500">Loading data...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-active">
      {/* 기존 레이아웃 */}
      <div className="h-screen w-full bg-gray-100 flex font-sans text-gray-800 overflow-hidden">
        <NavBar
          activeNav={activeNav}
          setActiveNav={handleNavChange}
          activeTrafficView={activeTrafficView}
          setActiveTrafficView={handleTrafficViewChange}
          onCloseDetailPanels={handleCloseDetailPanels}
        />
        {/* Sidebar 렌더링 로직 - tableau 모드일 때는 모든 sidebar 숨김 */}
        {activeNav !== "tableau" && (
          <>
            {activeTrafficView === "favorites" ? (
              <FavoritesSidebar
                favoriteIntersections={intersections.filter((intersection) =>
                  favoriteIntersections.includes(intersection.id)
                )}
                favoriteIncidents={incidents.filter((incident) =>
                  favoriteIncidents.includes(incident.id)
                )}
                onIntersectionClick={handleIntersectionClick}
                onIncidentClick={handleIncidentClick}
                selectedIntersectionId={selectedIntersection?.id}
                selectedIncidentId={selectedIncident?.id}
              />
            ) : activeTrafficView === "analysis" ? (
              <AnalysisSidebar
                selectedIntersection={selectedIntersection}
                onIntersectionClick={handleIntersectionClick}
                currentDate={currentDate}
                setCurrentDate={setCurrentDate}
                searchTerm={searchTerm}
                setSearchTerm={setSearchTerm}
                intersections={intersections}
                activeNav={activeNav}
                favoriteIntersections={favoriteIntersections}
                onToggleFavorite={handleToggleFavorite}
              />
            ) : activeTrafficView === "flow" ? (
              <TrafficFlowSidebar
                selectedPoints={selectedPoints}
                currentDate={currentDate}
                setCurrentDate={setCurrentDate}
                calculateDistance={calculateDistance}
                calculateTravelTime={calculateTravelTime}
              />
            ) : activeTrafficView === "incidents" ? (
              <IncidentSidebar
                incidents={incidents}
                onIncidentClick={handleIncidentClick}
                selectedIncidentId={selectedIncident?.id}
              />
            ) : null}
          </>
        )}

        <main className="flex-1 relative bg-gray-100 map-scroll-disabled">
          {activeNav === "tableau" ? (
            <div className="absolute inset-0 p-4 overflow-auto">
              <TableauDashboard />
            </div>
          ) : (
            <>
              <div className="absolute inset-0 map-container">
                <GoogleMapWrapper
                  selectedIntersection={selectedIntersection}
                  selectedIncident={selectedIncident}
                  onIntersectionClick={handleIntersectionClick}
                  intersections={intersections}
                  activeTrafficView={activeTrafficView}
                  intersectionTrafficData={intersectionTrafficData}
                  incidents={incidents}
                  onSelectedPointsChange={setSelectedPoints}
                  onIncidentClick={handleIncidentClick}
                  center={incidentMapCenter}
                />
              </div>
              {activeTrafficView === "favorites" && !selectedIntersection && (
                <div className="absolute top-8 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg p-4 flex items-center space-x-3 z-10">
                  <Star size={24} className="text-yellow-500" />
                  <div className="text-sm">
                    <p className="font-semibold text-gray-700">
                      Favorites Mode
                    </p>
                    <p className="text-gray-600">
                      {favoriteIntersections.length > 0
                        ? `${favoriteIntersections.length} favorite intersections`
                        : "No favorite intersections yet"}
                    </p>
                  </div>
                </div>
              )}
              {(activeTrafficView === "analysis" ||
                activeTrafficView === "flow" ||
                activeTrafficView === "incidents") &&
                !selectedIntersection &&
                !selectedIncident &&
                !(
                  activeTrafficView === "flow" && selectedPoints.length === 2
                ) &&
                !showIntersectionPanel &&
                !showIncidentPanel &&
                !showRoutePanel && (
                  <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg p-4 flex items-center space-x-3">
                    <MapIcon size={24} className="text-blue-500" />
                    <p className="text-sm text-gray-700">
                      {activeTrafficView === "analysis" &&
                        t("dashboard.selectIntersection")}
                      {activeTrafficView === "flow" &&
                        (selectedPoints.length === 0
                          ? t("map.clickFirstPoint")
                          : selectedPoints.length === 1
                          ? t("map.clickSecondPoint")
                          : t("map.selectTwoPointsDesc"))}
                      {activeTrafficView === "incidents" &&
                        t("dashboard.selectIncident")}
                    </p>
                  </div>
                )}
            </>
          )}
          {/* 단순 교차로 통행량 뷰에서 DetailPanel 표시 */}
          {(showIntersectionPanel || selectedIntersection) &&
            activeTrafficView === "analysis" &&
            selectedIntersection && (
              <div
                className={`fixed top-0 right-0 h-full z-50 flex justify-center items-center transition-all duration-300 ease-in-out bg-white/90
                ${
                  showIntersectionPanel
                    ? "translate-x-0 opacity-100"
                    : "translate-x-full opacity-0"
                }`}
                style={{
                  boxShadow: "0px 4px 12.8px 0px rgba(0, 0, 0, 0.30)",
                  backdropFilter: "blur(5px)",
                  borderRight: "1px solid #ECECEC",
                  zIndex: 60,
                  width: isDetailPanelFullscreen ? "100vw" : "min(700px, 90vw)",
                }}
              >
                <div
                  className="h-full overflow-y-auto relative flex justify-center"
                  style={{ width: "100%" }}
                >
                  <div className="w-full max-w-[700px]">
                    <IntersectionDetailPanel
                      intersection={selectedIntersection}
                      favoriteIntersections={favoriteIntersections}
                      onToggleFavorite={handleToggleFavorite}
                      onClose={handleCloseIntersectionPanel}
                      isFullscreen={isDetailPanelFullscreen}
                      trafficStat={trafficStat}
                      trafficChartData={trafficChartData} // 4. prop으로 전달
                    />
                  </div>
                </div>
              </div>
            )}

          {/* 교차로 간 통행량 뷰용 분석 패널 */}
          {(showRoutePanel || selectedPoints.length === 2) &&
            activeTrafficView === "flow" &&
            selectedPoints.length === 2 && (
              <div
                className={`fixed top-0 right-0 h-full z-50 flex justify-center items-center transition-all duration-300 ease-in-out bg-white/90
                ${
                  showRoutePanel
                    ? "translate-x-0 opacity-100"
                    : "translate-x-full opacity-0"
                }`}
                style={{
                  boxShadow: "0px 4px 12.8px 0px rgba(0, 0, 0, 0.30)",
                  backdropFilter: "blur(5px)",
                  borderRight: "1px solid #ECECEC",
                  zIndex: 60,
                  width: "min(700px, 90vw)",
                }}
              >
                <div
                  className="h-full overflow-y-auto relative flex justify-center"
                  style={{ width: "100%" }}
                >
                  <div className="w-full max-w-[700px] p-8 pt-20">
                    <TrafficFlowDetailPanel
                      selectedPoints={selectedPoints}
                      onClose={handleCloseRoutePanel}
                      calculateDistance={calculateDistance}
                      calculateTravelTime={calculateTravelTime}
                      isFullscreen={isDetailPanelFullscreen}
                    />
                  </div>
                </div>
              </div>
            )}
          {/* incidents 뷰에서 사고 선택 시 오른쪽 분석 패널 오버레이 */}
          {(showIncidentPanel || selectedIncident) &&
            activeTrafficView === "incidents" &&
            selectedIncident && (
              <div
                className={`fixed top-0 right-0 h-full z-50 flex justify-center items-center transition-all duration-300 ease-in-out bg-white/90
                ${
                  showIncidentPanel
                    ? "translate-x-0 opacity-100"
                    : "translate-x-full opacity-0"
                }`}
                style={{
                  boxShadow: "0px 4px 12.8px 0px rgba(0, 0, 0, 0.30)",
                  backdropFilter: "blur(5px)",
                  borderLeft: "1px solid #ECECEC",
                  zIndex: 60,
                  width: isDetailPanelFullscreen ? "100vw" : "min(700px, 90vw)",
                }}
              >
                <div
                  className="h-full overflow-y-auto relative flex justify-center"
                  style={{ width: "100%" }}
                >
                  <div className="w-full max-w-[700px] p-8 pt-20">
                    <IncidentDetailPanel
                      incident={selectedIncident}
                      onClose={handleCloseIncidentPanel}
                    />
                  </div>
                </div>
              </div>
            )}
        </main>
      </div>

      {/* AI 챗봇 플로팅 버튼 */}
      <ChatBotButton />
    </div>
  );
}
