import { TrafficData } from "../types/global.types";

export const generateTrafficData = (segmentId: number): TrafficData[] => {
  const data: TrafficData[] = [];
  const baseSpeed = 40 - segmentId * 3;
  const baseVolume = 1200 + segmentId * 150;

  for (let i = 0; i < 24; i++) {
    const hour = `${i.toString().padStart(2, "0")}:00`;
    let speed, volume;

    if ((i >= 7 && i <= 9) || (i >= 17 && i <= 19)) {
      speed = baseSpeed * (0.4 + Math.random() * 0.2);
      volume = baseVolume * (1.6 + Math.random() * 0.4);
    } else {
      speed = baseSpeed * (0.9 + Math.random() * 0.1);
      volume = baseVolume * (0.7 + Math.random() * 0.2);
    }

    data.push({
      hour,
      speed: parseFloat(speed.toFixed(1)),
      volume: Math.round(volume),
    });
  }
  return data;
};
