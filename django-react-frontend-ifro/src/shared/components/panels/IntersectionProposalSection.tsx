import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  Eye,
  ThumbsUp,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ChevronRight,
} from "lucide-react";
import {
  PolicyProposal,
  ProposalListResponse,
  Intersection,
  ProposalStatus,
  ProposalCategory,
  ProposalPriority,
} from "../../types/global.types";
import { getProposalsByIntersectionId } from "../../services/proposals";

interface IntersectionProposalSectionProps {
  intersection: Intersection;
  onRefresh?: (refreshFunction: () => void) => void; // 새로고침 함수를 등록하는 콜백
}

// 상태별 색상과 아이콘 매핑
const STATUS_CONFIG: Record<
  ProposalStatus,
  { color: string; bgColor: string; icon: React.ReactNode; label: string }
> = {
  pending: {
    color: "text-yellow-600",
    bgColor: "bg-yellow-100",
    icon: <Clock size={12} />,
    label: "대기 중",
  },
  under_review: {
    color: "text-blue-600",
    bgColor: "bg-blue-100",
    icon: <Eye size={12} />,
    label: "검토 중",
  },
  in_progress: {
    color: "text-purple-600",
    bgColor: "bg-purple-100",
    icon: <AlertTriangle size={12} />,
    label: "진행 중",
  },
  completed: {
    color: "text-green-600",
    bgColor: "bg-green-100",
    icon: <CheckCircle size={12} />,
    label: "완료",
  },
  rejected: {
    color: "text-red-600",
    bgColor: "bg-red-100",
    icon: <XCircle size={12} />,
    label: "반려",
  },
};

// 카테고리별 라벨 매핑
const CATEGORY_LABELS: Record<ProposalCategory, string> = {
  traffic_signal: "신호등",
  road_safety: "도로안전",
  traffic_flow: "교통흐름",
  infrastructure: "인프라",
  policy: "정책",
  other: "기타",
};

// 우선순위별 색상 매핑
const PRIORITY_COLORS: Record<ProposalPriority, string> = {
  low: "text-green-600",
  medium: "text-yellow-600",
  high: "text-orange-600",
  urgent: "text-red-600",
};

export const IntersectionProposalSection: React.FC<
  IntersectionProposalSectionProps
> = ({ intersection, onRefresh }) => {
  const navigate = useNavigate();
  const [proposals, setProposals] = useState<PolicyProposal[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 정책제안 데이터 로드
  useEffect(() => {
    const loadProposals = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response: ProposalListResponse =
          await getProposalsByIntersectionId(
            intersection.id,
            1,
            3 // 최대 3개만 표시
          );
        setProposals(response.results);
        setTotalCount(response.count);
      } catch (err) {
        console.error("정책제안 로딩 실패:", err);
        setError("정책제안을 불러오는데 실패했습니다.");
      } finally {
        setIsLoading(false);
      }
    };

    loadProposals();
  }, [intersection.id]);

  // 데이터 새로고침 함수
  const refreshProposals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response: ProposalListResponse = await getProposalsByIntersectionId(
        intersection.id,
        1,
        3
      );
      setProposals(response.results);
      setTotalCount(response.count);
    } catch (err) {
      console.error("정책제안 새로고침 실패:", err);
      setError("정책제안을 불러오는데 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, [intersection.id]);

  // 외부에서 새로고침 요청 시 처리
  useEffect(() => {
    if (onRefresh) {
      onRefresh(refreshProposals);
    }
  }, [onRefresh, refreshProposals]);

  // 컴포넌트 마운트 시 정책제안 목록 로드
  useEffect(() => {
    refreshProposals();
  }, [refreshProposals]);

  // 정책제안 상세 페이지로 이동
  const handleViewProposal = (proposalId: number) => {
    navigate(`/proposals/${proposalId}`);
  };

  // 전체 목록 페이지로 이동
  const handleViewAll = () => {
    navigate(`/proposals?intersection_id=${intersection.id}`);
  };

  // 제목 줄임 처리
  const truncateTitle = (title: string, maxLength: number = 40) => {
    return title.length > maxLength ? title.slice(0, maxLength) + "..." : title;
  };

  // 날짜 포맷팅
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return "오늘";
    } else if (diffDays === 1) {
      return "어제";
    } else if (diffDays < 7) {
      return `${diffDays}일 전`;
    } else {
      return date.toLocaleDateString("ko-KR", {
        month: "short",
        day: "numeric",
      });
    }
  };

  if (isLoading) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-gray-800 flex items-center">
            <FileText size={16} className="mr-2" />
            관련 정책제안
          </h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-sm text-gray-500">로딩 중...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-gray-800 flex items-center">
            <FileText size={16} className="mr-2" />
            관련 정책제안
          </h3>
        </div>
        <div className="text-center py-4">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-semibold text-gray-800 flex items-center">
          <FileText size={16} className="mr-2" />
          관련 정책제안
          {totalCount > 0 && (
            <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-600 rounded-full">
              {totalCount}
            </span>
          )}
        </h3>
      </div>

      {proposals.length === 0 ? (
        <div className="text-center py-6">
          <FileText size={32} className="mx-auto text-gray-400 mb-2" />
          <p className="text-sm text-gray-500 mb-3">
            이 교차로에 대한 정책제안이 없습니다.
          </p>
          <p className="text-xs text-gray-400">
            위쪽의 "정책제안" 버튼을 클릭하여 첫 번째 제안을 작성해보세요.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {proposals.map((proposal) => {
            const statusConfig = STATUS_CONFIG[proposal.status];
            return (
              <div
                key={proposal.id}
                className="bg-white rounded-lg p-3 border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
                onClick={() => handleViewProposal(proposal.id)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-gray-800 truncate">
                      {truncateTitle(proposal.title)}
                    </h4>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-xs text-gray-500">
                        {CATEGORY_LABELS[proposal.category]}
                      </span>
                      <span className="text-xs text-gray-400">•</span>
                      <span
                        className={`text-xs ${
                          PRIORITY_COLORS[proposal.priority]
                        }`}
                      >
                        {proposal.priority === "low" && "낮음"}
                        {proposal.priority === "medium" && "보통"}
                        {proposal.priority === "high" && "높음"}
                        {proposal.priority === "urgent" && "긴급"}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center ml-2">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusConfig.bgColor} ${statusConfig.color}`}
                    >
                      {statusConfig.icon}
                      <span className="ml-1">{statusConfig.label}</span>
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-3">
                    <span className="flex items-center">
                      <Eye size={12} className="mr-1" />
                      {proposal.views_count || 0}
                    </span>
                    <span className="flex items-center">
                      <ThumbsUp size={12} className="mr-1" />
                      {proposal.votes_count || 0}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span>{formatDate(proposal.created_at)}</span>
                    <ChevronRight size={12} className="ml-1" />
                  </div>
                </div>
              </div>
            );
          })}

          {totalCount > proposals.length && (
            <button
              onClick={handleViewAll}
              className="w-full py-2 text-sm text-blue-600 hover:text-blue-700 border border-blue-200 rounded-md hover:bg-blue-50 transition-colors"
            >
              전체 {totalCount}개 제안 보기
            </button>
          )}
        </div>
      )}
    </div>
  );
};
