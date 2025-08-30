import React from "react";
import { useTranslation } from "react-i18next";
import { X, GripVertical } from "lucide-react";
import { Incident } from "../../../shared/types/global.types";

interface IncidentDetailPanelProps {
  incident: Incident;
  onClose: () => void;
  onWidthChange?: (widthPercentage: number) => void;
}

// 긴 텍스트 2줄까지 자르고, 마우스 오버 시 전체 표시
const TwoLineTruncate: React.FC<{ text: string }> = ({ text }) => (
  <span
    className="block text-sm font-medium text-gray-900 leading-relaxed"
    style={{
      display: "-webkit-box",
      WebkitLineClamp: 2,
      WebkitBoxOrient: "vertical",
      overflow: "hidden",
      textOverflow: "ellipsis",
      wordBreak: "break-word",
      lineHeight: "1.4",
      maxHeight: "2.8em",
      cursor: "pointer",
    }}
    title={text}
  >
    {text}
  </span>
);

// 한 줄 ... 처리, 마우스 오버 시 전체 표시
const OneLineTruncate: React.FC<{ text: string }> = ({ text }) => (
  <span
    className="block text-sm font-medium text-gray-900 truncate"
    style={{ maxWidth: "100%", cursor: "pointer" }}
    title={text}
  >
    {text}
  </span>
);

export const IncidentDetailPanel: React.FC<IncidentDetailPanelProps> = ({
  incident,
  onClose,
  onWidthChange,
}) => {
  const { t } = useTranslation();

  // 드래그 리사이저 상태
  const [isDragging, setIsDragging] = React.useState(false);
  const dragStartX = React.useRef(0);
  const startWidth = React.useRef(0);

  // 드래그 시작
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!onWidthChange) return;
    setIsDragging(true);
    dragStartX.current = e.clientX;
    startWidth.current = window.innerWidth * 0.35; // 현재 패널 너비 (35% 기본값)
    e.preventDefault();
  };

  // 드래그 중
  const handleMouseMove = React.useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !onWidthChange) return;

      const deltaX = dragStartX.current - e.clientX; // 왼쪽으로 드래그하면 양수
      const newWidth = startWidth.current + deltaX;
      const widthPercentage = Math.max(
        20,
        Math.min(60, (newWidth / window.innerWidth) * 100)
      );

      onWidthChange(widthPercentage);
    },
    [isDragging, onWidthChange]
  );

  // 드래그 종료
  const handleMouseUp = React.useCallback(() => {
    setIsDragging(false);
  }, []);

  // 드래그 이벤트 리스너 등록/해제
  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "ew-resize";
      document.body.style.userSelect = "none";
    } else {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div className="h-full w-full mx-auto bg-white relative overflow-y-auto flex">
      {/* 드래그 리사이저 */}
      {onWidthChange && (
        <div
          className="absolute left-0 top-0 w-1 h-full bg-gray-300 hover:bg-red-500 cursor-ew-resize flex items-center justify-center transition-colors z-50"
          onMouseDown={handleMouseDown}
          style={{
            background: isDragging ? "#ef4444" : undefined,
          }}
        >
          <div className="w-4 h-8 bg-gray-400 hover:bg-red-500 rounded-r flex items-center justify-center">
            <GripVertical size={12} className="text-white" />
          </div>
        </div>
      )}

      <div className="flex-1 p-6 pt-4 overflow-y-auto">
        {/* 드래그 오버레이 */}
        {isDragging && (
          <div className="fixed inset-0 z-40" style={{ cursor: "ew-resize" }} />
        )}
        {/* 헤더 영역 */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold text-red-600 mb-1 truncate">
              {t("incidents.title")} {t("traffic.analysis")}
            </h2>
            <p className="text-xs text-gray-500">
              사고 상세 정보 및 교통 영향 분석
            </p>
          </div>

          {/* 액션 버튼 그룹 */}
          <div className="flex items-center gap-2 ml-4 flex-shrink-0">
            {/* 닫기 버튼 */}
            <button
              onClick={onClose}
              aria-label="Close panel"
              className="flex items-center justify-center w-8 h-8 rounded-lg border border-red-400 text-red-500 hover:text-red-700 hover:bg-red-50 hover:border-red-500 transition-all duration-200"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* 상단 요약 카드 */}
        <div className="bg-gradient-to-br from-red-50 to-pink-50 border border-red-100 rounded-xl p-4 mb-6">
          <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            사고 개요
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-white rounded-lg p-3 border border-red-100 shadow-sm">
              <div className="text-center">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  {t("incidents.type")}
                </p>
                <TwoLineTruncate text={incident.incident_type} />
              </div>
            </div>

            <div className="bg-white rounded-lg p-3 border border-red-100 shadow-sm">
              <div className="text-center">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  {t("incidents.status")}
                </p>
                <OneLineTruncate text={incident.status} />
              </div>
            </div>
          </div>
        </div>

        {/* 위치 정보 섹션 */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            {t("incidents.locationInfo")}
          </h3>
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-800 mb-3">
                {t("incidents.location")}
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">위치:</span>
                  <span
                    className="text-sm font-medium text-gray-900 max-w-xs truncate"
                    title={
                      incident.location_name ||
                      incident.intersection_name ||
                      "N/A"
                    }
                  >
                    {incident.location_name ||
                      incident.intersection_name ||
                      "N/A"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">구역:</span>
                  <span className="text-sm font-medium text-blue-700 bg-blue-100 px-2 py-1 rounded">
                    {incident.district}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-800 mb-3">
                관리 정보
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {t("incidents.managedBy")}:
                  </span>
                  <span
                    className="text-sm font-medium text-gray-900 max-w-xs truncate"
                    title={incident.managed_by}
                  >
                    {incident.managed_by}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {t("incidents.assignedTo")}:
                  </span>
                  <span className="text-sm font-medium text-green-700 bg-green-100 px-2 py-1 rounded">
                    {incident.assigned_to}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 추가 정보 섹션 */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
            {t("incidents.additionalInfo")}
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Incident ID:</span>
                <span className="text-sm font-medium text-gray-900">
                  #{incident.id}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">등록일:</span>
                <span className="text-sm font-medium text-gray-900">
                  {new Date(incident.registered_at).toLocaleDateString()}
                </span>
              </div>
              {incident.incident_number && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    Incident Number:
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {String(incident.incident_number)}
                  </span>
                </div>
              )}
              {incident.ticket_number && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Ticket Number:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {String(incident.ticket_number)}
                  </span>
                </div>
              )}
              {incident.operator && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Operator:</span>
                  <span className="text-sm font-medium text-gray-900">
                    {String(incident.operator)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 타임라인 섹션 */}
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            {t("incidents.timeline")}
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">등록 시간:</span>
                <span className="text-sm font-medium text-gray-900">
                  {new Date(incident.registered_at).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">최종 업데이트:</span>
                <span className="text-sm font-medium text-gray-900">
                  {new Date(incident.last_status_update).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 설명 섹션 */}
        {incident.description && (
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              {t("incidents.description")}
            </h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                {incident.description}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
