import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ProposalCategory,
  ProposalPriority,
  CreateProposalRequest,
  Intersection,
  PolicyProposal,
} from "../../../shared/types/global.types";
import {
  getProposal,
  updateProposal,
} from "../../../shared/services/proposals";
import { getTrafficIntersections } from "../../../shared/services/intersections";
import { getCurrentUser } from "../../../shared/services/user";

const CATEGORY_OPTIONS: { value: ProposalCategory; label: string }[] = [
  { value: "traffic_signal", label: "신호등 관련" },
  { value: "road_safety", label: "도로 안전" },
  { value: "traffic_flow", label: "교통 흐름" },
  { value: "infrastructure", label: "인프라 개선" },
  { value: "policy", label: "교통 정책" },
  { value: "other", label: "기타" },
];

const PRIORITY_OPTIONS: {
  value: ProposalPriority;
  label: string;
  color: string;
}[] = [
  { value: "low", label: "낮음", color: "text-green-600" },
  { value: "medium", label: "보통", color: "text-yellow-600" },
  { value: "high", label: "높음", color: "text-orange-600" },
  { value: "urgent", label: "긴급", color: "text-red-600" },
];

const EditProposalForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [proposal, setProposal] = useState<PolicyProposal | null>(null);
  const [intersections, setIntersections] = useState<Intersection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState<CreateProposalRequest>({
    title: "",
    description: "",
    category: "other",
    priority: "medium",
    location: "",
    intersection_id: undefined,
    tags: [],
  });
  const [tagInput, setTagInput] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 현재 사용자와 제안 데이터 로드
  useEffect(() => {
    const loadData = async () => {
      if (!id) {
        navigate("/proposals");
        return;
      }

      try {
        // 사용자 정보 로드
        const user = await getCurrentUser();

        // 제안 정보 로드
        const proposalData = await getProposal(parseInt(id));

        // 작성자 확인
        if (user && user.id !== proposalData.submitted_by) {
          alert("자신이 작성한 제안만 수정할 수 있습니다.");
          navigate(`/proposals/${id}`);
          return;
        }

        // 수정 가능한 상태 확인
        if (proposalData.status !== "pending") {
          alert("대기 중인 제안만 수정할 수 있습니다.");
          navigate(`/proposals/${id}`);
          return;
        }

        setProposal(proposalData);
        setFormData({
          title: proposalData.title,
          description: proposalData.description,
          category: proposalData.category,
          priority: proposalData.priority,
          location: proposalData.location || "",
          intersection_id: proposalData.intersection_id,
          tags: proposalData.tags || [],
        });

        // 교차로 목록 로드
        const intersectionData = await getTrafficIntersections();
        setIntersections(intersectionData);
      } catch (error) {
        console.error("데이터 로딩 실패:", error);
        alert("제안 정보를 불러올 수 없습니다.");
        navigate("/proposals");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [id, navigate]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = "제목을 입력해주세요.";
    } else if (formData.title.length < 5) {
      newErrors.title = "제목은 최소 5자 이상 입력해주세요.";
    }

    if (!formData.description.trim()) {
      newErrors.description = "내용을 입력해주세요.";
    } else if (formData.description.length < 20) {
      newErrors.description = "내용은 최소 20자 이상 입력해주세요.";
    }

    if (!formData.category) {
      newErrors.category = "카테고리를 선택해주세요.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm() || !proposal) {
      return;
    }

    setIsSaving(true);
    try {
      await updateProposal(proposal.id, formData);
      alert("정책제안이 성공적으로 수정되었습니다!");
      navigate(`/proposals/${proposal.id}`);
    } catch (error) {
      console.error("정책제안 수정 실패:", error);
      alert("정책제안 수정에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleTagAdd = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData((prev) => ({
        ...prev,
        tags: [...(prev.tags || []), tagInput.trim()],
      }));
      setTagInput("");
    }
  };

  const handleTagRemove = (tagToRemove: string) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags?.filter((tag) => tag !== tagToRemove) || [],
    }));
  };

  const handleIntersectionChange = (intersectionId: string) => {
    const selectedIntersection = intersections.find(
      (i) => i.id.toString() === intersectionId
    );

    setFormData((prev) => ({
      ...prev,
      intersection_id: intersectionId ? parseInt(intersectionId) : undefined,
      location: selectedIntersection
        ? selectedIntersection.name
        : prev.location,
    }));
  };

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
          <p className="text-gray-600 text-lg">제안을 찾을 수 없습니다.</p>
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
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">정책제안 수정</h1>
        <p className="text-gray-600">
          제안 내용을 수정할 수 있습니다. 검토 중인 제안은 수정할 수 없습니다.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 제목 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            제목 *
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, title: e.target.value }))
            }
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.title ? "border-red-500" : "border-gray-300"
            }`}
            placeholder="정책제안 제목을 입력해주세요"
            maxLength={200}
          />
          {errors.title && (
            <p className="mt-1 text-sm text-red-600">{errors.title}</p>
          )}
        </div>

        {/* 카테고리와 우선순위 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              카테고리 *
            </label>
            <select
              value={formData.category}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  category: e.target.value as ProposalCategory,
                }))
              }
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.category ? "border-red-500" : "border-gray-300"
              }`}
            >
              {CATEGORY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.category && (
              <p className="mt-1 text-sm text-red-600">{errors.category}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              우선순위
            </label>
            <select
              value={formData.priority}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  priority: e.target.value as ProposalPriority,
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PRIORITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 위치 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              관련 교차로
            </label>
            <select
              value={formData.intersection_id || ""}
              onChange={(e) => handleIntersectionChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">교차로 선택 (선택사항)</option>
              {intersections.map((intersection) => (
                <option key={intersection.id} value={intersection.id}>
                  {intersection.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              위치 설명
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, location: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="구체적인 위치나 주소 (선택사항)"
            />
          </div>
        </div>

        {/* 내용 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            내용 *
          </label>
          <textarea
            value={formData.description}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, description: e.target.value }))
            }
            rows={8}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.description ? "border-red-500" : "border-gray-300"
            }`}
            placeholder="정책제안 내용을 상세히 설명해주세요. 현재 문제점, 개선 방안, 기대 효과 등을 포함해주시면 더 좋습니다."
          />
          {errors.description && (
            <p className="mt-1 text-sm text-red-600">{errors.description}</p>
          )}
          <p className="mt-1 text-sm text-gray-500">
            {formData.description.length}/2000자
          </p>
        </div>

        {/* 태그 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            태그
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyPress={(e) =>
                e.key === "Enter" && (e.preventDefault(), handleTagAdd())
              }
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="태그를 입력하고 Enter 또는 추가 버튼을 누르세요"
            />
            <button
              type="button"
              onClick={handleTagAdd}
              className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600"
            >
              추가
            </button>
          </div>
          {formData.tags && formData.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {formData.tags.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleTagRemove(tag)}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 버튼 */}
        <div className="flex gap-4 pt-4">
          <button
            type="button"
            onClick={() => navigate(`/proposals/${proposal.id}`)}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isSaving}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? "저장 중..." : "수정 완료"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditProposalForm;
