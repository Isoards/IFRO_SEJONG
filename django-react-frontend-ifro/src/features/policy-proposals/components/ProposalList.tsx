import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  PolicyProposal,
  ProposalCategory,
  ProposalStatus,
  ProposalPriority,
  ProposalFilters,
} from "../../../shared/types/global.types";
import {
  getProposals,
  getMyProposals,
} from "../../../shared/services/proposals";
import { ChatBotButton } from "../../chatbot/components/ChatBotButton";

const CATEGORY_LABELS: Record<ProposalCategory, string> = {
  traffic_signal: "신호등 관련",
  road_safety: "도로 안전",
  traffic_flow: "교통 흐름",
  infrastructure: "인프라 개선",
  policy: "교통 정책",
  other: "기타",
};

const STATUS_LABELS: Record<ProposalStatus, string> = {
  pending: "대기 중",
  under_review: "검토 중",
  in_progress: "진행 중",
  completed: "완료",
  rejected: "반려",
};

const PRIORITY_LABELS: Record<
  ProposalPriority,
  { label: string; color: string }
> = {
  low: { label: "낮음", color: "text-green-600 bg-green-100" },
  medium: { label: "보통", color: "text-yellow-600 bg-yellow-100" },
  high: { label: "높음", color: "text-orange-600 bg-orange-100" },
  urgent: { label: "긴급", color: "text-red-600 bg-red-100" },
};

const STATUS_COLORS: Record<ProposalStatus, string> = {
  pending: "text-gray-600 bg-gray-100",
  under_review: "text-blue-600 bg-blue-100",
  in_progress: "text-purple-600 bg-purple-100",
  completed: "text-green-600 bg-green-100",
  rejected: "text-red-600 bg-red-100",
};

const ProposalList: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [proposals, setProposals] = useState<PolicyProposal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(10);
  const [showMyProposals, setShowMyProposals] = useState(false);

  const [filters, setFilters] = useState<ProposalFilters>({
    category: undefined,
    status: undefined,
    priority: undefined,
    search: "",
  });

  // URL 파라미터에서 필터 설정
  useEffect(() => {
    const intersectionId = searchParams.get("intersection_id");
    const category = searchParams.get("category") as ProposalCategory;
    const status = searchParams.get("status") as ProposalStatus;
    const priority = searchParams.get("priority") as ProposalPriority;
    const search = searchParams.get("search");

    setFilters((prev) => ({
      ...prev,
      intersection_id: intersectionId ? parseInt(intersectionId) : undefined,
      category: category || undefined,
      status: status || undefined,
      priority: priority || undefined,
      search: search || "",
    }));
  }, [searchParams]);

  // 제안 목록 로드
  useEffect(() => {
    loadProposals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, filters, showMyProposals]);

  const loadProposals = async () => {
    setIsLoading(true);
    try {
      let response;
      if (showMyProposals) {
        response = await getMyProposals(currentPage, pageSize);
      } else {
        response = await getProposals(currentPage, pageSize, filters);
      }

      setProposals(response.results);
      setTotalCount(response.count);
    } catch (error) {
      console.error("정책제안 목록 로딩 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (key: keyof ProposalFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadProposals();
  };

  const clearFilters = () => {
    setFilters({
      category: undefined,
      status: undefined,
      priority: undefined,
      search: "",
    });
    setCurrentPage(1);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const renderPagination = () => {
    const pages = [];
    const maxVisiblePages = 5;
    const startPage = Math.max(
      1,
      currentPage - Math.floor(maxVisiblePages / 2)
    );
    const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => setCurrentPage(i)}
          className={`px-3 py-2 mx-1 rounded-md ${
            i === currentPage
              ? "bg-blue-600 text-white"
              : "bg-gray-200 text-gray-700 hover:bg-gray-300"
          }`}
        >
          {i}
        </button>
      );
    }

    return (
      <div className="flex justify-center items-center mt-6 space-x-2">
        <button
          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="px-3 py-2 rounded-md bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          이전
        </button>
        {pages}
        <button
          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className="px-3 py-2 rounded-md bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          다음
        </button>
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            {showMyProposals ? "내 정책제안" : "정책제안"}
          </h1>
          <p className="text-gray-600">
            {showMyProposals
              ? "내가 제출한 정책제안들을 확인하고 관리할 수 있습니다."
              : "시민들의 교통 관련 정책제안을 확인해보세요."}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowMyProposals(!showMyProposals)}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
          >
            {showMyProposals ? "전체 제안 보기" : "내 제안만 보기"}
          </button>
          <button
            onClick={() => navigate("/proposals/create")}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            정책제안 작성
          </button>
        </div>
      </div>

      {/* 필터 및 검색 */}
      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                카테고리
              </label>
              <select
                value={filters.category || ""}
                onChange={(e) =>
                  handleFilterChange("category", e.target.value || undefined)
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">전체</option>
                {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상태
              </label>
              <select
                value={filters.status || ""}
                onChange={(e) =>
                  handleFilterChange("status", e.target.value || undefined)
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">전체</option>
                {Object.entries(STATUS_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                우선순위
              </label>
              <select
                value={filters.priority || ""}
                onChange={(e) =>
                  handleFilterChange("priority", e.target.value || undefined)
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">전체</option>
                {Object.entries(PRIORITY_LABELS).map(([value, { label }]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                검색
              </label>
              <input
                type="text"
                value={filters.search || ""}
                onChange={(e) => handleFilterChange("search", e.target.value)}
                placeholder="제목, 내용 검색..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              검색
            </button>
            <button
              type="button"
              onClick={clearFilters}
              className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
            >
              필터 초기화
            </button>
          </div>
        </form>
      </div>

      {/* 제안 목록 */}
      {isLoading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">로딩 중...</p>
        </div>
      ) : proposals.length === 0 ? (
        <div className="text-center py-8 bg-white rounded-lg shadow-sm">
          <p className="text-gray-600 text-lg">
            {showMyProposals
              ? "작성한 정책제안이 없습니다."
              : "등록된 정책제안이 없습니다."}
          </p>
          {showMyProposals && (
            <button
              onClick={() => navigate("/proposals/create")}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              첫 정책제안 작성하기
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {proposals.map((proposal) => (
            <div
              key={proposal.id}
              className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <Link
                    to={`/proposals/${proposal.id}`}
                    className="text-lg font-semibold text-gray-800 hover:text-blue-600 block"
                  >
                    {proposal.title}
                  </Link>
                  <div className="flex items-center gap-2 mt-2">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        PRIORITY_LABELS[proposal.priority].color
                      }`}
                    >
                      {PRIORITY_LABELS[proposal.priority].label}
                    </span>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        STATUS_COLORS[proposal.status]
                      }`}
                    >
                      {STATUS_LABELS[proposal.status]}
                    </span>
                    <span className="px-2 py-1 rounded-full text-xs font-medium text-gray-600 bg-gray-100">
                      {CATEGORY_LABELS[proposal.category]}
                    </span>
                  </div>
                </div>
                <div className="text-sm text-gray-500 text-right">
                  <p>{formatDate(proposal.created_at)}</p>
                  <p>by {proposal.submitted_by_name}</p>
                </div>
              </div>

              <p className="text-gray-600 mb-3 line-clamp-2">
                {proposal.description.length > 150
                  ? `${proposal.description.substring(0, 150)}...`
                  : proposal.description}
              </p>

              <div className="flex justify-between items-center">
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  {proposal.intersection_name && (
                    <span>📍 {proposal.intersection_name}</span>
                  )}
                  {proposal.votes_count !== undefined && (
                    <span>👍 {proposal.votes_count}</span>
                  )}
                  {proposal.views_count !== undefined && (
                    <span>👁️ {proposal.views_count}</span>
                  )}
                </div>

                <div className="flex gap-2">
                  {proposal.tags && proposal.tags.length > 0 && (
                    <div className="flex gap-1">
                      {proposal.tags.slice(0, 3).map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                        >
                          #{tag}
                        </span>
                      ))}
                      {proposal.tags.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                          +{proposal.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && renderPagination()}

      {/* 통계 정보 */}
      <div className="mt-8 text-center text-sm text-gray-500">
        총 {totalCount}개의 정책제안 중 {(currentPage - 1) * pageSize + 1}-
        {Math.min(currentPage * pageSize, totalCount)}개 표시
      </div>

      {/* AI 챗봇 플로팅 버튼 */}
      <ChatBotButton />
    </div>
  );
};

export default ProposalList;
