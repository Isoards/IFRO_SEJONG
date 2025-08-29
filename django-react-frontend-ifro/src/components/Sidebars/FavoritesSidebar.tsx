import React from "react";
import { useTranslation } from "react-i18next";
import { Star, MapPin, AlertTriangle } from "lucide-react";
import { Intersection, Incident } from "../../types/global.types";

interface FavoritesSidebarProps {
  favoriteIntersections: Intersection[];
  favoriteIncidents: Incident[];
  onIntersectionClick: (intersection: Intersection) => void;
  onIncidentClick: (incident: Incident) => void;
  selectedIntersectionId?: number | null;
  selectedIncidentId?: number | null;
}

export const FavoritesSidebar: React.FC<FavoritesSidebarProps> = ({
  favoriteIntersections,
  favoriteIncidents,
  onIntersectionClick,
  onIncidentClick,
  selectedIntersectionId,
  selectedIncidentId,
}) => {
  const { t } = useTranslation();

  const hasFavorites =
    favoriteIntersections.length > 0 || favoriteIncidents.length > 0;

  return (
    <aside className="w-[400px] bg-white flex flex-col border-r border-gray-200 z-10 h-screen">
      <header className="px-4 py-4 border-b border-gray-200">
        <div className="px-2 space-y-4">
          <h2 className="text-lg font-bold text-yellow-600 tracking-wide">
            {t("navigation.favorites")}
          </h2>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4 bg-gray-50 space-y-4">
        {!hasFavorites ? (
          <div className="text-center py-16 text-gray-500">
            <Star className="mx-auto mb-4 text-gray-300" size={40} />
            <p className="font-semibold">{t("favorites.empty.title")}</p>
            <p className="text-sm mt-1">{t("favorites.empty.description")}</p>
          </div>
        ) : (
          <>
            {favoriteIntersections.length > 0 && (
              <section>
                <h3 className="px-2 mb-2 text-sm font-semibold text-gray-500 flex items-center">
                  <MapPin size={16} className="mr-2" />
                  {t("traffic.intersections")}
                </h3>
                <ul className="space-y-2">
                  {favoriteIntersections.map((intersection) => (
                    <li
                      key={`fav-int-${intersection.id}`}
                      className={`p-3 rounded-lg shadow-sm cursor-pointer border-l-4 ${
                        selectedIntersectionId === intersection.id
                          ? "border-blue-500 bg-blue-50"
                          : "border-transparent bg-white hover:bg-gray-100"
                      }`}
                      onClick={() => onIntersectionClick(intersection)}
                    >
                      <span className="font-medium text-sm text-gray-800">
                        {intersection.name}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {favoriteIncidents.length > 0 && (
              <section>
                <h3 className="px-2 mb-2 text-sm font-semibold text-gray-500 flex items-center">
                  <AlertTriangle size={16} className="mr-2" />
                  {t("incidents.title")}
                </h3>
                <ul className="space-y-2">
                  {favoriteIncidents.map((incident) => (
                    <li
                      key={`fav-inc-${incident.id}`}
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
                              : "bg-green-100 text-green-800"
                          }`}
                        >
                          {incident.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-800 truncate font-medium">
                        {incident.location_name || incident.intersection_name}
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </div>
    </aside>
  );
};
