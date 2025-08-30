import React, { useState, useEffect } from "react";
import GoogleMapWrapper from "./GoogleMapWrapper";
import { getTopViewedIntersections, getHeatmapData } from "../../../api/intersections";
import { TopViewedIntersection, HeatmapDataPoint } from "../../../types/global.types";

interface SejongHeatmapProps {
    className?: string;
    topViewedData?: TopViewedIntersection[];
}

const SejongHeatmap: React.FC<SejongHeatmapProps> = ({ className = "", topViewedData: propsTopViewedData = [] }) => {
    const [topViewedData, setTopViewedData] = useState<TopViewedIntersection[]>([]);
    const [heatmapData, setHeatmapData] = useState<HeatmapDataPoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 세종시 중심 좌표
    const sejongCenter = { lat: 36.5040736, lng: 127.2494855 };

    useEffect(() => {
        const fetchHeatmapData = async () => {
            try {
                setLoading(true);
                
                // 외부에서 전달받은 데이터가 있으면 우선 사용
                if (propsTopViewedData.length > 0) {
                    setTopViewedData(propsTopViewedData);
                    
                    // 히트맵 데이터만 가져오기
                    const heatmap = await getHeatmapData();
                    setHeatmapData(heatmap);
                } else {
                    // 외부 데이터가 없으면 직접 가져오기
                    const [topViewed, heatmap] = await Promise.all([
                        getTopViewedIntersections(),
                        getHeatmapData()
                    ]);

                    setTopViewedData(topViewed);
                    setHeatmapData(heatmap);
                }
                
                setError(null);
            } catch (err: any) {
                console.error('Failed to fetch heatmap data:', err);
                setError('히트맵 데이터를 불러오는데 실패했습니다.');
                // 에러 시 빈 데이터로 설정
                setTopViewedData([]);
                setHeatmapData([]);
            } finally {
                setLoading(false);
            }
        };

        fetchHeatmapData();

        // 30초마다 데이터 새로고침
        const interval = setInterval(fetchHeatmapData, 30000);
        return () => clearInterval(interval);
    }, [propsTopViewedData]);

    // 색상 스펙트럼 생성 함수 (빨간색 계열)
    const getColorFromIntensity = (intensity: number): string => {
        // intensity: 0.1 ~ 1.0
        const red = Math.min(255, Math.floor(255 * intensity));
        const green = Math.max(0, Math.floor(255 * (1 - intensity * 0.8)));
        const blue = Math.max(0, Math.floor(255 * (1 - intensity)));
        const alpha = Math.max(0.3, intensity * 0.8);
        
        return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
    };

    // 히트맵용 교차로 데이터 변환
    const intersectionsWithHeatmap = heatmapData.map(point => ({
        id: point.intersection_id,
        name: point.intersection_name,
        latitude: point.latitude,
        longitude: point.longitude,
        total_traffic_volume: point.view_count,
        heatmapIntensity: point.intensity,
        heatmapColor: getColorFromIntensity(point.intensity),
        isTopViewed: topViewedData.some(top => top.intersection_id === point.intersection_id)
    }));

    if (loading) {
        return (
            <div className={`${className} flex items-center justify-center bg-gray-50 rounded-lg`}>
                <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                    <div className="text-sm text-gray-600">히트맵 로딩 중...</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`${className} flex items-center justify-center bg-gray-50 rounded-lg`}>
                <div className="text-center text-red-500">
                    <div className="text-sm">{error}</div>
                </div>
            </div>
        );
    }

    return (
        <div className={className}>
            <div className="relative h-full">
                <GoogleMapWrapper
                    selectedIntersection={null}
                    onIntersectionClick={() => { }}
                    intersections={intersectionsWithHeatmap}
                    center={sejongCenter}
                    showHeatmap={true}
                    heatmapData={heatmapData}
                />
                
                {/* 범례 */}
                <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3 z-10">
                    <div className="text-xs font-semibold text-gray-700 mb-2">조회수 히트맵</div>
                    <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-600">낮음</span>
                        <div className="flex">
                            {[0.2, 0.4, 0.6, 0.8, 1.0].map((intensity, idx) => (
                                <div
                                    key={idx}
                                    className="w-4 h-3"
                                    style={{ backgroundColor: getColorFromIntensity(intensity) }}
                                />
                            ))}
                        </div>
                        <span className="text-xs text-gray-600">높음</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                        TOP 10: {topViewedData.length}개 구간
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SejongHeatmap;