import { Intersection } from '../types/global.types';

// 두 지점 간의 거리를 계산하는 함수 (Haversine 공식)
export const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number): number => {
  const R = 6371; // 지구의 반지름 (km)
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLng/2) * Math.sin(dLng/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
};

// 특정 교차로에서 가장 가까운 N개의 교차로를 찾는 함수
export const findNearestIntersections = (
  targetIntersection: Intersection, 
  allIntersections: Intersection[], 
  count: number = 2
): Intersection[] => {
  const distances = allIntersections
    .filter(intersection => intersection.id !== targetIntersection.id)
    .map(intersection => ({
      intersection,
      distance: calculateDistance(
        targetIntersection.latitude,
        targetIntersection.longitude,
        intersection.latitude,
        intersection.longitude
      )
    }))
    .sort((a, b) => a.distance - b.distance);

  return distances.slice(0, count).map(item => item.intersection);
};

// 두 교차로 간의 통행량을 계산하는 함수
export const calculateIntersectionTraffic = (
  intersection1: Intersection,
  intersection2: Intersection
): {
  distance: number;
  averageVolume: number;
  averageSpeed: number;
  trafficFlow: number;
} => {
  const distance = calculateDistance(
    intersection1.latitude,
    intersection1.longitude,
    intersection2.latitude,
    intersection2.longitude
  );

  // 두 교차로의 평균 통행량과 속도 계산
  const volume1 = intersection1.total_traffic_volume ?? 0;
  const volume2 = intersection2.total_traffic_volume ?? 0;
  const speed1 = intersection1.average_speed ?? 0;
  const speed2 = intersection2.average_speed ?? 0;

  const averageVolume = Math.round((volume1 + volume2) / 2);
  const averageSpeed = Math.round((speed1 + speed2) / 2);
  
  // 거리에 따른 통행량 흐름 계산 (거리가 가까울수록 통행량이 높음)
  const distanceFactor = Math.max(0.1, 1 - (distance / 10)); // 10km 이상이면 최소 0.1
  const trafficFlow = Math.round(averageVolume * distanceFactor);

  return {
    distance: Math.round(distance * 1000) / 1000, // 소수점 3자리까지
    averageVolume,
    averageSpeed,
    trafficFlow
  };
};

// 모든 교차로에 대해 근접 교차로 간 통행량을 계산하는 함수
export const calculateAllIntersectionTraffic = (
  intersections: Intersection[]
): Array<{
  source: Intersection;
  nearest: Intersection[];
  trafficData: Array<{
    target: Intersection;
    distance: number;
    averageVolume: number;
    averageSpeed: number;
    trafficFlow: number;
  }>;
}> => {
  return intersections.map(source => {
    const nearest = findNearestIntersections(source, intersections, 2);
    const trafficData = nearest.map(target => ({
      target,
      ...calculateIntersectionTraffic(source, target)
    }));

    return {
      source,
      nearest,
      trafficData
    };
  });
};

// 교차로 이름을 비교를 위해 정규화 (공백, 특수문자 제거, 소문자 통일)
function normalizeName(name: string) {
  return name.replace(/[^a-zA-Z0-9가-힣]/g, '').toLowerCase();
}

// 모든 교차로 쌍 중 이름 파트에 공통된 부분이 하나라도 있고, 두 교차로의 거리가 0.5km(=500m) 이하인 경우만 연결쌍으로 반환
export const findAllConnectedPairs = (allIntersections: Intersection[]) => {
  const pairs: Array<{ source: Intersection; target: Intersection }> = [];
  const seen = new Set<string>();
  for (let i = 0; i < allIntersections.length; i++) {
    const a = allIntersections[i];
    const aParts = a.name.split('-').map(s => normalizeName(s.trim())).filter(Boolean);
    for (let j = i + 1; j < allIntersections.length; j++) {
      const b = allIntersections[j];
      const bParts = b.name.split('-').map(s => normalizeName(s.trim())).filter(Boolean);
      const distance = calculateDistance(a.latitude, a.longitude, b.latitude, b.longitude);
      if (
        distance <= 0.5 &&
        aParts.some(part => part && bParts.includes(part))
      ) {
        const key = `${a.id}-${b.id}`;
        if (!seen.has(key)) {
          pairs.push({ source: a, target: b });
          seen.add(key);
        }
      }
    }
  }
  return pairs;
}; 