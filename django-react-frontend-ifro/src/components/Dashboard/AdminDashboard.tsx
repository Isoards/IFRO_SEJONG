import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from "recharts";
import {
  getAdminStats,
  getAdminIntersections,
  getTrafficFlowFavoritesStats,
  getTrafficFlowSummary
} from "../../api/intersections";
import {
  AdminStats,
  TopArea,
  IntersectionStats,
  TrafficFlowFavoriteStats,
  TrafficFlowSummary
} from "../../types/global.types";

// 일별 조회수 데이터 타입
interface DailyViewData {
  date: string;
  views: number;
  day: string;
}

// 테스트 데이터 생성 함수
const generateDailyViewData = (): DailyViewData[] => {
  const data: DailyViewData[] = [];
  const today = new Date();
  
  // 고정된 패턴 데이터 (요일별로 다른 패턴)
  const fixedPatterns = [1850, 1650, 1750, 1950, 2100, 2350, 2200]; // 7일간 고정 패턴
  
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
    const dayName = dayNames[date.getDay()];
    
    // 고정된 패턴 사용 (6-i는 0부터 6까지의 인덱스)
    const views = fixedPatterns[6 - i];
    
    data.push({
      date: `${date.getMonth() + 1}/${date.getDate()}`,
      views: views,
      day: dayName
    });
  }
  
  return data;
};

const AdminDashboard = () => {
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [intersectionStats, setIntersectionStats] = useState<IntersectionStats[]>([]);
  const [trafficFlowStats, setTrafficFlowStats] = useState<TrafficFlowFavoriteStats[]>([]);
  const [trafficFlowSummary, setTrafficFlowSummary] = useState<TrafficFlowSummary | null>(null);
  const [dailyViewData, setDailyViewData] = useState<DailyViewData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        setLoading(true);

        // 통계 데이터만 먼저 빠르게 로드 (더 중요한 데이터)
        const statsPromise = getAdminStats();
        const stats = await statsPromise;

        console.log('Fetched admin stats:', stats);
        console.log('Top favorite areas:', stats.top_favorite_areas);
        console.log('Top favorite areas length:', stats.top_favorite_areas?.length);

        setAdminStats(stats);
        setError(null);

        // 일별 조회수 데이터 초기화
        setDailyViewData(generateDailyViewData());

        // 교차로 목록과 교통 흐름 데이터는 백그라운드에서 로드 (덜 중요한 데이터)
        console.log('Starting to fetch additional data...');

        // 각각 개별적으로 호출해서 어느 것이 실패하는지 확인
        // 교차로 데이터는 성능상 이유로 비활성화
        // try {
        //   console.log('Fetching intersections...');
        //   const intersections = await getAdminIntersections();
        //   console.log('Intersections fetched:', intersections.length);
        //   setIntersectionStats(intersections);
        // } catch (err: any) {
        //   console.error('Failed to fetch intersections:', err);
        //   setIntersectionStats([]);
        // }

        // 교통 흐름 통계 활성화
        try {
          console.log('Fetching traffic flow stats...');
          const flowStats = await getTrafficFlowFavoritesStats();
          console.log('Traffic flow stats fetched:', flowStats);
          setTrafficFlowStats(flowStats);
        } catch (err: any) {
          console.error('Failed to fetch traffic flow stats:', err);
          console.error('Error details:', err.response?.data || err.message);
          setTrafficFlowStats([]);
        }

        // 교통 흐름 요약 활성화
        try {
          console.log('Fetching traffic flow summary...');
          const flowSummary = await getTrafficFlowSummary();
          console.log('Traffic flow summary fetched:', flowSummary);
          setTrafficFlowSummary(flowSummary);
        } catch (err: any) {
          console.error('Failed to fetch traffic flow summary:', err);
          console.error('Error details:', err.response?.data || err.message);
          setTrafficFlowSummary(null);
        }

      } catch (err: any) {
        console.error('Failed to fetch admin stats:', err);
        setError('통계 데이터를 불러오는데 실패했습니다.');
        // 에러 시 기본 데이터 사용
        setAdminStats({
          top_viewed_areas: [],
          top_favorite_areas: [],
          top_ai_report_areas: [],
          total_views: 0,
          total_favorites: 0,
          total_ai_reports: 0
        });
        setIntersectionStats([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAdminData();

    // 60초마다 데이터 새로고침 (30초에서 60초로 변경)
    const interval = setInterval(fetchAdminData, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-gray-100 min-h-screen">
      {/* 상단 헤더 */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                시민 통계 대시보드
              </h1>
              <p className="text-gray-600 mt-1">
                관리자용 - 실시간 시민 행동 분석
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors duration-200 shadow-sm"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 5a2 2 0 012-2h4a2 2 0 012 2v2H8V5z"
                  />
                </svg>
                <span className="text-sm font-medium">대시보드</span>
              </button>
              <div className="text-sm text-gray-500">
                마지막 업데이트: {new Date().toLocaleTimeString("ko-KR")}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="p-8 space-y-8">
        {/* KPI 카드들 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 조회수</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? "..." : adminStats?.total_views.toLocaleString() || "0"}
                </p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-red-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                  <path
                    fillRule="evenodd"
                    d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            </div>
            <div className="mt-2 flex items-center">
              <span className="text-green-600 text-sm font-medium">+12.5%</span>
              <span className="text-gray-500 text-sm ml-1">전일 대비</span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 즐겨찾기</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? "..." : adminStats?.total_favorites.toLocaleString() || "0"}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-blue-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                </svg>
              </div>
            </div>
            <div className="mt-2 flex items-center">
              <span className="text-green-600 text-sm font-medium">실시간</span>
              <span className="text-gray-500 text-sm ml-1">업데이트</span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 정책 제안</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? "..." : "0"}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-purple-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            </div>
            <div className="mt-2 flex items-center">
              <span className="text-gray-600 text-sm font-medium">준비 중</span>
              <span className="text-gray-500 text-sm ml-1">기능 개발 예정</span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">AI 분석 요청</p>
                <p className="text-2xl font-bold text-gray-900">
                  {loading ? "..." : adminStats?.total_ai_reports.toLocaleString() || "0"}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-purple-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            </div>
            <div className="mt-2 flex items-center">
              <span className="text-blue-600 text-sm font-medium">누적</span>
              <span className="text-gray-500 text-sm ml-1">전체 요청 수</span>
            </div>
          </div>
        </div>

        {/* 메인 콘텐츠 그리드 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 실시간 최다 조회 구간 TOP 10 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                실시간 최다 조회 구간 TOP 10
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                세종시 시민들이 가장 많이 조회하는 지역
              </p>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-gray-500">데이터 로딩 중...</div>
                </div>
              ) : error ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-red-500">{error}</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {adminStats?.top_viewed_areas.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                      조회 데이터가 없습니다.
                    </div>
                  ) : (
                    adminStats?.top_viewed_areas.map((item: TopArea) => (
                      <div
                        key={item.rank}
                        className="flex items-center justify-between py-2"
                      >
                        <div className="flex items-center space-x-3">
                          <span
                            className={`text-sm font-bold w-6 ${item.rank <= 3
                                ? "text-red-600"
                                : item.rank <= 5
                                  ? "text-orange-600"
                                  : "text-gray-600"
                              }`}
                          >
                            {item.rank}
                          </span>
                          <span className="text-gray-900 font-medium">
                            {item.area}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">
                            {(item.views ?? 0).toLocaleString()}
                          </span>
                          <span
                            className={`text-xs px-1 ${(item.change ?? 0) > 0
                                ? "text-red-600"
                                : (item.change ?? 0) < 0
                                  ? "text-blue-600"
                                  : "text-gray-600"
                              }`}
                          >
                            {(item.change ?? 0) > 0 ? "▲" : (item.change ?? 0) < 0 ? "▼" : "—"}{" "}
                            {Math.abs(item.change ?? 0)}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 트래픽 차트 */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                시민 관심도 추이
              </h3>
              <p className="text-sm text-gray-500 mt-1">일주일간 조회수 변화</p>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-gray-500">차트 데이터 로딩 중...</div>
                </div>
              ) : error ? (
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-red-500">차트 데이터 로드 실패</div>
                </div>
              ) : (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={dailyViewData}
                      margin={{
                        top: 20,
                        right: 30,
                        left: 20,
                        bottom: 20,
                      }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12, fill: "#666" }}
                        stroke="#888"
                        tickLine={{ stroke: "#ddd" }}
                      />
                      <YAxis
                        tick={{ fontSize: 12, fill: "#666" }}
                        stroke="#888"
                        tickLine={{ stroke: "#ddd" }}
                        domain={[0, 'dataMax + 200']}
                        tickFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#ffffff",
                          border: "1px solid #e2e8f0",
                          borderRadius: "8px",
                          fontSize: "14px",
                          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                        }}
                        labelStyle={{ 
                          fontWeight: "600",
                          color: "#374151"
                        }}
                        formatter={(value: number, name: string) => [
                          `${value.toLocaleString()}회`,
                          "조회수"
                        ]}
                        labelFormatter={(label: string) => {
                          const item = dailyViewData.find(d => d.date === label);
                          return `${label} (${item?.day})`;
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="views"
                        stroke="#3b82f6"
                        strokeWidth={3}
                        dot={{
                          fill: "#3b82f6",
                          strokeWidth: 2,
                          r: 5,
                        }}
                        activeDot={{
                          r: 7,
                          fill: "#1d4ed8",
                          stroke: "#ffffff",
                          strokeWidth: 2,
                        }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 두 번째 행 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 관심도 히트맵 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                관심도 히트맵
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                세종시 지역별 시민 관심도 분포
              </p>
            </div>
            <div className="p-6">
              <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">세종시 히트맵 영역</p>
              </div>
            </div>
          </div>

          {/* 최다 즐겨찾기 등록 구간 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                최다 즐겨찾기 등록 구간
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                시민들이 꾸준히 모니터링하는 지역
              </p>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-gray-500">데이터 로딩 중...</div>
                </div>
              ) : error ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-red-500">{error}</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {(!adminStats?.top_favorite_areas || adminStats?.top_favorite_areas.length === 0) ? (
                    <div className="text-center text-gray-500 py-8">
                      즐겨찾기 데이터가 없습니다. (Length: {adminStats?.top_favorite_areas?.length})
                    </div>
                  ) : (
                    adminStats?.top_favorite_areas.map((item: TopArea) => (
                      <div
                        key={item.rank}
                        className="flex items-center justify-between py-2"
                      >
                        <div className="flex items-center space-x-3">
                          <span
                            className={`text-sm font-bold w-6 ${item.rank <= 2
                                ? "text-yellow-600"
                                : item.rank <= 4
                                  ? "text-blue-600"
                                  : "text-gray-600"
                              }`}
                          >
                            {item.rank}
                          </span>
                          <span className="text-gray-900 font-medium">
                            {item.area}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">
                            {(item.favorites ?? 0)}명
                          </span>
                          <span
                            className={`text-xs px-1 ${(item.growth ?? 0) > 0
                                ? "text-green-600"
                                : (item.growth ?? 0) < 0
                                  ? "text-red-600"
                                  : "text-gray-600"
                              }`}
                          >
                            {(item.growth ?? 0) > 0 ? "▲" : (item.growth ?? 0) < 0 ? "▼" : "—"}{" "}
                            {Math.abs(item.growth ?? 0)}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 인기 검색어 클라우드 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                인기 검색어
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                시민들이 자주 검색하는 키워드
              </p>
            </div>
            <div className="p-6">
              <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">워드 클라우드 영역</p>
              </div>
            </div>
          </div>
        </div>

        {/* 세 번째 행 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 문제 제기 키워드 분석 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                문제 제기 키워드 분석
              </h3>
              <p className="text-sm text-gray-500 mt-1">시민 불편사항 분석</p>
            </div>
            <div className="p-6">
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">키워드 빈도 차트</p>
              </div>
            </div>
          </div>

          {/* AI 리포트 다발 지역 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                AI 리포트 다발 지역
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                분석 요청이 많은 문제 지역
              </p>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-gray-500">데이터 로딩 중...</div>
                </div>
              ) : error ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-red-500">{error}</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {(!adminStats?.top_ai_report_areas || adminStats?.top_ai_report_areas.length === 0) ? (
                    <div className="text-center text-gray-500 py-8">
                      AI 리포트 데이터가 없습니다.
                    </div>
                  ) : (
                    adminStats.top_ai_report_areas.map((area, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center space-x-3">
                          <span className="flex items-center justify-center w-6 h-6 bg-purple-100 text-purple-600 rounded-full text-sm font-medium">
                            {area.rank}
                          </span>
                          <span className="font-medium text-gray-900">
                            {area.area}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4">
                          <span className="text-sm text-gray-600">
                            {area.ai_reports}회
                          </span>
                          <div className="flex items-center space-x-1">
                            <span className="text-xs text-green-600">↗</span>
                            <span className="text-xs text-green-600">
                              {area.growth}%
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 네 번째 행 - 교차로별 즐겨찾기 현황 (비활성화됨 - 성능상 이유) */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">
              교차로별 즐겨찾기 현황
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              각 교차로의 조회수와 즐겨찾기 등록 수 현황 (성능상 이유로 비활성화)
            </p>
          </div>
          <div className="p-6">
            <div className="flex justify-center items-center h-32">
              <div className="text-center">
                <div className="text-gray-500 mb-2">📊</div>
                <div className="text-gray-500">
                  성능 최적화를 위해 일시적으로 비활성화되었습니다.
                </div>
                <div className="text-sm text-gray-400 mt-1">
                  필요시 개별 교차로 상세 페이지에서 확인 가능합니다.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 다섯 번째 행 - 교통 흐름 분석 즐겨찾기 통계 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 교통 흐름 요약 통계 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                교통 흐름 분석 요약
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                시민들의 교통 흐름 분석 이용 현황
              </p>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-gray-500">데이터 로딩 중...</div>
                </div>
              ) : error ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-red-500">데이터 로드 실패: {error}</div>
                </div>
              ) : trafficFlowSummary ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {trafficFlowSummary.summary.total_favorites}
                      </div>
                      <div className="text-sm text-gray-600">총 즐겨찾기</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {trafficFlowSummary.summary.total_routes}
                      </div>
                      <div className="text-sm text-gray-600">분석 경로</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {trafficFlowSummary.summary.total_users}
                      </div>
                      <div className="text-sm text-gray-600">활성 사용자</div>
                    </div>
                    <div className="text-center p-3 bg-orange-50 rounded-lg">
                      <div className="text-lg font-bold text-orange-600">
                        {trafficFlowSummary.summary.avg_favorites_per_route.toFixed(1)}
                      </div>
                      <div className="text-sm text-gray-600">경로당 평균</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  교통 흐름 데이터가 없습니다.
                </div>
              )}
            </div>
          </div>

          {/* 인기 교통 흐름 경로 TOP 10 */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                인기 교통 흐름 경로 TOP 5
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                시민들이 가장 많이 즐겨찾기한 A → B 경로 분석
              </p>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-gray-500">데이터 로딩 중...</div>
                </div>
              ) : error ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-red-500">데이터 로드 실패: {error}</div>
                </div>
              ) : trafficFlowStats.length > 0 ? (
                <div className="space-y-3">
                  {trafficFlowStats.slice(0, 5).map((flow) => (
                    <div
                      key={flow.rank}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <span
                          className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${flow.rank <= 3
                              ? "bg-yellow-100 text-yellow-800"
                              : flow.rank <= 5
                                ? "bg-blue-100 text-blue-800"
                                : "bg-gray-100 text-gray-800"
                            }`}
                        >
                          {flow.rank}
                        </span>
                        <div>
                          <div className="font-medium text-gray-900">
                            <span className="text-blue-600">{flow.start_intersection.name}</span>
                            <span className="mx-2 text-gray-400">→</span>
                            <span className="text-orange-600">{flow.end_intersection.name}</span>
                          </div>
                          <div className="text-sm text-gray-500">
                            {flow.unique_users}명의 사용자가 이용
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center space-x-4">
                          <div className="text-center">
                            <div className="text-lg font-bold text-blue-600">
                              {flow.total_favorites}
                            </div>
                            <div className="text-xs text-gray-500">즐겨찾기</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-green-600">
                              {flow.total_accesses}
                            </div>
                            <div className="text-xs text-gray-500">접근 횟수</div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-bold text-purple-600">
                              {flow.popularity_score}
                            </div>
                            <div className="text-xs text-gray-500">인기도</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  교통 흐름 즐겨찾기 데이터가 없습니다.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 여섯 번째 행 - 교통 흐름 분석 상세 통계 */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">
              교통 흐름 분석 상세 통계
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              각 교통 흐름 경로별 상세 이용 현황 및 인기도 분석
            </p>
          </div>
          <div className="p-6">
            {loading ? (
              <div className="flex justify-center items-center h-32">
                <div className="text-gray-500">데이터 로딩 중...</div>
              </div>
            ) : trafficFlowStats.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        순위
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        교통 흐름 경로
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        즐겨찾기 수
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        총 접근 횟수
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        고유 사용자
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        인기도 점수
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        최근 접근
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {trafficFlowStats.map((flow) => (
                      <tr key={flow.rank} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`text-sm font-bold ${flow.rank <= 3
                                ? "text-yellow-600"
                                : flow.rank <= 5
                                  ? "text-blue-600"
                                  : "text-gray-600"
                              }`}
                          >
                            {flow.rank}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            <span className="text-blue-600">{flow.start_intersection.name}</span>
                            <span className="mx-2 text-gray-400">→</span>
                            <span className="text-orange-600">{flow.end_intersection.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-blue-600">
                              {flow.total_favorites}
                            </span>
                            <span className="text-sm text-gray-500 ml-1">명</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {flow.total_accesses.toLocaleString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {flow.unique_users}명
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <span
                              className={`text-sm font-bold ${flow.popularity_score >= 50
                                  ? "text-red-600"
                                  : flow.popularity_score >= 20
                                    ? "text-orange-600"
                                    : flow.popularity_score >= 10
                                      ? "text-green-600"
                                      : "text-gray-600"
                                }`}
                            >
                              {flow.popularity_score}
                            </span>
                            <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${flow.popularity_score >= 50
                                    ? "bg-red-600"
                                    : flow.popularity_score >= 20
                                      ? "bg-orange-600"
                                      : flow.popularity_score >= 10
                                        ? "bg-green-600"
                                        : "bg-gray-600"
                                  }`}
                                style={{
                                  width: `${Math.min((flow.popularity_score / 100) * 100, 100)}%`,
                                }}
                              ></div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {flow.last_accessed
                            ? new Date(flow.last_accessed).toLocaleDateString("ko-KR", {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                            : "접근 없음"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                교통 흐름 분석 데이터가 없습니다.
              </div>
            )}
          </div>
        </div>

        {/* 일곱 번째 행 - 정책 제안 섹션 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 정책 제안 공감 순위 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                정책 제안 공감 순위
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                시민 지지도가 높은 제안
              </p>
            </div>
            <div className="p-6">
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">공감 순위 리스트</p>
              </div>
            </div>
          </div>

          {/* 정책 제안 처리 현황 */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                정책 제안 처리 현황
              </h3>
              <p className="text-sm text-gray-500 mt-1">단계별 처리 상태</p>
            </div>
            <div className="p-6">
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">퍼널 차트 영역</p>
              </div>
            </div>
          </div>
        </div>

        {/* 하단 정보 */}
        <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-blue-800 mb-2">
                💡 대시보드 활용 가이드
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-700">
                <div className="bg-white p-3 rounded border border-blue-100">
                  <strong>시민 관심도 지표:</strong> 잠재적 문제 지역 발굴을
                  위한 수동적 사용자 행동 분석
                </div>
                <div className="bg-white p-3 rounded border border-blue-100">
                  <strong>불편 및 요구사항:</strong> 시민들의 직접적인
                  불편사항과 개선 요구사항 파악
                </div>
                <div className="bg-white p-3 rounded border border-blue-100">
                  <strong>플랫폼 활용도:</strong> 서비스 이용률과 정책 제안 처리
                  투명성 확보
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
