import React from "react";
import {
  Car,
  ArrowRightLeft,
  AlertTriangle,
  BarChart3,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import UserMenu from "./UserMenu";

interface NavBarProps {
  activeNav: string;
  setActiveNav: (nav: string) => void;
  activeTrafficView: "analysis" | "flow" | "incidents" | "favorites";
  setActiveTrafficView: (
    view: "analysis" | "flow" | "incidents" | "favorites"
  ) => void;
  onCloseDetailPanels?: () => void; // detail panel을 닫는 함수 추가
}

export const NavBar: React.FC<NavBarProps> = ({
  activeNav,
  setActiveNav,
  activeTrafficView,
  setActiveTrafficView,
  onCloseDetailPanels,
}) => {
  const { t } = useTranslation();

  return (
    <nav className="w-16 bg-white flex flex-col items-center shadow-md z-20">
      <div className="pt-4 pb-2 flex flex-col items-center gap-2 w-full">
        <button
          onClick={() => {
            setActiveTrafficView("analysis");
            setActiveNav("map");
          }}
          title={t("navigation.analysisView") as string}
          className={`inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors h-10 w-10 ${
            activeTrafficView === "analysis" && activeNav !== "tableau"
              ? "bg-blue-600 text-white"
              : "hover:bg-gray-100"
          }`}
        >
          <Car size={20} />
        </button>
        <button
          onClick={() => {
            setActiveTrafficView("flow");
            setActiveNav("map");
          }}
          title={t("navigation.flowView") as string}
          className={`inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors h-10 w-10 ${
            activeTrafficView === "flow" && activeNav !== "tableau"
              ? "bg-green-600 text-white"
              : "hover:bg-gray-100"
          }`}
        >
          <ArrowRightLeft size={20} />
        </button>
        <button
          onClick={() => {
            setActiveTrafficView("incidents");
            setActiveNav("map");
          }}
          title={t("navigation.incidentsView") as string}
          className={`inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors h-10 w-10 ${
            activeTrafficView === "incidents" && activeNav !== "tableau"
              ? "bg-red-600 text-white"
              : "hover:bg-gray-100"
          }`}
        >
          <AlertTriangle size={20} />
        </button>
        <button
          onClick={() => {
            setActiveTrafficView("favorites");
            setActiveNav("map");
          }}
          title={t("navigation.favorites") as string}
          className={`inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors h-10 w-10 ${
            activeTrafficView === "favorites" && activeNav !== "tableau"
              ? "bg-yellow-600 text-white"
              : "hover:bg-gray-100"
          }`}
        >
          {activeTrafficView === "favorites" && activeNav !== "tableau" ? (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="white"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#222"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          )}
        </button>
      </div>
      <div className="w-full px-3 py-2">
        <div className="w-full h-px bg-gray-200" />
      </div>
      <div className="p-3">
        <button
          onClick={() => {
            if (activeNav === "tableau") {
              setActiveNav("map");
              setActiveTrafficView("analysis"); // tableau에서 나올 때 기본 뷰로 설정
            } else {
              // tableau 모드로 전환할 때 detail panel 먼저 닫기
              if (onCloseDetailPanels) {
                onCloseDetailPanels();
              }
              setActiveNav("tableau");
            }
          }}
          title={t("navigation.tableau") as string}
          className={`inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors h-10 w-10 ${
            activeNav === "tableau"
              ? "bg-purple-600 text-white"
              : "hover:bg-gray-100"
          }`}
        >
          <BarChart3 size={24} />
        </button>
      </div>
      <div className="mt-auto p-4">
        <UserMenu />
      </div>
    </nav>
  );
};
