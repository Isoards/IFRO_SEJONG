import React, {
  useRef,
  useEffect,
  useState,
  useCallback,
} from "react";
import { useTranslation } from "react-i18next";
import {
  GoogleMap as GoogleMapComponent,
  OverlayView,
} from "@react-google-maps/api";
import { Intersection, Incident } from "../../types/global.types";
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
  onSelectedPointsChange?: (points: Intersection[]) => void;
  onIncidentClick?: (incident: Incident) => void;
  center?: { lat: number; lng: number } | null;
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
  onSelectedPointsChange,
  onIncidentClick,
  center,
}) => {
  const { t } = useTranslation();
  const mapRef = useRef<google.maps.Map | null>(null);
  const polylineRef = useRef<google.maps.Polyline | null>(null);
  // const [selectedMarker, setSelectedMarker] = useState<Intersection | null>(
  //   null
  // );
  const [visibleMarkers, setVisibleMarkers] = useState<Intersection[]>([]);
  const [selectedPoints, setSelectedPoints] = useState<Intersection[]>([]);
  const [showPolyline, setShowPolyline] = useState(false);
  const [mapCenter, setMapCenter] = useState(defaultCenter);

  // 컴포넌트 스타일 설정
  useEffect(() => {
    // 필요한 경우 추가 스타일을 여기에 정의할 수 있습니다
  }, []);

  // selectedPoints가 변경될 때 부모 컴포넌트에 알림
  useEffect(() => {
    if (onSelectedPointsChange) {
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

  // Polyline 관리 함수
  const updatePolyline = useCallback(() => {
    // 기존 Polyline 제거
    if (polylineRef.current) {
      polylineRef.current.setMap(null);
      polylineRef.current = null;
      console.log("Existing Polyline removed");
    }

    // intersection 뷰에서만 Polyline 생성
    if (
      activeTrafficView === "flow" &&
      showPolyline &&
      selectedPoints.length === 2 &&
      mapRef.current
    ) {
      const polyline = new window.google.maps.Polyline({
        path: [
          { lat: selectedPoints[0].latitude, lng: selectedPoints[0].longitude },
          { lat: selectedPoints[1].latitude, lng: selectedPoints[1].longitude },
        ],
        strokeColor: "#10b981",
        strokeOpacity: 0.9,
        strokeWeight: 5,
        geodesic: false,
        map: mapRef.current,
      });
      polylineRef.current = polyline;
      console.log("New Polyline created");
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
      // 부모 컴포넌트에 변경 알림
      if (onSelectedPointsChange) {
        onSelectedPointsChange([]);
      }
      // Polyline 제거
      if (polylineRef.current) {
        polylineRef.current.setMap(null);
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
        polylineRef.current.setMap(null);
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
          return newPoints;
        }

        // 새로운 점 선택
        if (prev.length === 0) {
          console.log("First point selected:", intersection.id);
          setShowPolyline(false);
          return [intersection];
        } else if (prev.length === 1) {
          console.log("Second point selected:", intersection.id);
          setShowPolyline(true);
          return [...prev, intersection];
        } else if (prev.length === 2) {
          // 2개가 이미 선택된 상태에서 새로운 점을 클릭하면 초기화
          console.log("Reset with new point:", intersection.id);
          setShowPolyline(false);
          return [intersection];
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
