import React, { useRef, useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  GoogleMap as GoogleMapComponent,
  OverlayView,
} from "@react-google-maps/api";
import { Intersection, Incident } from "../../../shared/types/global.types";
import {
  MarkerClusterer,
  SuperClusterAlgorithm,
} from "@googlemaps/markerclusterer";

interface GoogleMapProps {
  selectedIntersection: Intersection | null;
  selectedIncident?: Incident | null;
  onIntersectionClick: (intersection: Intersection) => void;
  intersections: Intersection[];
  activeTrafficView?: "analysis" | "flow" | "incidents" | "favorites";
  intersectionTrafficData?: Array<{
    source: Intersection;
    nearest: Intersection[];
    trafficData: Array<{
      target: Intersection;
      distance: number;
      averageVolume: number;
      averageSpeed: number;
      trafficFlow: number;
    }>;
  }>;
  incidents?: Incident[];
  selectedPoints?: Intersection[]; // 추가
  onSelectedPointsChange?: (points: Intersection[]) => void;
  onIncidentClick?: (incident: Incident) => void;
  center?: { lat: number; lng: number } | null;
  onRouteUpdate?: (routeData: {
    distance: string;
    duration: string;
    source: string;
    coordinates: { lat: number; lng: number }[];
  }) => void;
}

// const defaultCenter = { lat: -12.0464, lng: -77.0428 }; // Lima, Peru
const defaultCenter = { lat: 36.5040736, lng: 127.2494855 }; //세종

export const GoogleMap: React.FC<GoogleMapProps> = ({
  selectedIntersection,
  selectedIncident,
  onIntersectionClick,
  intersections,
  activeTrafficView = "analysis",
  intersectionTrafficData,
  incidents = [],
  selectedPoints: propsSelectedPoints = [], // 추가
  onSelectedPointsChange,
  onIncidentClick,
  center,
  onRouteUpdate,
}) => {
  const { t } = useTranslation();
  const mapRef = useRef<google.maps.Map | null>(null);
  const polylineRef = useRef<google.maps.Polyline | null>(null);
  const directionsRendererRef = useRef<google.maps.DirectionsRenderer | null>(
    null
  );
  // const [selectedMarker, setSelectedMarker] = useState<Intersection | null>(
  //   null
  // );
  const [visibleMarkers, setVisibleMarkers] = useState<Intersection[]>([]);
  const [selectedPoints, setSelectedPoints] =
    useState<Intersection[]>(propsSelectedPoints);
  const [showPolyline, setShowPolyline] = useState(false);
  const [mapCenter, setMapCenter] = useState(defaultCenter);
  const prevPropsSelectedPointsRef =
    useRef<Intersection[]>(propsSelectedPoints);

  // props의 selectedPoints와 동기화
  useEffect(() => {
    if (
      JSON.stringify(propsSelectedPoints) !==
      JSON.stringify(prevPropsSelectedPointsRef.current)
    ) {
      setSelectedPoints(propsSelectedPoints);
      prevPropsSelectedPointsRef.current = propsSelectedPoints;
    }
  }, [propsSelectedPoints]);

  // selectedPoints가 빈 배열이 될 때 polyline 정리
  useEffect(() => {
    if (selectedPoints.length === 0) {
      // polyline 정리
      if (polylineRef.current) {
        // 다중 레이어 polyline인 경우
        if ((polylineRef.current as any).shadow) {
          (polylineRef.current as any).shadow?.setMap(null);
          (polylineRef.current as any).main?.setMap(null);
          (polylineRef.current as any).highlight?.setMap(null);
          (polylineRef.current as any).animated?.setMap(null);
        } else {
          // 단일 polyline인 경우
          polylineRef.current.setMap(null);
        }
        polylineRef.current = null;
      }

      // DirectionsRenderer 정리
      if (directionsRendererRef.current) {
        directionsRendererRef.current.setMap(null);
        directionsRendererRef.current = null;
      }
    }
  }, [selectedPoints]);

  // 컴포넌트 스타일 설정
  useEffect(() => {
    // 필요한 경우 추가 스타일을 여기에 정의할 수 있습니다
  }, []);

  // selectedPoints가 변경될 때 부모 컴포넌트에 알림 (무한 루프 방지)
  useEffect(() => {
    if (
      onSelectedPointsChange &&
      JSON.stringify(selectedPoints) !==
        JSON.stringify(prevPropsSelectedPointsRef.current)
    ) {
      onSelectedPointsChange(selectedPoints);
    }
  }, [selectedPoints, onSelectedPointsChange]);

  // 화면 내 마커만 필터링
  const updateVisibleMarkers = useCallback(() => {
    if (!mapRef.current) return;
    const bounds = mapRef.current.getBounds();
    if (!bounds) return;
    setVisibleMarkers(
      intersections.filter((i) =>
        bounds.contains(new window.google.maps.LatLng(i.latitude, i.longitude))
      )
    );
  }, [intersections]);

  // 맵이 이동/확대될 때마다 visibleMarkers 갱신
  const onMapIdle = useCallback(() => {
    updateVisibleMarkers();
  }, [updateVisibleMarkers]);

  // OpenStreetMap Routing을 사용한 실제 도로 경로 (무료 대안)
  const tryOpenStreetMapRouting = useCallback(async (): Promise<boolean> => {
    if (!mapRef.current || selectedPoints.length !== 2) return false;

    try {
      console.log("🗺️ OpenStreetMap Routing 시도");

      const start = selectedPoints[0];
      const end = selectedPoints[1];

      // OSRM (Open Source Routing Machine) API 사용
      const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${start.longitude},${start.latitude};${end.longitude},${end.latitude}?overview=full&geometries=geojson`;

      console.log("OSRM API URL:", osrmUrl);

      const response = await fetch(osrmUrl);
      const osrmData = await response.json();

      console.log("OSRM 전체 응답:", osrmData);

      if (
        osrmData.code === "Ok" &&
        osrmData.routes &&
        osrmData.routes.length > 0
      ) {
        const route = osrmData.routes[0];
        const coordinates = route.geometry.coordinates;

        console.log("🎉 OSRM 성공! 경로 점 개수:", coordinates.length);
        console.log(
          "거리:",
          route.distance,
          "미터, 시간:",
          route.duration,
          "초"
        );

        // 좌표를 Google Maps 형식으로 변환 ([lng, lat] -> {lat, lng})
        const pathPoints = coordinates.map((coord: [number, number]) => ({
          lat: coord[1],
          lng: coord[0],
        }));

        // 개선된 도로 경로 폴리라인 생성 - 이중 라인 효과 (굵기 +2pt)

        // 1. 바닥 그림자 라인 (더 두껍고 어두운 색)
        const shadowPolyline = new window.google.maps.Polyline({
          path: pathPoints,
          strokeColor: "#1e293b", // 어두운 회색
          strokeOpacity: 0.4,
          strokeWeight: 12, // 기존 10 + 2
          geodesic: false,
          map: mapRef.current,
          zIndex: 998,
        });

        // 2. 메인 경로 라인 (녹색)
        const mainPolyline = new window.google.maps.Polyline({
          path: pathPoints,
          strokeColor: "#059669", // 진한 초록색
          strokeOpacity: 0.9,
          strokeWeight: 8, // 기존 6 + 2
          geodesic: false,
          map: mapRef.current,
          zIndex: 999,
        });

        // 3. 중앙 하이라이트 라인 (더 밝은 녹색)
        const highlightPolyline = new window.google.maps.Polyline({
          path: pathPoints,
          strokeColor: "#10b981", // 밝은 녹색
          strokeOpacity: 0.8,
          strokeWeight: 5, // 기존 3 + 2
          geodesic: false,
          map: mapRef.current,
          zIndex: 1000,
        });

        // 4. 애니메이션 효과를 위한 점선
        const animatedPolyline = new window.google.maps.Polyline({
          path: pathPoints,
          strokeColor: "#ffffff",
          strokeOpacity: 0.7,
          strokeWeight: 3, // 기존 1 + 2
          geodesic: false,
          map: mapRef.current,
          zIndex: 1001,
          icons: [
            {
              icon: {
                path: "M 0,-1 0,1",
                strokeOpacity: 1,
                strokeColor: "#ffffff",
                strokeWeight: 4, // 기존 2 + 2
              },
              offset: "0",
              repeat: "20px",
            },
          ],
        });

        // 모든 폴리라인을 객체로 저장해서 나중에 제거할 수 있도록
        polylineRef.current = {
          shadow: shadowPolyline,
          main: mainPolyline,
          highlight: highlightPolyline,
          animated: animatedPolyline,
        } as any;

        // OSRM 경로 데이터를 부모 컴포넌트로 전달
        if (onRouteUpdate) {
          onRouteUpdate({
            distance: `${(route.distance / 1000).toFixed(1)} km`,
            duration: `${Math.round(route.duration / 60)}분`,
            source: "osrm",
            coordinates: pathPoints,
          });
        }

        // 경로가 잘 보이도록 지도 범위 조정
        const bounds = new window.google.maps.LatLngBounds();
        pathPoints.forEach((point: { lat: number; lng: number }) =>
          bounds.extend(point)
        );
        mapRef.current.fitBounds(bounds);

        console.log("🎉 OpenStreetMap 실제 도로 경로 표시 완료!");
        return true;
      } else {
        console.log("OSRM 경로 찾기 실패:", osrmData.message || osrmData.code);
        return false;
      }
    } catch (error) {
      console.error("OpenStreetMap Routing 오류:", error);
      return false;
    }
  }, [selectedPoints]);

  // Roads API를 사용한 도로 스냅핑 경로 생성
  const tryRoadsAPI = useCallback(async (): Promise<boolean> => {
    if (!mapRef.current || selectedPoints.length !== 2) return false;

    try {
      const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
      if (!apiKey) {
        console.error("Google Maps API Key가 없습니다");
        return false;
      }

      // 두 점 사이에 중간점들을 생성 (더 정확한 경로를 위해)
      const start = selectedPoints[0];
      const end = selectedPoints[1];

      // 간단한 직선 상의 중간점들 생성 (실제로는 더 복잡한 경로 알고리즘 필요)
      const intermediatePoints = [];
      const steps = 5; // 중간점 개수

      for (let i = 0; i <= steps; i++) {
        const ratio = i / steps;
        const lat = start.latitude + (end.latitude - start.latitude) * ratio;
        const lng = start.longitude + (end.longitude - start.longitude) * ratio;
        intermediatePoints.push(`${lat},${lng}`);
      }

      console.log("🛣️ Roads API 경로 스냅핑 시도:", intermediatePoints);

      // Roads API - Snap to Roads 호출
      const pathParam = intermediatePoints.join("|");
      const roadsUrl = `https://roads.googleapis.com/v1/snapToRoads?path=${pathParam}&interpolate=true&key=${apiKey}`;

      console.log("Roads API URL:", roadsUrl);

      const response = await fetch(roadsUrl);
      const roadsData = await response.json();

      console.log("Roads API 전체 응답:", roadsData);

      if (roadsData.error) {
        console.error("Roads API 오류:", roadsData.error);
        return false;
      }

      // Roads API 응답 상세 분석
      console.log("snappedPoints 존재:", !!roadsData.snappedPoints);
      console.log("snappedPoints 길이:", roadsData.snappedPoints?.length || 0);
      console.log("warningMessage:", roadsData.warningMessage);

      if (roadsData.snappedPoints && roadsData.snappedPoints.length > 0) {
        console.log(
          "🎉 Roads API 성공! 스냅된 점 개수:",
          roadsData.snappedPoints.length
        );

        // 스냅된 점들로 폴리라인 생성
        const snappedPath = roadsData.snappedPoints.map((point: any) => ({
          lat: point.location.latitude,
          lng: point.location.longitude,
        }));

        const polyline = new window.google.maps.Polyline({
          path: snappedPath,
          strokeColor: "#22c55e", // 녹색으로 구분
          strokeOpacity: 0.8,
          strokeWeight: 6,
          geodesic: false,
          map: mapRef.current,
          zIndex: 1000,
        });

        polylineRef.current = polyline;

        // 경로가 잘 보이도록 지도 범위 조정
        const bounds = new window.google.maps.LatLngBounds();
        snappedPath.forEach((point: { lat: number; lng: number }) =>
          bounds.extend(point)
        );
        mapRef.current.fitBounds(bounds);

        console.log("Roads API 경로 표시 완료");
        return true;
      }

      console.log("Roads API 결과 없음");
      return false;
    } catch (error) {
      console.error("Roads API 오류:", error);
      return false;
    }
  }, [selectedPoints]);

  // Geometry Library를 사용한 곡선 경로 생성 (Roads API 대안)
  const tryGeometryPath = useCallback((): boolean => {
    if (
      !mapRef.current ||
      selectedPoints.length !== 2 ||
      !window.google?.maps?.geometry
    )
      return false;

    try {
      console.log("🔀 Geometry Library로 곡선 경로 생성 시도");

      const start = new window.google.maps.LatLng(
        selectedPoints[0].latitude,
        selectedPoints[0].longitude
      );
      const end = new window.google.maps.LatLng(
        selectedPoints[1].latitude,
        selectedPoints[1].longitude
      );

      // 두 점 사이의 거리 계산
      const distance =
        window.google.maps.geometry.spherical.computeDistanceBetween(
          start,
          end
        );
      console.log("두 점 사이 거리:", distance, "미터");

      // 더 현실적인 도로 경로를 위한 중간점들 생성
      const pathPoints = [];
      const numPoints = Math.max(15, Math.floor(distance / 30)); // 30m마다 점 생성 (더 세밀하게)

      for (let i = 0; i <= numPoints; i++) {
        const fraction = i / numPoints;

        // 기본 직선 보간
        const lat =
          selectedPoints[0].latitude +
          (selectedPoints[1].latitude - selectedPoints[0].latitude) * fraction;
        const lng =
          selectedPoints[0].longitude +
          (selectedPoints[1].longitude - selectedPoints[0].longitude) *
            fraction;

        // 도로 패턴을 모방한 복합 곡선 효과
        const sineCurve = Math.sin(fraction * Math.PI * 2) * 0.001; // 기본 곡선
        const randomOffset = (Math.random() - 0.5) * 0.0008; // 랜덤 변화
        const gradualCurve = Math.sin(fraction * Math.PI) * 0.002; // 부드러운 아치

        // 도시 도로 패턴: 격자형 이동 시뮬레이션
        let latOffset = 0;
        let lngOffset = 0;

        // 1/3 지점에서 북쪽으로 우회
        if (fraction > 0.3 && fraction < 0.7) {
          latOffset = 0.001 * Math.sin(((fraction - 0.3) / 0.4) * Math.PI);
        }

        // 2/3 지점에서 동쪽으로 우회
        if (fraction > 0.5 && fraction < 0.8) {
          lngOffset = 0.001 * Math.sin(((fraction - 0.5) / 0.3) * Math.PI);
        }

        const adjustedLat =
          lat + sineCurve + randomOffset + gradualCurve + latOffset;
        const adjustedLng =
          lng + sineCurve * 0.7 + randomOffset * 0.8 + lngOffset;

        pathPoints.push({ lat: adjustedLat, lng: adjustedLng });
      }

      console.log("생성된 경로 점 개수:", pathPoints.length);

      // 곡선 경로로 폴리라인 생성
      const polyline = new window.google.maps.Polyline({
        path: pathPoints,
        strokeColor: "#f59e0b", // 주황색으로 구분
        strokeOpacity: 0.8,
        strokeWeight: 6,
        geodesic: true, // 지구 곡면을 따라가는 경로
        map: mapRef.current,
        zIndex: 1000,
      });

      polylineRef.current = polyline;

      // 경로가 잘 보이도록 지도 범위 조정
      const bounds = new window.google.maps.LatLngBounds();
      pathPoints.forEach((point: { lat: number; lng: number }) =>
        bounds.extend(point)
      );
      mapRef.current.fitBounds(bounds);

      console.log("🎉 Geometry Library 곡선 경로 표시 완료");
      return true;
    } catch (error) {
      console.error("Geometry Library 오류:", error);
      return false;
    }
  }, [selectedPoints]);

  // Polyline 관리 함수
  // Google Directions API를 사용한 실제 도로 경로 표시
  const updatePolyline = useCallback(async () => {
    console.log("경로 표시 시작:", {
      activeTrafficView,
      showPolyline,
      selectedPointsLength: selectedPoints.length,
    });

    // 기존 모든 경로 표시 제거
    if (polylineRef.current) {
      if ("setMap" in polylineRef.current) {
        // 단일 폴리라인인 경우
        polylineRef.current.setMap(null);
      } else {
        // 다중 폴리라인 객체인 경우
        (polylineRef.current as any).shadow?.setMap(null);
        (polylineRef.current as any).main?.setMap(null);
        (polylineRef.current as any).highlight?.setMap(null);
        (polylineRef.current as any).animated?.setMap(null);
      }
      polylineRef.current = null;
      console.log("기존 Polyline 제거");
    }

    if (directionsRendererRef.current) {
      directionsRendererRef.current.setMap(null);
      directionsRendererRef.current = null;
      console.log("기존 DirectionsRenderer 제거");
    }

    // flow 뷰에서 두 점이 선택된 경우에만 경로 표시
    if (
      activeTrafficView === "flow" &&
      showPolyline &&
      selectedPoints.length === 2 &&
      mapRef.current
    ) {
      // 좌표 조정 함수 (더 큰 범위로)
      const adjustCoordinates = (lat: number, lng: number, attempt: number) => {
        const adjustments = [
          { lat: 0, lng: 0 }, // 원본
          { lat: 0.001, lng: 0.001 }, // 북동쪽 (100m 정도)
          { lat: -0.001, lng: -0.001 }, // 남서쪽
          { lat: 0.001, lng: -0.001 }, // 북서쪽
          { lat: -0.001, lng: 0.001 }, // 남동쪽
          { lat: 0.002, lng: 0 }, // 북쪽 (200m)
          { lat: 0, lng: 0.002 }, // 동쪽
          { lat: -0.002, lng: 0 }, // 남쪽
          { lat: 0, lng: -0.002 }, // 서쪽
          { lat: 0.003, lng: 0.003 }, // 더 큰 범위 (300m)
          { lat: -0.003, lng: -0.003 },
        ];

        const adjustment = adjustments[attempt] || adjustments[0];
        const adjustedLat = lat + adjustment.lat;
        const adjustedLng = lng + adjustment.lng;

        console.log(
          `📍 좌표 조정 (시도 ${
            attempt + 1
          }): ${lat}, ${lng} → ${adjustedLat}, ${adjustedLng}`
        );
        return { lat: adjustedLat, lng: adjustedLng };
      };

      try {
        // 1. OpenStreetMap Routing을 먼저 시도 (무료, 전세계 도로 데이터)
        const osmSuccess = await tryOpenStreetMapRouting();
        if (osmSuccess) {
          console.log("🗺️ OpenStreetMap Routing 성공!");
          return;
        }

        // 2. Roads API 시도 (GPS 좌표를 도로에 스냅핑)
        const roadsApiSuccess = await tryRoadsAPI();
        if (roadsApiSuccess) {
          console.log("🛣️ Roads API 성공!");
          return;
        }

        // 3. Roads API 실패 시 Geometry Library로 곡선 경로 시도
        console.log("Roads API 실패, Geometry Library로 시도...");
        const geometrySuccess = tryGeometryPath();
        if (geometrySuccess) {
          console.log("🔀 Geometry Library 성공!");
          return;
        }

        // 4. Geometry Library도 실패 시 Directions API 시도
        console.log("Geometry Library 실패, Directions API로 시도...");
        const directionsService = new window.google.maps.DirectionsService();
        const directionsRenderer = new window.google.maps.DirectionsRenderer({
          map: mapRef.current,
          suppressMarkers: false,
          polylineOptions: {
            strokeColor: "#2563eb",
            strokeWeight: 6,
            strokeOpacity: 0.8,
          },
        });

        // 여러 좌표 조정과 모드로 시도
        const routeAttempts = [
          // 원본 좌표로 시도
          {
            origin: {
              lat: selectedPoints[0].latitude,
              lng: selectedPoints[0].longitude,
            },
            destination: {
              lat: selectedPoints[1].latitude,
              lng: selectedPoints[1].longitude,
            },
            travelMode: window.google.maps.TravelMode.DRIVING,
            label: "자동차(원본)",
          },
          {
            origin: {
              lat: selectedPoints[0].latitude,
              lng: selectedPoints[0].longitude,
            },
            destination: {
              lat: selectedPoints[1].latitude,
              lng: selectedPoints[1].longitude,
            },
            travelMode: window.google.maps.TravelMode.WALKING,
            label: "도보(원본)",
          },
          // 조정된 좌표로 시도 (3가지 조정)
          ...Array.from({ length: 3 }, (_, i) => [
            {
              origin: adjustCoordinates(
                selectedPoints[0].latitude,
                selectedPoints[0].longitude,
                i + 1
              ),
              destination: adjustCoordinates(
                selectedPoints[1].latitude,
                selectedPoints[1].longitude,
                i + 1
              ),
              travelMode: window.google.maps.TravelMode.DRIVING,
              label: `자동차(조정${i + 1})`,
            },
            {
              origin: adjustCoordinates(
                selectedPoints[0].latitude,
                selectedPoints[0].longitude,
                i + 1
              ),
              destination: adjustCoordinates(
                selectedPoints[1].latitude,
                selectedPoints[1].longitude,
                i + 1
              ),
              travelMode: window.google.maps.TravelMode.WALKING,
              label: `도보(조정${i + 1})`,
            },
          ]).flat(),
          // 대중교통 (마지막 시도)
          {
            origin: {
              lat: selectedPoints[0].latitude,
              lng: selectedPoints[0].longitude,
            },
            destination: {
              lat: selectedPoints[1].latitude,
              lng: selectedPoints[1].longitude,
            },
            travelMode: window.google.maps.TravelMode.TRANSIT,
            label: "대중교통",
          },
        ];

        for (let i = 0; i < routeAttempts.length; i++) {
          try {
            console.log(
              `🗺️ [${routeAttempts[i].label}] 경로 검색 시도 ${i + 1}:`,
              routeAttempts[i]
            );
            const result = await directionsService.route({
              origin: routeAttempts[i].origin,
              destination: routeAttempts[i].destination,
              travelMode: routeAttempts[i].travelMode,
              region: "KR",
            });

            if (result.routes && result.routes.length > 0) {
              directionsRenderer.setDirections(result);
              directionsRendererRef.current = directionsRenderer;

              const route = result.routes[0];
              const leg = route.legs[0];
              console.log(
                `🎉 [${routeAttempts[i].label}] 경로 표시 성공! (시도 ${
                  i + 1
                }) - ${leg.distance?.text}, ${leg.duration?.text}`
              );

              // 경로가 잘 보이도록 지도 범위 조정
              const bounds = route.bounds;
              if (bounds && mapRef.current) {
                mapRef.current.fitBounds(bounds);
              }

              return; // 성공하면 종료
            }
          } catch (error) {
            const errorMessage =
              error instanceof Error ? error.message : String(error);
            console.log(
              `❌ [${routeAttempts[i].label}] 경로 검색 시도 ${i + 1} 실패:`,
              {
                label: routeAttempts[i].label,
                error: errorMessage,
              }
            );

            // 마지막 시도가 아니면 계속
            if (i < routeAttempts.length - 1) {
              continue;
            }
          }
        }

        // 모든 시도가 실패한 경우 직선으로 표시 (폴백)
        console.log("모든 경로 검색 실패, 직선으로 표시");
        const polyline = new window.google.maps.Polyline({
          path: [
            {
              lat: selectedPoints[0].latitude,
              lng: selectedPoints[0].longitude,
            },
            {
              lat: selectedPoints[1].latitude,
              lng: selectedPoints[1].longitude,
            },
          ],
          strokeColor: "#ff0000",
          strokeOpacity: 0.8,
          strokeWeight: 6,
          geodesic: true,
          map: mapRef.current,
          zIndex: 1000,
        });
        polylineRef.current = polyline;

        // 두 점을 포함하도록 지도 범위 조정
        const bounds = new window.google.maps.LatLngBounds();
        bounds.extend({
          lat: selectedPoints[0].latitude,
          lng: selectedPoints[0].longitude,
        });
        bounds.extend({
          lat: selectedPoints[1].latitude,
          lng: selectedPoints[1].longitude,
        });
        mapRef.current.fitBounds(bounds);

        console.log("직선 경로 표시 완료");
      } catch (error) {
        console.error("경로 표시 중 오류:", error);
      }
    }
  }, [activeTrafficView, showPolyline, selectedPoints]);

  // activeTrafficView가 변경될 때 선택된 점들 초기화
  useEffect(() => {
    // 교차로 간 뷰에서 다른 뷰(analysis, incidents)로 전환할 때 선 해제
    if (activeTrafficView === "analysis" || activeTrafficView === "incidents") {
      console.log(
        `View changed to ${activeTrafficView}, clearing selected points and polyline`
      );
      setSelectedPoints([]);
      setShowPolyline(false);
      // Polyline 제거
      if (polylineRef.current) {
        if ("setMap" in polylineRef.current) {
          // 단일 폴리라인인 경우
          polylineRef.current.setMap(null);
        } else {
          // 다중 폴리라인 객체인 경우
          (polylineRef.current as any).shadow?.setMap(null);
          (polylineRef.current as any).main?.setMap(null);
          (polylineRef.current as any).highlight?.setMap(null);
          (polylineRef.current as any).animated?.setMap(null);
        }
        polylineRef.current = null;
        console.log("Polyline removed due to view change");
      }
    }
  }, [activeTrafficView, onSelectedPointsChange]);

  // Polyline 업데이트
  useEffect(() => {
    updatePolyline();

    // cleanup 함수
    return () => {
      if (polylineRef.current) {
        if ("setMap" in polylineRef.current) {
          // 단일 폴리라인인 경우
          polylineRef.current.setMap(null);
        } else {
          // 다중 폴리라인 객체인 경우
          (polylineRef.current as any).shadow?.setMap(null);
          (polylineRef.current as any).main?.setMap(null);
          (polylineRef.current as any).highlight?.setMap(null);
          (polylineRef.current as any).animated?.setMap(null);
        }
        polylineRef.current = null;
        console.log("Polyline removed on component unmount");
      }
    };
  }, [updatePolyline]);

  // 마커 클릭 핸들러 - flow 뷰에서만 선 연결 기능 활성화
  const handleMarkerClick = useCallback(
    (intersection: Intersection) => {
      // 클릭된 마커 위치로 지도 중심 이동
      if (mapRef.current) {
        mapRef.current.panTo({
          lat: intersection.latitude,
          lng: intersection.longitude,
        });
      }

      if (activeTrafficView !== "flow") {
        // 단순 교차로/사고 뷰에서는 교차로 선택만 처리
        onIntersectionClick(intersection);
        return;
      }

      console.log("clicked", intersection.id);

      setSelectedPoints((prev) => {
        console.log(
          "prev selectedPoints:",
          prev.map((p) => p.id)
        );

        // 이미 선택된 점인지 확인
        const isAlreadySelected = prev.some((p) => p.id === intersection.id);

        if (isAlreadySelected) {
          // 이미 선택된 점을 클릭하면 해제
          const newPoints = prev.filter((p) => p.id !== intersection.id);
          console.log(
            "Deselected! New state:",
            newPoints.map((p) => p.id)
          );
          // Polyline 숨기기
          setShowPolyline(false);
          // 부모 컴포넌트에 알림
          if (onSelectedPointsChange) {
            onSelectedPointsChange(newPoints);
          }
          return newPoints;
        }

        // 새로운 점 선택
        if (prev.length === 0) {
          console.log("First point selected:", intersection.id);
          setShowPolyline(false);
          const newPoints = [intersection];
          // 부모 컴포넌트에 알림
          if (onSelectedPointsChange) {
            onSelectedPointsChange(newPoints);
          }
          return newPoints;
        } else if (prev.length === 1) {
          console.log("Second point selected:", intersection.id);
          setShowPolyline(true);
          const newPoints = [...prev, intersection];
          // 부모 컴포넌트에 알림
          if (onSelectedPointsChange) {
            onSelectedPointsChange(newPoints);
          }
          return newPoints;
        } else if (prev.length === 2) {
          // 2개가 이미 선택된 상태에서 새로운 점을 클릭하면 초기화
          console.log("Reset with new point:", intersection.id);
          setShowPolyline(false);
          const newPoints = [intersection];
          // 부모 컴포넌트에 알림
          if (onSelectedPointsChange) {
            onSelectedPointsChange(newPoints);
          }
          return newPoints;
        }

        return prev;
      });
    },
    [activeTrafficView, onIntersectionClick]
  ); // 의존성 배열에 activeTrafficView와 onIntersectionClick 추가

  // 클러스터러 적용 - 뷰에 따라 다른 마커 표시
  useEffect(() => {
    if (!mapRef.current) return;

    // 기존 마커/클러스터러 정리
    if ((window as any).markerClusterer) {
      (window as any).markerClusterer.clearMarkers();
    }

    // 선택된 마커들도 정리
    if ((window as any).selectedMarkers) {
      (window as any).selectedMarkers.forEach((marker: google.maps.Marker) => {
        marker.setMap(null);
      });
      (window as any).selectedMarkers = [];
    }

    let markers: google.maps.Marker[] = [];

    if (activeTrafficView === "incidents") {
      // incidents/intersections 데이터 상태 확인용 로그
      console.log(
        "incidents:",
        incidents.map((i) => i.intersection_name || i.location_name)
      );
      console.log(
        "intersections:",
        intersections.map((i) => i.name)
      );

      // incidents 또는 intersections가 비어있으면 마커 생성하지 않음
      if (incidents.length === 0 || intersections.length === 0) {
        markers = [];
      } else {
        markers = incidents
          .map((incident) => {
            // incidents에 위경도가 없으면 intersections에서 찾아서 사용
            let lat = incident.latitude;
            let lng = incident.longitude;
            if (
              (lat === undefined || lng === undefined) &&
              intersections.length > 0
            ) {
              const found = intersections.find(
                (i) => i.name === incident.intersection_name
              );
              console.log(
                "incident:",
                incident.intersection_name,
                "found:",
                found ? found.name : "NOT FOUND"
              );
              if (found) {
                lat = found.latitude;
                lng = found.longitude;
              }
            }
            if (lat === undefined || lng === undefined) return null; // 위치 정보 없으면 마커 생성 X

            // 선택된 사고인지 확인하여 시각적 강조
            const isSelected =
              selectedIncident && selectedIncident.id === incident.id;

            const marker = new window.google.maps.Marker({
              position: { lat, lng },
              icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: isSelected ? 10 : 8, // 선택된 경우 더 크게
                fillColor: "#ef4444", // 빨간색
                fillOpacity: 1,
                strokeColor: isSelected ? "#fbbf24" : "#ffffff", // 선택된 경우 노란색 테두리
                strokeWeight: isSelected ? 3 : 2, // 선택된 경우 더 두꺼운 테두리
              },
              title: `${incident.incident_type} - ${incident.location_name}`,
              zIndex: isSelected ? 1000 : 100, // 선택된 마커가 위에 표시되도록
            });

            marker.addListener("click", () => {
              console.log("🎯 Incident marker clicked!");
              console.log("Incident data:", incident);
              console.log("onIncidentClick function:", typeof onIncidentClick);

              // 클릭된 마커 위치로 지도 중심 이동
              if (mapRef.current) {
                mapRef.current.panTo({ lat, lng });
              }

              if (onIncidentClick) {
                console.log("✅ Calling onIncidentClick...");
                onIncidentClick(incident);
              } else {
                console.log("❌ onIncidentClick is not provided");
              }
            });

            return marker;
          })
          .filter((m): m is google.maps.Marker => m !== null); // 타입 단언
      }
    } else {
      // analysis, flow 뷰에서는 교차로 마커 표시
      if (visibleMarkers.length === 0) return;

      // 선택된 점들의 ID 배열
      const selectedIds = selectedPoints.map((p) => p.id);

      // 선택되지 않은 점들은 클러스터링 적용
      const unselectedMarkers = visibleMarkers
        .filter((intersection) => !selectedIds.includes(intersection.id))
        .map((intersection) => {
          // 뷰에 따른 마커 색상 결정
          let fillColor = "#3b82f6"; // 기본 파란색
          let strokeColor = "#ffffff";
          let strokeWeight = 1.5;
          let scale = 6;

          // 선택된 교차로인지 확인하여 시각적 강조
          const isSelected =
            !!selectedIntersection &&
            selectedIntersection.id === intersection.id;

          if (isSelected) {
            strokeColor = "#fbbf24"; // 노란색 테두리
            strokeWeight = 3; // 더 두꺼운 테두리
            scale = 8; // 더 큰 크기
          }

          switch (activeTrafficView) {
            case "analysis":
              fillColor = "#3b82f6"; // 파란색
              break;
            case "flow":
              fillColor = "#10b981"; // 초록색
              break;
          }

          const marker = new window.google.maps.Marker({
            position: {
              lat: intersection.latitude,
              lng: intersection.longitude,
            },
            icon: {
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: scale,
              fillColor: fillColor,
              fillOpacity: 1,
              strokeColor: strokeColor,
              strokeWeight: strokeWeight,
            },
            zIndex: isSelected ? 1000 : 100, // 선택된 마커가 위에 표시되도록
          });
          marker.addListener("click", () => {
            handleMarkerClick(intersection);
          });
          return marker;
        });

      // 선택된 점들은 개별 마커로 표시 (클러스터링 제외)
      // selectedPoints.map((intersection, idx) => {
      //   const isFirstSelected = idx === 0;
      //   const isSecondSelected = idx === 1;

      //   let fillColor = "#3b82f6";
      //   let strokeColor = "#ffffff";
      //   let strokeWeight = 2; // 테두리 강조
      //   let scale = 8; // 선택된 점은 조금 더 크게

      //   if (isFirstSelected) {
      //     fillColor = "#2563eb"; // 진한 파란색 (시작점)
      //   } else if (isSecondSelected) {
      //     fillColor = "#ef4444"; // 빨간색 (끝점)
      //   }

      //   const marker = new window.google.maps.Marker({
      //     position: { lat: intersection.latitude, lng: intersection.longitude },
      //     icon: {
      //       path: window.google.maps.SymbolPath.CIRCLE,
      //       scale: scale,
      //       fillColor: fillColor,
      //       fillOpacity: 1,
      //       strokeColor: strokeColor,
      //       strokeWeight: strokeWeight,
      //     },
      //     zIndex: 1000, // 선택된 마커가 위에 표시되도록
      //   });
      //   marker.addListener("click", () => {
      //     handleMarkerClick(intersection);
      //   });
      //   return marker;
      // });

      // 클러스터링은 선택되지 않은 마커들에만 적용
      markers = unselectedMarkers;
    }

    if (markers.length > 0) {
      // incidents 뷰에서는 클러스터링을 완전히 비활성화
      if (activeTrafficView === "incidents") {
        console.log(
          "Setting incidents markers directly on map:",
          markers.length
        );
        markers.forEach((marker) => {
          marker.setMap(mapRef.current!);
        });
      } else {
        // 클러스터링은 선택되지 않은 마커들에만 적용
        if (markers.length > 0) {
          (window as any).markerClusterer = new MarkerClusterer({
            markers,
            map: mapRef.current!,
            algorithm: new SuperClusterAlgorithm({
              radius: 120, // 80에서 120으로 증가 (더 넓은 클러스터링)
              maxZoom: 15, // 16에서 15로 낮춤 (더 높은 줌에서도 클러스터링 유지)
              minPoints: 2, // 최소 2개 점으로 클러스터 형성
            }),
          });
        }

        // 선택된 마커들은 개별적으로 맵에 추가 (클러스터링 제외)
        if (activeTrafficView === "flow" && selectedPoints.length > 0) {
          selectedPoints.forEach((intersection, idx) => {
            const isFirstSelected = idx === 0;
            const isSecondSelected = idx === 1;

            let fillColor = "#3b82f6";
            let strokeColor = "#ffffff";
            let strokeWeight = 2;
            let scale = 8;

            if (isFirstSelected) {
              fillColor = "#2563eb"; // 진한 파란색 (시작점)
            } else if (isSecondSelected) {
              fillColor = "#ef4444"; // 빨간색 (끝점)
            }

            const selectedMarker = new window.google.maps.Marker({
              position: {
                lat: intersection.latitude,
                lng: intersection.longitude,
              },
              icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: scale,
                fillColor: fillColor,
                fillOpacity: 1,
                strokeColor: strokeColor,
                strokeWeight: strokeWeight,
              },
              zIndex: 1000,
              map: mapRef.current!,
            });

            selectedMarker.addListener("click", () => {
              handleMarkerClick(intersection);
            });

            // 선택된 마커들을 추적하기 위해 전역 배열에 저장
            if (!(window as any).selectedMarkers) {
              (window as any).selectedMarkers = [];
            }
            (window as any).selectedMarkers.push(selectedMarker);
          });
        }
      }
    }

    // cleanup
    return () => {
      if (activeTrafficView === "incidents") {
        console.log("Cleaning up incidents markers");
        markers.forEach((marker) => {
          marker.setMap(null);
        });
      } else {
        (window as any).markerClusterer?.clearMarkers();

        // 선택된 마커들도 정리
        if ((window as any).selectedMarkers) {
          (window as any).selectedMarkers.forEach(
            (marker: google.maps.Marker) => {
              marker.setMap(null);
            }
          );
          (window as any).selectedMarkers = [];
        }
      }
    };
  }, [
    visibleMarkers,
    handleMarkerClick,
    activeTrafficView,
    selectedPoints,
    incidents,
    intersections,
    selectedIntersection,
    selectedIncident,
    onIncidentClick,
  ]);

  // selectedIntersection이 바뀔 때 panTo로 이동
  useEffect(() => {
    if (selectedIntersection && mapRef.current) {
      mapRef.current.panTo({
        lat: selectedIntersection.latitude,
        lng: selectedIntersection.longitude,
      });
    }
  }, [selectedIntersection]);

  // 디버깅을 위한 selectedPoints 상태 변화 로그
  useEffect(() => {
    console.log(
      "selectedPoints changed:",
      selectedPoints.map((p) => p.id)
    );
    console.log(
      "Polyline status:",
      showPolyline && selectedPoints.length === 2 ? "visible" : "hidden",
      selectedPoints.map((p) => p.id)
    );
    console.log("showPolyline:", showPolyline);

    // 부모 컴포넌트로 선택된 점 정보 전달
    if (onSelectedPointsChange) {
      onSelectedPointsChange(selectedPoints);
    }
  }, [selectedPoints, showPolyline, onSelectedPointsChange]);

  // incidents 뷰일 때 첫 번째 마커 위치로 center 이동
  useEffect(() => {
    if (activeTrafficView === "incidents" && incidents.length > 0) {
      let lat = incidents[0].latitude;
      let lng = incidents[0].longitude;
      if (
        (lat === undefined || lng === undefined) &&
        intersections.length > 0
      ) {
        const searchName = (
          incidents[0].intersection_name ||
          incidents[0].location_name ||
          ""
        )
          .trim()
          .toLowerCase();
        const found = intersections.find(
          (i) => i.name.trim().toLowerCase() === searchName
        );
        if (found) {
          lat = found.latitude;
          lng = found.longitude;
        }
      }
      if (lat !== undefined && lng !== undefined) {
        setMapCenter({ lat, lng });
      }
    }
  }, [activeTrafficView, incidents, intersections]);

  // center prop이 바뀔 때 지도 중심 이동
  useEffect(() => {
    if (center && mapRef.current) {
      mapRef.current.panTo(center);
    }
  }, [center]);

  return (
    <GoogleMapComponent
      mapContainerStyle={{
        width: "100%",
        height: "100%",
      }}
      center={mapCenter}
      zoom={14}
      onLoad={(map) => {
        mapRef.current = map;
        updateVisibleMarkers();
      }}
      onIdle={onMapIdle}
      options={{
        styles: [
          {
            featureType: "poi",
            elementType: "labels",
            stylers: [{ visibility: "off" }],
          },
        ],
        disableDefaultUI: true,
        zoomControl: true,
        scrollwheel: true,
        gestureHandling: "greedy",
      }}
    >
      {/* 선택된 점 위에 커스텀 라벨 표시 - 교차로 간 통행량 뷰에서만 표시 */}
      {activeTrafficView === "flow" &&
        selectedPoints.map((point, idx) => (
          <OverlayView
            key={point.id}
            position={{ lat: point.latitude, lng: point.longitude }}
            mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
          >
            <div
              style={{
                position: "absolute",
                transform: "translate(-50%, -100%)",
                marginTop: "-10px",
                fontWeight: "600",
                color: "white",
                padding: "6px 14px",
                borderRadius: "18px",
                backgroundColor: idx === 0 ? "#2563eb" : "#ef4444",
                fontSize: "11px",
                boxShadow: "0 3px 10px rgba(0, 0, 0, 0.2)",
                textAlign: "center",
                minWidth: "70px",
                letterSpacing: "0.5px",
                textTransform: "uppercase",
                whiteSpace: "nowrap",
                zIndex: 1000,
              }}
            >
              {idx === 0 ? t("map.startPoint") : t("map.endPoint")}
            </div>
          </OverlayView>
        ))}
    </GoogleMapComponent>
  );
};

export default GoogleMap;
