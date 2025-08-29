import React from "react";

const AdminDashboard = () => {
  // 세종시 모킹 데이터
  const topViewedAreas = [
    { rank: 1, area: "정부청사 교차로", views: 1847, change: 15 },
    { rank: 2, area: "세종로터리", views: 1456, change: 8 },
    { rank: 3, area: "나성동 교차로", views: 1323, change: -3 },
    { rank: 4, area: "조치원읍 중심가", views: 1184, change: 12 },
    { rank: 5, area: "반곡동 교차로", views: 967, change: 7 },
    { rank: 6, area: "어진동 사거리", views: 832, change: -1 },
    { rank: 7, area: "새롬동 중앙로", views: 798, change: 4 },
    { rank: 8, area: "종촌동 교차로", views: 656, change: 9 },
    { rank: 9, area: "연기면 소재지", views: 589, change: -2 },
    { rank: 10, area: "전동면 중심가", views: 487, change: 6 },
  ];

  const topFavoriteAreas = [
    { rank: 1, area: "정부청사 출근길", favorites: 234, growth: 12 },
    { rank: 2, area: "세종로터리", favorites: 198, growth: 8 },
    { rank: 3, area: "나성동 학교앞", favorites: 167, growth: -2 },
    { rank: 4, area: "조치원역 주변", favorites: 145, growth: 15 },
    { rank: 5, area: "새롬동 아파트단지", favorites: 123, growth: 5 },
  ];

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
                <p className="text-2xl font-bold text-gray-900">2,123</p>
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
                <p className="text-sm font-medium text-gray-600">활성 사용자</p>
                <p className="text-2xl font-bold text-gray-900">3,143</p>
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
              <span className="text-green-600 text-sm font-medium">+8.2%</span>
              <span className="text-gray-500 text-sm ml-1">전일 대비</span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">정책 제안</p>
                <p className="text-2xl font-bold text-gray-900">1,423</p>
              </div>
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-yellow-600"
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
              <span className="text-green-600 text-sm font-medium">+5.1%</span>
              <span className="text-gray-500 text-sm ml-1">전일 대비</span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">AI 리포트</p>
                <p className="text-2xl font-bold text-gray-900">89</p>
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
              <span className="text-red-600 text-sm font-medium">-2.3%</span>
              <span className="text-gray-500 text-sm ml-1">전일 대비</span>
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
              <div className="space-y-3">
                {topViewedAreas.map((item) => (
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
                        {item.views.toLocaleString()}
                      </span>
                      <span
                        className={`text-xs px-1 ${
                          item.change > 0
                            ? "text-red-600"
                            : item.change < 0
                            ? "text-blue-600"
                            : "text-gray-600"
                        }`}
                      >
                        {item.change > 0 ? "▲" : item.change < 0 ? "▼" : "—"}{" "}
                        {Math.abs(item.change)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
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
              <div className="space-y-3">
                {topFavoriteAreas.map((item) => (
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
                        {item.favorites}명
                      </span>
                      <span
                        className={`text-xs px-1 ${
                          item.growth > 0
                            ? "text-green-600"
                            : item.growth < 0
                            ? "text-red-600"
                            : "text-gray-600"
                        }`}
                      >
                        {item.growth > 0 ? "▲" : item.growth < 0 ? "▼" : "—"}{" "}
                        {Math.abs(item.growth)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
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

          {/* AI 리포트 생성 지역 */}
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
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">지역별 리포트 빈도</p>
              </div>
            </div>
          </div>
        </div>

        {/* 네 번째 행 - 정책 제안 섹션 */}
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
