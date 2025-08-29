import React, { useState, useEffect } from "react";
import { getAdminStats, getAdminIntersections } from "../../api/intersections";
import { AdminStats, TopArea, IntersectionStats } from "../../types/global.types";

const AdminDashboard = () => {
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [intersectionStats, setIntersectionStats] = useState<IntersectionStats[]>([]);
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
        
        // 교차로 목록은 백그라운드에서 로드 (덜 중요한 데이터)
        getAdminIntersections().then(intersections => {
          setIntersectionStats(intersections);
        }).catch(err => {
          console.error('Failed to fetch intersection stats:', err);
          setIntersectionStats([]);
        });
        
      } catch (err) {
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
              <div className="bg-green-100 px-3 py-1 rounded-full">
                <span className="text-green-800 text-sm font-medium">
                  실시간 업데이트
                </span>
              </div>
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
                            className={`text-sm font-bold w-6 ${
                              item.rank <= 3
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
                            className={`text-xs px-1 ${
                              (item.change ?? 0) > 0
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
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">라인 차트 영역 (시간별 트래픽)</p>
              </div>
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
                            className={`text-sm font-bold w-6 ${
                              item.rank <= 2
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
                            className={`text-xs px-1 ${
                              (item.growth ?? 0) > 0
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

        {/* 네 번째 행 - 교차로별 즐겨찾기 현황 */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6 border-b">
            <h3 className="text-lg font-semibold text-gray-900">
              교차로별 즐겨찾기 현황
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              각 교차로의 조회수와 즐겨찾기 등록 수 현황
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
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        순위
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        교차로명
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        총 조회수
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        즐겨찾기 수
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        즐겨찾기 비율
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        최근 조회
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {intersectionStats.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                          교차로 데이터가 없습니다.
                        </td>
                      </tr>
                    ) : (
                      intersectionStats.map((intersection, index) => {
                        const favoriteRatio = intersection.view_count > 0 
                          ? ((intersection.favorite_count / intersection.view_count) * 100).toFixed(1)
                          : "0.0";
                        
                        return (
                          <tr key={intersection.intersection_id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`text-sm font-bold ${
                                index < 3 ? "text-red-600" : 
                                index < 5 ? "text-orange-600" : "text-gray-600"
                              }`}>
                                {index + 1}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">
                                {intersection.intersection_name}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900">
                                {intersection.view_count.toLocaleString()}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-sm font-medium text-blue-600">
                                  {intersection.favorite_count}
                                </span>
                                <span className="text-sm text-gray-500 ml-1">명</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                  <div 
                                    className="bg-blue-600 h-2 rounded-full" 
                                    style={{ width: `${Math.min(parseFloat(favoriteRatio), 100)}%` }}
                                  ></div>
                                </div>
                                <span className="text-sm text-gray-600">
                                  {favoriteRatio}%
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {intersection.last_viewed 
                                ? new Date(intersection.last_viewed).toLocaleDateString('ko-KR', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })
                                : "조회 없음"
                              }
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* 다섯 번째 행 - 정책 제안 섹션 */}
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
