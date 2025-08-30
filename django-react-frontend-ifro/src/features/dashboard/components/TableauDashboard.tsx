import React, { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { BarChart3, ExternalLink } from "lucide-react";

interface TableauDashboardProps {
  className?: string;
}

export const TableauDashboard: React.FC<TableauDashboardProps> = ({
  className = "",
}) => {
  const { t, i18n } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadTableauEmbeddingAPI = async () => {
      // Embedding API v3 스크립트 로드 확인
      if (document.querySelector('script[src*="tableau.embedding.3"]')) {
        return;
      }

      // 새로운 Embedding API v3 스크립트 로드
      const script = document.createElement("script");
      script.type = "module";
      script.src =
        "https://public.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js";
      script.async = true;
      document.head.appendChild(script);

      // 스크립트 로드 완료 대기
      await new Promise<void>((resolve) => {
        script.onload = () => resolve();
        script.onerror = () => resolve(); // 에러가 나도 계속 진행
      });
    };

    const initializeTableauViz = () => {
      if (!containerRef.current) return;

      // 기존 컨텐츠 제거
      containerRef.current.innerHTML = "";

      // tableau-viz 웹 컴포넌트 생성
      const tableauViz = document.createElement("tableau-viz");
      tableauViz.setAttribute("id", "tableauViz");
      // 영어 태블로 대시보드 URL 사용
      tableauViz.setAttribute(
        "src",
        "https://public.tableau.com/shared/DQ378Q5T9?:display_count=n&:origin=viz_share_link"
      );
      tableauViz.setAttribute("width", "100%");
      tableauViz.setAttribute("height", "950px");
      tableauViz.setAttribute("toolbar", "bottom");
      tableauViz.setAttribute("hide-tabs", "true");
      tableauViz.setAttribute("device", "desktop");
      tableauViz.setAttribute("toolbar-position", "bottom");

      // 전체 화면 활용
      tableauViz.style.width = "100%";
      tableauViz.style.height = "950px";
      tableauViz.style.minWidth = "1200px";

      // 컨테이너에 추가
      containerRef.current.appendChild(tableauViz);
    };

    // 초기화 실행
    loadTableauEmbeddingAPI().then(() => {
      // 약간의 지연 후 초기화 (스크립트 로드 완료 대기)
      setTimeout(initializeTableauViz, 1000);
    });
  }, [i18n.language]); // 언어가 변경될 때마다 태블로 재로드

  return (
    <div className={`w-full h-full ${className}`}>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BarChart3 className="h-6 w-6 text-white" />
              <h2 className="text-xl font-semibold text-white">
                {t("dashboard.title")}
              </h2>
            </div>
            <a
              href="https://public.tableau.com/shared/DQ378Q5T9?:display_count=n&:origin=viz_share_link"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-1 bg-white/20 text-white rounded-md hover:bg-white/30 transition-colors text-sm"
            >
              <ExternalLink className="w-4 h-4 mr-1" />
              {t("navigation.tableau")}
            </a>
          </div>
        </div>

        <div className="p-6">
          <div
            className="w-full bg-gray-50 rounded-lg border border-gray-200 overflow-auto"
            style={{ padding: "20px", width: "100%" }}
          >
            <div
              ref={containerRef}
              className="w-full min-h-[950px] flex items-center justify-center"
              style={{
                minHeight: "950px",
                width: "100%",
                overflowX: "auto",
                display: "flex",
                justifyContent: "center",
              }}
            >
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">{t("dashboard.loading")}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TableauDashboard;
