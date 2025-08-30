import React, { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Incident } from "../../types/global.types";
import { Search } from "lucide-react";

interface IncidentSidebarProps {
  incidents: Incident[];
  onIncidentClick: (incident: Incident) => void;
  selectedIncidentId?: number | null;
}

export const IncidentSidebar: React.FC<IncidentSidebarProps> = ({
  incidents,
  onIncidentClick,
  selectedIncidentId,
}) => {
  const { t } = useTranslation();
  // 유형별 필터 상태
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  // 유형 목록 추출
  const incidentTypes = useMemo(
    () => Array.from(new Set(incidents.map((i) => i.incident_type))),
    [incidents]
  );

  // 필터링된 리스트
  const filteredIncidents = useMemo(
    () =>
      incidents.filter(
        (i) =>
          (!selectedType || i.incident_type === selectedType) &&
          (search === "" ||
            i.location_name?.toLowerCase().includes(search.toLowerCase()) ||
            i.intersection_name?.toLowerCase().includes(search.toLowerCase()))
      ),
    [incidents, selectedType, search]
  );

  return (
    <aside className="w-[400px] bg-white flex flex-col border-r border-gray-200 z-10 h-screen">
      <div className="flex flex-col">
        <header className="px-4 py-4 border-b border-gray-200">
          <div className="px-2 space-y-4">
            <h2 className="text-lg font-bold text-red-600 tracking-wide">
              {t("incidents.title")} {t("traffic.analysis")}
            </h2>
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                size={20}
              />
              <input
                type="text"
                placeholder={t("common.search") + "..."}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-gray-100 border-transparent rounded-md py-2 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
              />
            </div>
          </div>
        </header>
        <div className="p-4">
          <div className="px-2">
            <div className="flex flex-wrap gap-2 mb-2">
              <button
                className={`px-3 py-1 rounded-full text-xs border ${
                  selectedType === null
                    ? "bg-red-500 text-white border-red-500"
                    : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                } transition`}
                onClick={() => setSelectedType(null)}
              >
                {t("common.all")}
              </button>
              {incidentTypes.map((type) => (
                <button
                  key={type}
                  className={`px-3 py-1 rounded-full text-xs border ${
                    selectedType === type
                      ? "bg-red-500 text-white border-red-500"
                      : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                  } transition`}
                  onClick={() => setSelectedType(type)}
                >
                  {type}
                </button>
              ))}
            </div>
            <div className="text-xs text-gray-500">
              {filteredIncidents.length} {t("incidents.title").toLowerCase()}
            </div>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50 space-y-3">
        <ul className="space-y-2">
          {filteredIncidents.map((incident) => (
            <li
              key={incident.id}
              id={`incident-${incident.id}`}
              className={`p-3 rounded-lg shadow-sm cursor-pointer border-l-4 ${
                selectedIncidentId === incident.id
                  ? "border-red-500 bg-red-50"
                  : "border-transparent bg-white hover:bg-gray-100"
              }`}
              onClick={() => onIncidentClick(incident)}
            >
              <div className="flex justify-between items-center mb-1">
                <span className="font-semibold text-red-700 text-xs">
                  {incident.incident_type}
                </span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    incident.status === "OPEN"
                      ? "bg-yellow-100 text-yellow-800"
                      : incident.status === "RESOLVED"
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {incident.status}
                </span>
              </div>
              <div className="text-sm text-gray-800 truncate font-medium">
                {incident.location_name || incident.intersection_name}
              </div>
              <div className="text-xs text-gray-500 pt-1">
                {incident.district} |{" "}
                {new Date(incident.registered_at).toLocaleDateString()}
              </div>
            </li>
          ))}
          {filteredIncidents.length === 0 && (
            <li className="text-gray-400 text-sm py-4 text-center">
              {t("dashboard.noData")}
            </li>
          )}
        </ul>
      </div>
    </aside>
  );
};
