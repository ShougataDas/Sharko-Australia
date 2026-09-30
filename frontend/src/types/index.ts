export type ZoneType = "heat" | "infected" | "toxic";

export type Zone = {
  id: string;
  type: ZoneType;
  lat: number; // degrees
  lon: number; // degrees
  radius: number; // visual radius in world units (on unit sphere scale)
};

export const ZONE_COLORS: Record<ZoneType, string> = {
  heat: "#ef4444", // red-500
  infected: "#f59e0b", // amber-500
  toxic: "#22c55e", // green-500
};

export const defaultZones: Zone[] = [
  { id: "z1", type: "heat", lat: 34.05, lon: -118.24, radius: 0.06 }, // near LA
  { id: "z2", type: "infected", lat: 40.71, lon: -74.0, radius: 0.05 }, // near NYC
  { id: "z3", type: "toxic", lat: 35.68, lon: 139.69, radius: 0.055 }, // near Tokyo
  { id: "z4", type: "heat", lat: 51.5074, lon: -0.1278, radius: 0.045 }, // London
  { id: "z5", type: "infected", lat: -33.8688, lon: 151.2093, radius: 0.06 }, // Sydney
];
