import React from "react";
import { useTranslation } from "react-i18next";
import { X, MapPin, Info, Calendar, ClipboardList } from "lucide-react";
import { Incident } from "../../types/global.types";

interface IncidentDetailPanelProps {
  incident: Incident;
  onClose: () => void;
}

// 긴 텍스트 2줄까지 자르고, 마우스 오버 시 전체 표시
const TwoLineTruncate: React.FC<{ text: string }> = ({ text }) => (
  <span
    className="block text-lg font-bold text-gray-900 tracking-tight overflow-hidden whitespace-pre-line"
    style={{
      display: "-webkit-box",
      WebkitLineClamp: 2,
      WebkitBoxOrient: "vertical",
      overflow: "hidden",
      textOverflow: "ellipsis",
      wordBreak: "break-all",
      lineHeight: "1.2",
      maxHeight: "2.6em",
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
    className="block font-bold text-gray-900 truncate"
    style={{ maxWidth: "100%", cursor: "pointer" }}
    title={text}
  >
    {text}
  </span>
);

export const IncidentDetailPanel: React.FC<IncidentDetailPanelProps> = ({
  incident,
  onClose,
}) => {
  const { t } = useTranslation();

  return (
    <div className="h-full p-8 pt-4 bg-white relative max-w-[700px] w-full mx-auto">
      {/* 상단 타이틀 + 닫기 버튼 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-red-600">
          {t("incidents.title")} {t("traffic.analysis")}
        </h2>
        <button
          onClick={onClose}
          aria-label="Close panel"
          className="inline-flex items-center justify-center h-10 w-10 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground ml-2"
        >
          <X size={28} className="text-gray-500" />
        </button>
      </div>

      {/* 상단 요약 */}
      <div className="mb-6">
        <div className="flex-1">
          <div className="flex flex-wrap gap-4 items-start">
            <div className="p-4 bg-white rounded-lg shadow-sm min-w-[180px]">
              <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                <Info size={16} /> {t("incidents.type")}
              </p>
              <TwoLineTruncate text={incident.incident_type} />
            </div>
            <div className="p-4 bg-white rounded-lg shadow-sm min-w-[120px]">
              <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                <ClipboardList size={16} /> {t("incidents.status")}
              </p>
              <OneLineTruncate text={incident.status} />
            </div>
            <div className="p-4 bg-white rounded-lg shadow-sm min-w-[100px]">
              <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                <Info size={16} /> Incident ID
              </p>
              <OneLineTruncate text={`#${incident.id}`} />
            </div>
            <div className="p-4 bg-white rounded-lg shadow-sm min-w-[120px]">
              <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                <Calendar size={16} /> {t("incidents.registeredAt")}
              </p>
              <OneLineTruncate
                text={new Date(incident.registered_at).toLocaleDateString()}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 주요 정보 섹션 */}
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <MapPin size={18} /> {t("incidents.locationInfo")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <p className="text-xs text-gray-500 mb-1">
              {t("incidents.location")}
            </p>
            <TwoLineTruncate
              text={
                incident.location_name || incident.intersection_name || "N/A"
              }
            />
            <p className="text-xs text-gray-500 mt-2">
              District{" "}
              <span className="font-bold text-gray-800 ml-2">
                {incident.district}
              </span>
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <p className="text-xs text-gray-500 mb-1">
              {t("incidents.managedBy")}
            </p>
            <OneLineTruncate text={incident.managed_by} />
            <p className="text-xs text-gray-500 mt-2">
              {t("incidents.assignedTo")}{" "}
              <span className="font-bold text-gray-800 ml-2">
                {incident.assigned_to}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* 기타 정보 섹션 */}
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Info size={18} /> {t("incidents.additionalInfo")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {incident.incident_number && (
            <div className="bg-white rounded-lg shadow-sm p-4">
              <p className="text-xs text-gray-500 mb-1">Incident Number</p>
              <OneLineTruncate text={String(incident.incident_number)} />
            </div>
          )}
          {incident.ticket_number && (
            <div className="bg-white rounded-lg shadow-sm p-4">
              <p className="text-xs text-gray-500 mb-1">Ticket Number</p>
              <OneLineTruncate text={String(incident.ticket_number)} />
            </div>
          )}
          {incident.operator && (
            <div className="bg-white rounded-lg shadow-sm p-4">
              <p className="text-xs text-gray-500 mb-1">Operator</p>
              <OneLineTruncate text={String(incident.operator)} />
            </div>
          )}
        </div>
      </div>

      {/* 타임라인/설명 섹션 */}
      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Calendar size={18} /> {t("incidents.timeline")}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <p className="text-xs text-gray-500 mb-1">Registered At</p>
            <span className="text-base font-semibold text-gray-900">
              {new Date(incident.registered_at).toLocaleString()}
            </span>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <p className="text-xs text-gray-500 mb-1">Last Status Update</p>
            <span className="text-base font-semibold text-gray-900">
              {new Date(incident.last_status_update).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Info size={18} /> {t("incidents.description")}
        </h3>
        <div className="bg-white rounded-lg shadow-sm p-4">
          <div className="text-base text-gray-700 leading-relaxed whitespace-pre-line">
            {incident.description ? (
              <TwoLineTruncate text={incident.description} />
            ) : (
              <span className="text-gray-400">No description provided.</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
