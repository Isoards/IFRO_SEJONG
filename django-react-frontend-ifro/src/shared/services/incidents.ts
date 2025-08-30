import api from "./axios";
import { debugLog } from "../utils/debugUtils";
import { Incident } from "../types/global.types";

export const getIncidents = async (): Promise<Incident[]> => {
  debugLog("Fetching all incidents...");
  const response = await api.get("traffic/incidents");
  debugLog("Received incidents data:", response.data);
  return response.data;
};

export const getIncidentById = async (id: number): Promise<Incident> => {
  debugLog(`Fetching incident with ID: ${id}`);
  const response = await api.get(`traffic/incidents/${id}`);
  debugLog("Received incident data:", response.data);
  return response.data;
};
