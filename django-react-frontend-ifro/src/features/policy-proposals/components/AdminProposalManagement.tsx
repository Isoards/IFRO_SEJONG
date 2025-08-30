import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  PolicyProposal,
  ProposalCategory,
  ProposalStatus,
  ProposalPriority,
  ProposalFilters,
} from "../../../shared/types/global.types";
import {
  getProposals,
  updateProposalStatus,
  getProposalStats,
} from "../../../shared/services/proposals";

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

const AdminProposalManagement: React.FC = () => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [currentUser, setCurrentUser] = useState<any>({ role: 'admin' }); // Mock admin user
  const [proposals, setProposals] = useState<PolicyProposal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(15);
  const [selectedProposal, setSelectedProposal] =
    useState<PolicyProposal | null>(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusUpdateData, setStatusUpdateData] = useState({
    status: "" as ProposalStatus,
    admin_response: "",
  });

  const [filters, setFilters] = useState<ProposalFilters>({
    category: undefined,
    status: undefined,
    priority: undefined,
    search: "",
  });

  const [stats, setStats] = useState({
    total_proposals: 0,
    pending_proposals: 0,
    completed_proposals: 0,
    proposals_by_category: {} as Record<string, number>,
    proposals_by_status: {} as Record<string, number>,
    monthly_proposals: [] as Array<{ month: string; count: number }>,
  });

  // 데이터 로드
  useEffect(() => {
    if (currentUser) {
      loadProposals();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, filters, currentUser]);  // 통계 데이터 로드
  useEffect(() => {
    if (currentUser) {
      loadStats();
    }
  }, [currentUser]);

  const loadProposals = async () => {
    setIsLoading(true);
    try {
      const response = await getProposals(currentPage, pageSize, filters);
      setProposals(response.results);
      setTotalCount(response.count);
    } catch (error) {
      console.error("정책제안 목록 로딩 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const statsData = await getProposalStats();
      setStats(statsData);
    } catch (error) {
      console.error("통계 데이터 로딩 실패:", error);
    }
  };

  const handleFilterChange = (key: keyof ProposalFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const handleStatusUpdate = async () => {
    if (!selectedProposal || !statusUpdateData.status) return;

    try {
      const updatedProposal = await updateProposalStatus(
        selectedProposal.id,
        statusUpdateData
      );

      // 목록에서 해당 제안 업데이트
      setProposals((prev) =>
        prev.map((p) => (p.id === updatedProposal.id ? updatedProposal : p))
      );

      setShowStatusModal(false);
      setSelectedProposal(null);
      setStatusUpdateData({ status: "" as ProposalStatus, admin_response: "" });

      // 통계 다시 로드
      loadStats();

      alert("상태가 업데이트되었습니다.");
    } catch (error) {
      console.error("상태 업데이트 실패:", error);
      alert("상태 업데이트에 실패했습니다.");
    }
  };

  const openStatusModal = (proposal: PolicyProposal) => {
    setSelectedProposal(proposal);
    setStatusUpdateData({
      status: proposal.status,
      admin_response: proposal.admin_response || "",
    });
    setShowStatusModal(true);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getUrgentProposals = () => {
    return proposals.filter(
      (p) => p.priority === "urgent" && p.status === "pending"
    );
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  if (!currentUser) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">권한 확인 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* 헤더 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">정책제안 관리</h1>
        <p className="text-gray-600">
          시민들이 제출한 정책제안을 검토하고 관리할 수 있습니다.
        </p>
      </div>

      {/* 통계 대시보드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">전체 제안</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.total_proposals}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">📋</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">대기 중</p>
              <p className="text-2xl font-bold text-yellow-600">
                {stats.pending_proposals}
              </p>
            </div>
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">⏱️</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">완료</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.completed_proposals}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">✅</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">긴급 처리</p>
              <p className="text-2xl font-bold text-red-600">
                {getUrgentProposals().length}
              </p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <span className="text-2xl">🚨</span>
            </div>
          </div>
        </div>
      </div>

      {/* 긴급 제안 알림 */}
      {getUrgentProposals().length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <span className="text-red-600 text-xl mr-3">🚨</span>
            <div>
              <h3 className="text-red-800 font-semibold">
                긴급 처리가 필요한 제안이 있습니다
              </h3>
              <p className="text-red-700 text-sm mt-1">
                {getUrgentProposals().length}개의 긴급 제안이 처리를 기다리고
                있습니다.
              </p>
              <div className="mt-2 space-y-1">
                {getUrgentProposals()
                  .slice(0, 3)
                  .map((proposal) => (
                    <Link
                      key={proposal.id}
                      to={`/proposals/${proposal.id}`}
                      className="block text-red-700 hover:text-red-800 text-sm underline"
                    >
                      • {proposal.title}
                    </Link>
                  ))}
                {getUrgentProposals().length > 3 && (
                  <p className="text-red-700 text-sm">
                    ... 및 {getUrgentProposals().length - 3}개 더
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 필터 */}
      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              검색
            </label>
            <input
              type="text"
              value={filters.search || ""}
              onChange={(e) => handleFilterChange("search", e.target.value)}
              placeholder="제목, 내용, 제안자 검색..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* 제안 목록 테이블 */}
      {isLoading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">로딩 중...</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    제안
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    우선순위
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상태
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    제안자
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    제출일
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    작업
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {proposals.map((proposal) => (
                  <tr key={proposal.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <Link
                          to={`/proposals/${proposal.id}`}
                          className="text-sm font-medium text-gray-900 hover:text-blue-600"
                        >
                          {proposal.title}
                        </Link>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="px-2 py-1 rounded-full text-xs font-medium text-gray-600 bg-gray-100">
                            {CATEGORY_LABELS[proposal.category]}
                          </span>
                          {proposal.intersection_name && (
                            <span className="text-xs text-gray-500">
                              📍 {proposal.intersection_name}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          PRIORITY_LABELS[proposal.priority].color
                        }`}
                      >
                        {PRIORITY_LABELS[proposal.priority].label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          STATUS_COLORS[proposal.status]
                        }`}
                      >
                        {STATUS_LABELS[proposal.status]}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {proposal.submitted_by_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(proposal.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <Link
                          to={`/proposals/${proposal.id}`}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          보기
                        </Link>
                        <button
                          onClick={() => openStatusModal(proposal)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          상태변경
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center py-4 space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-2 rounded-md bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                이전
              </button>

              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = currentPage <= 3 ? i + 1 : currentPage - 2 + i;
                if (pageNum > totalPages) return null;

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-2 mx-1 rounded-md ${
                      pageNum === currentPage
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}

              <button
                onClick={() =>
                  setCurrentPage(Math.min(totalPages, currentPage + 1))
                }
                disabled={currentPage === totalPages}
                className="px-3 py-2 rounded-md bg-gray-200 text-gray-700 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                다음
              </button>
            </div>
          )}
        </div>
      )}

      {/* 상태 업데이트 모달 */}
      {showStatusModal && selectedProposal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">
              제안 상태 변경: {selectedProposal.title}
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  상태 *
                </label>
                <select
                  value={statusUpdateData.status}
                  onChange={(e) =>
                    setStatusUpdateData((prev) => ({
                      ...prev,
                      status: e.target.value as ProposalStatus,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(STATUS_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  관리자 답변
                </label>
                <textarea
                  value={statusUpdateData.admin_response}
                  onChange={(e) =>
                    setStatusUpdateData((prev) => ({
                      ...prev,
                      admin_response: e.target.value,
                    }))
                  }
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="제안에 대한 관리자 답변을 입력해주세요..."
                />
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowStatusModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleStatusUpdate}
                disabled={!statusUpdateData.status}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                업데이트
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminProposalManagement;
