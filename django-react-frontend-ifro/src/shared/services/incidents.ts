import api from "./axios";
import { Incident } from "../types/global.types";

export const getIncidents = async (): Promise<Incident[]> => {
  console.log("Fetching all incidents...");
  const response = await api.get("traffic/incidents");
  console.log("Received incidents data:", response.data);
  return response.data;
};

export const getIncidentById = async (id: number): Promise<Incident> => {
  console.log(`Fetching incident with ID: ${id}`);
  const response = await api.get(`traffic/incidents/${id}`);
  console.log("Received incident data:", response.data);
  return response.data;
};
