import api from "./axios";
import {
  PolicyProposal,
  CreateProposalRequest,
  UpdateProposalStatusRequest,
  ProposalListResponse,
  ProposalFilters,
} from "../types/global.types";

const PROPOSALS_BASE_URL = "proposals";

// 정책제안 목록 조회 (페이지네이션, 필터링 지원)
export async function getProposals(
  page: number = 1,
  pageSize: number = 10,
  filters?: ProposalFilters
): Promise<ProposalListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        params.append(key, value.toString());
      }
    });
  }

  const response = await api.get(`${PROPOSALS_BASE_URL}/?${params.toString()}`);
  return response.data;
}

// 내가 제출한 정책제안 목록 조회
export async function getMyProposals(
  page: number = 1,
  pageSize: number = 10
): Promise<ProposalListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  const response = await api.get(
    `${PROPOSALS_BASE_URL}/my/?${params.toString()}`
  );
  return response.data;
}

// 정책제안 상세 조회
export async function getProposal(id: number): Promise<PolicyProposal> {
  const response = await api.get(`${PROPOSALS_BASE_URL}/${id}/`);
  return response.data;
}

// 정책제안 생성
export async function createProposal(
  proposalData: CreateProposalRequest
): Promise<PolicyProposal> {
  const response = await api.post(`${PROPOSALS_BASE_URL}/`, proposalData);
  return response.data;
}

// 정책제안 수정 (본인이 작성한 경우만)
export async function updateProposal(
  id: number,
  proposalData: Partial<CreateProposalRequest>
): Promise<PolicyProposal> {
  const response = await api.patch(
    `${PROPOSALS_BASE_URL}/${id}/`,
    proposalData
  );
  return response.data;
}

// 정책제안 삭제 (본인이 작성한 경우만)
export async function deleteProposal(id: number): Promise<void> {
  await api.delete(`${PROPOSALS_BASE_URL}/${id}/`);
}

// 관리자용: 정책제안 상태 업데이트
export async function updateProposalStatus(
  id: number,
  statusData: UpdateProposalStatusRequest
): Promise<PolicyProposal> {
  const response = await api.patch(
    `${PROPOSALS_BASE_URL}/${id}/status/`,
    statusData
  );
  return response.data;
}

// 정책제안에 투표하기 (추천/비추천)
export async function voteProposal(
  id: number,
  voteType: "up" | "down"
): Promise<{ votes_count: number; user_vote: string }> {
  const response = await api.post(`${PROPOSALS_BASE_URL}/${id}/vote/`, {
    vote_type: voteType,
  });
  return response.data;
}

// 정책제안 조회수 증가
export async function increaseProposalViews(id: number): Promise<void> {
  await api.post(`${PROPOSALS_BASE_URL}/${id}/view/`);
}

// 첨부파일 업로드
export async function uploadProposalAttachment(
  proposalId: number,
  file: File
): Promise<{ file_url: string; file_name: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(
    `${PROPOSALS_BASE_URL}/${proposalId}/attachments/`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
}

// 정책제안 통계 (관리자용)
export async function getProposalStats(): Promise<{
  total_proposals: number;
  pending_proposals: number;
  completed_proposals: number;
  proposals_by_category: Record<string, number>;
  proposals_by_status: Record<string, number>;
  monthly_proposals: Array<{ month: string; count: number }>;
}> {
  const response = await api.get(`${PROPOSALS_BASE_URL}/stats/`);
  return response.data;
}

// 카테고리별 제안 수 조회
export async function getProposalsByCategory(): Promise<
  Record<string, number>
> {
  const response = await api.get(`${PROPOSALS_BASE_URL}/by-category/`);
  return response.data;
}

// 교차로별 제안 수 조회
export async function getProposalsByIntersection(): Promise<
  Array<{ intersection_id: number; intersection_name: string; count: number }>
> {
  const response = await api.get(`${PROPOSALS_BASE_URL}/by-intersection/`);
  return response.data;
}
