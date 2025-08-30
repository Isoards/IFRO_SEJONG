import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import GoogleMapsLoader from "../../utils/googleMapsLoader";
import { GoogleMap } from "./GoogleMap";
import { Intersection, Incident } from "../../types/global.types";

interface GoogleMapWrapperProps {
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
  showHeatmap?: boolean;
  heatmapData?: Array<{
    intersection_id: number;
    intersection_name: string;
    latitude: number;
    longitude: number;
    view_count: number;
    intensity: number;
    weight: number;
  }>;
}

const GOOGLE_MAPS_API_KEY = "AIzaSyBzlJSrUcsUQ4ygHlaQNhPVrgFmlqTyw_o";

// 언어 코드를 Google Maps API 언어 코드로 매핑
const getGoogleMapsLanguage = (i18nLanguage: string): string => {
  switch (i18nLanguage) {
    case "ko":
      return "ko";
    case "es":
      return "es";
    case "en":
    default:
      return "en";
  }
};

// 언어에 따른 지역 코드 설정
const getGoogleMapsRegion = (i18nLanguage: string): string => {
  switch (i18nLanguage) {
    case "ko":
      return "KR";
    case "es":
      return "PE"; // 페루 (리마)
    case "en":
    default:
      return "US";
  }
};

export const GoogleMapWrapper: React.FC<GoogleMapWrapperProps> = (props) => {
  const { i18n, t } = useTranslation();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapKey, setMapKey] = useState(0); // 지도 재렌더링을 위한 키

  useEffect(() => {
    const loadGoogleMaps = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const googleMapsLanguage = getGoogleMapsLanguage(i18n.language);
        const googleMapsRegion = getGoogleMapsRegion(i18n.language);

        const loader = GoogleMapsLoader.getInstance();

        // 언어가 변경되었는지 확인
        const currentLanguage = loader.getCurrentLanguage();
        if (currentLanguage && currentLanguage !== googleMapsLanguage) {
          // 언어가 변경되었으면 지도를 다시 렌더링
          setMapKey((prev) => prev + 1);
        }

        await loader.load({
          apiKey: GOOGLE_MAPS_API_KEY,
          language: googleMapsLanguage,
          region: googleMapsRegion,
          libraries: ["places", "geometry"], // geometry 라이브러리 추가
        });

        setIsLoading(false);
      } catch (err) {
        console.error("Google Maps 로드 실패:", err);
        setError(t("map.loadError") || "지도를 로드할 수 없습니다.");
        setIsLoading(false);
      }
    };

    loadGoogleMaps();
  }, [i18n.language]);

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {t("map.loading") || "지도를 로드하는 중..."}
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-2">⚠️</div>
          <p className="text-red-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            {t("common.refresh") || "새로고침"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div key={mapKey} className="w-full h-full">
      <GoogleMap {...props} />
    </div>
  );
};

export default GoogleMapWrapper;
