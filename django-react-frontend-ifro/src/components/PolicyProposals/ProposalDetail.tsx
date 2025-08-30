import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  PolicyProposal,
  ProposalCategory,
  ProposalStatus,
  ProposalPriority,
} from "../../types/global.types";
import {
  getProposal,
  voteProposal,
  increaseProposalViews,
  deleteProposal,
  updateProposalStatus,
} from "../../api/proposals";
import { getCurrentUser } from "../../api/user";

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

const ProposalDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [proposal, setProposal] = useState<PolicyProposal | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [userVote, setUserVote] = useState<string | null>(null);
  const [showStatusUpdateModal, setShowStatusUpdateModal] = useState(false);
  const [statusUpdateData, setStatusUpdateData] = useState({
    status: "" as ProposalStatus,
    admin_response: "",
  });
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    if (id) {
      loadProposal();
      loadCurrentUser();
    }
  }, [id]);

  const loadCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch (error) {
      console.error("사용자 정보 로딩 실패:", error);
    }
  };

  const loadProposal = async () => {
    if (!id) return;

    setIsLoading(true);
    try {
      // 조회수 증가
      await increaseProposalViews(parseInt(id));

      // 제안 상세 정보 로드
      const data = await getProposal(parseInt(id));
      setProposal(data);
    } catch (error) {
      console.error("정책제안 로딩 실패:", error);
      alert("정책제안을 불러올 수 없습니다.");
      navigate("/proposals");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVote = async (voteType: "up" | "down") => {
    if (!proposal || !currentUser) {
      alert("로그인이 필요합니다.");
      return;
    }

    try {
      const result = await voteProposal(proposal.id, voteType);
      setProposal((prev) =>
        prev ? { ...prev, votes_count: result.votes_count } : null
      );
      setUserVote(result.user_vote);
    } catch (error) {
      console.error("투표 실패:", error);
      alert("투표에 실패했습니다.");
    }
  };

  const handleDelete = async () => {
    if (!proposal || !currentUser) return;

    try {
      await deleteProposal(proposal.id);
      alert("정책제안이 삭제되었습니다.");
      navigate("/proposals");
    } catch (error) {
      console.error("삭제 실패:", error);
      alert("삭제에 실패했습니다.");
    }
  };

  const confirmDelete = () => {
    setShowDeleteModal(true);
  };

  const handleStatusUpdate = async () => {
    if (!proposal || !statusUpdateData.status) return;

    try {
      const updatedProposal = await updateProposalStatus(
        proposal.id,
        statusUpdateData
      );
      setProposal(updatedProposal);
      setShowStatusUpdateModal(false);
      alert("상태가 업데이트되었습니다.");
    } catch (error) {
      console.error("상태 업데이트 실패:", error);
      alert("상태 업데이트에 실패했습니다.");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const canEdit =
    currentUser && proposal && currentUser.id === proposal.submitted_by;
  const canDelete = canEdit && proposal.status === "pending";
  const isAdmin = currentUser && currentUser.role === "admin";

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (!proposal) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-8">
          <p className="text-gray-600 text-lg">정책제안을 찾을 수 없습니다.</p>
          <button
            onClick={() => navigate("/proposals")}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            목록으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* 헤더 */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-800 mb-3">
              {proposal.title}
            </h1>
            <div className="flex items-center gap-3 mb-4">
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  PRIORITY_LABELS[proposal.priority].color
                }`}
              >
                {PRIORITY_LABELS[proposal.priority].label}
              </span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  STATUS_COLORS[proposal.status]
                }`}
              >
                {STATUS_LABELS[proposal.status]}
              </span>
              <span className="px-3 py-1 rounded-full text-sm font-medium text-gray-600 bg-gray-100">
                {CATEGORY_LABELS[proposal.category]}
              </span>
            </div>
          </div>

          <div className="flex gap-2">
            {canEdit && (
              <button
                onClick={() => navigate(`/proposals/${proposal.id}/edit`)}
                className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
              >
                수정
              </button>
            )}
            {canDelete && (
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                삭제
              </button>
            )}
            {isAdmin && (
              <button
                onClick={() => setShowStatusUpdateModal(true)}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
              >
                상태 변경
              </button>
            )}
          </div>
        </div>

        {/* 제안자 정보 */}
        <div className="border-t pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
            <div>
              <span className="font-medium">제안자:</span>{" "}
              {proposal.submitted_by_name}
            </div>
            <div>
              <span className="font-medium">제출일:</span>{" "}
              {formatDate(proposal.created_at)}
            </div>
            {proposal.location && (
              <div>
                <span className="font-medium">위치:</span> {proposal.location}
              </div>
            )}
            {proposal.intersection_name && (
              <div>
                <span className="font-medium">관련 교차로:</span>{" "}
                {proposal.intersection_name}
              </div>
            )}
            <div>
              <span className="font-medium">조회수:</span>{" "}
              {proposal.views_count || 0}
            </div>
            <div>
              <span className="font-medium">추천수:</span>{" "}
              {proposal.votes_count || 0}
            </div>
          </div>
        </div>
      </div>

      {/* 내용 */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">제안 내용</h2>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
            {proposal.description}
          </p>
        </div>

        {/* 태그 */}
        {proposal.tags && proposal.tags.length > 0 && (
          <div className="mt-6 pt-4 border-t">
            <h3 className="text-sm font-medium text-gray-700 mb-2">태그</h3>
            <div className="flex flex-wrap gap-2">
              {proposal.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 관리자 응답 */}
      {proposal.admin_response && (
        <div className="bg-blue-50 rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-blue-800 mb-4 flex items-center">
            <span className="mr-2">📝</span>
            관리자 답변
          </h2>
          <div className="text-gray-700 whitespace-pre-wrap leading-relaxed mb-4">
            {proposal.admin_response}
          </div>
          {proposal.admin_response_date && (
            <div className="text-sm text-blue-600">
              답변일: {formatDate(proposal.admin_response_date)}
              {proposal.admin_response_by &&
                ` by ${proposal.admin_response_by}`}
            </div>
          )}
        </div>
      )}

      {/* 추천/비추천 */}
      {currentUser && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            이 제안이 도움이 되셨나요?
          </h2>
          <div className="flex gap-4">
            <button
              onClick={() => handleVote("up")}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                userVote === "up"
                  ? "bg-green-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-green-100"
              }`}
            >
              <span>👍</span>
              도움됨
            </button>
            <button
              onClick={() => handleVote("down")}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                userVote === "down"
                  ? "bg-red-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-red-100"
              }`}
            >
              <span>👎</span>
              도움안됨
            </button>
          </div>
        </div>
      )}

      {/* 하단 버튼 */}
      <div className="flex justify-between">
        <button
          onClick={() => navigate("/proposals")}
          className="px-6 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
        >
          목록으로 돌아가기
        </button>

        <button
          onClick={() => navigate("/proposals/create")}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          새 정책제안 작성
        </button>
      </div>

      {/* 상태 업데이트 모달 */}
      {showStatusUpdateModal && isAdmin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">제안 상태 변경</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  상태
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
                  <option value="">상태 선택</option>
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
                onClick={() => setShowStatusUpdateModal(false)}
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

      {/* 삭제 확인 모달 */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-red-800">
              정책제안 삭제
            </h3>

            <p className="text-gray-700 mb-6">
              정말로 이 정책제안을 삭제하시겠습니까?
              <br />
              <strong>"{proposal?.title}"</strong>
              <br />
              삭제된 제안은 복구할 수 없습니다.
            </p>

            <div className="flex gap-2">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  handleDelete();
                }}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProposalDetail;
