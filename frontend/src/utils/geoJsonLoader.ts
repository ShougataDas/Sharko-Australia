import * as Cesium from "cesium";

export interface GeoJsonFeature {
  type: "Feature";
  properties: Record<string, unknown>;
  geometry: {
    type:
      | "Point"
      | "Polygon"
      | "MultiPolygon"
      | "LineString"
      | "MultiLineString";
    coordinates: number[] | number[][] | number[][][] | number[][][][];
  };
}

export interface GeoJsonData {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
}

/**
 * Loads and parses a GeoJSON file
 * @param filePath - Path to the GeoJSON file
 * @returns Promise<GeoJsonData>
 */
export async function loadGeoJson(filePath: string): Promise<GeoJsonData> {
  try {
    console.log(`Loading GeoJSON from: ${filePath}`);
    const response = await fetch(filePath);
    if (!response.ok) {
      throw new Error(
        `Failed to load GeoJSON file: ${response.statusText} (${response.status})`
      );
    }

    // Check if the response is actually JSON or GeoJSON
    const contentType = response.headers.get("content-type");
    if (
      !contentType ||
      (!contentType.includes("application/json") &&
        !contentType.includes("application/geo+json"))
    ) {
      const text = await response.text();
      console.error("Response is not JSON:", text.substring(0, 200));
      throw new Error(`Expected JSON but got: ${contentType}`);
    }

    const data: GeoJsonData = await response.json();
    console.log(
      `Successfully loaded GeoJSON with ${data.features.length} features`
    );
    return data;
  } catch (error) {
    console.error("Error loading GeoJSON:", error);
    throw error;
  }
}

/**
 * Converts GeoJSON coordinates to Cesium Cartesian3 positions
 * @param coordinates - GeoJSON coordinates array
 * @param geometryType - Type of geometry (Point, Polygon, etc.)
 * @returns Cartesian3[] array of positions
 */
export function convertGeoJsonToCesiumPositions(
  coordinates: number[] | number[][] | number[][][] | number[][][][],
  geometryType: string
): [number, number][] {
  switch (geometryType) {
    case "Point": {
      const pointCoords = coordinates as number[];
      return [[pointCoords[0], pointCoords[1]]];
    }

    case "Polygon": {
      const polygonCoords = coordinates as number[][][];
      // GeoJSON polygons have an outer ring and optional inner rings
      // We'll use the outer ring (first array)
      const outerRing = polygonCoords[0];
      return outerRing.map((coord) => [coord[0], coord[1]]);
    }

    case "MultiPolygon": {
      const multiPolygonCoords = coordinates as number[][][][];
      // For MultiPolygon, we'll take the first polygon's outer ring
      const firstPolygon = multiPolygonCoords[0];
      const firstRing = firstPolygon[0];
      return firstRing.map((coord) => [coord[0], coord[1]]);
    }

    case "LineString": {
      const lineCoords = coordinates as number[][];
      return lineCoords.map((coord) => [coord[0], coord[1]]);
    }

    case "MultiLineString": {
      const multiLineCoords = coordinates as number[][][];
      // For MultiLineString, we'll take the first line
      const firstLine = multiLineCoords[0];
      return firstLine.map((coord) => [coord[0], coord[1]]);
    }

    default:
      console.warn(`Unsupported geometry type: ${geometryType}`);
      return [];
  }
}

/**
 * Processes GeoJSON features and returns Cesium entities data
 * @param geoJsonData - Parsed GeoJSON data
 * @param maxFeatures - Maximum number of features to process (optional, for performance)
 * @returns Array of objects containing positions and properties for each feature
 */
export function processGeoJsonFeatures(
  geoJsonData: GeoJsonData,
  maxFeatures?: number
) {
  let features = geoJsonData.features;

  // Limit features for performance if specified
  if (maxFeatures && features.length > maxFeatures) {
    console.log(
      `Limiting features from ${features.length} to ${maxFeatures} for performance`
    );
    features = features.slice(0, maxFeatures);
  }

  return features.map((feature) => {
    const positions = convertGeoJsonToCesiumPositions(
      feature.geometry.coordinates,
      feature.geometry.type
    );

    return {
      positions,
      properties: feature.properties,
      geometryType: feature.geometry.type,
      name:
        feature.properties.name ||
        `Feature ${feature.properties.id || "Unknown"}`,
    };
  });
}

/**
 * Finds the center of a polygon or point
 * @param positions - Array of Cartesian3 positions
 * @returns Cartesian3 center position
 */
export function findFeatureCenter(
  positions: [number, number][]
): [number, number] {
  if (positions.length === 0) {
    throw new Error("Cannot find center of empty positions array");
  }

  if (positions.length === 1) {
    return [positions[0][0], positions[0][1]];
  }

  let x = 0;
  let y = 0;

  for (const position of positions) {
    x += position[0];
    y += position[1];
  }

  return [x / positions.length, y / positions.length];
}

/**
 * Calculates the bounding box of a set of positions
 * @param positions - Array of Cartesian3 positions
 * @returns Object containing min/max coordinates and dimensions
 */
export function calculateBoundingBox(positions: [number, number][]) {
  if (positions.length === 0) {
    throw new Error("Cannot calculate bounding box of empty positions array");
  }

  let minX = positions[0][0];
  let maxX = positions[0][0];
  let minY = positions[0][1];
  let maxY = positions[0][1];

  for (const position of positions) {
    minX = Math.min(minX, position[0]);
    maxX = Math.max(maxX, position[0]);
    minY = Math.min(minY, position[1]);
    maxY = Math.max(maxY, position[1]);
  }

  const width = maxX - minX;
  const height = maxY - minY;
  const diagonal = Math.sqrt(width * width + height * height);

  return {
    min: new Cesium.Cartesian3(minX, minY),
    max: new Cesium.Cartesian3(maxX, maxY),
    center: new Cesium.Cartesian3((minX + maxX) / 2, (minY + maxY) / 2),
    width,
    height,
    diagonal,
  };
}

/**
 * Calculates optimal camera distance based on polygon area/bounding box
 * @param positions - Array of Cartesian3 positions
 * @param minDistance - Minimum camera distance (default: 1000m)
 * @param maxDistance - Maximum camera distance (default: 1000000m)
 * @returns Optimal camera distance in meters
 */
export function calculateOptimalCameraDistance(
  positions: [number, number][],
  minDistance: number = 1,
  maxDistance: number = 10000
): number {
  if (positions.length === 0) {
    return minDistance;
  }

  if (positions.length === 1) {
    return minDistance;
  }

  const boundingBox = calculateBoundingBox(positions);
  console.log("boundingBox", boundingBox);
  // Calculate the maximum dimension (width, height, or depth)
  const maxDimension = Math.max(boundingBox.width, boundingBox.height);

  // Use the maximum dimension as base for distance calculation
  // Add padding (multiply by 2) to ensure the entire polygon is visible
  // Cesium positions are in meters, so we can use them directly
  let optimalDistance = maxDimension * 2;

  // Apply bounds
  optimalDistance = Math.max(optimalDistance, minDistance);
  optimalDistance = Math.min(optimalDistance, maxDistance);

  // For very small polygons, ensure minimum visibility
  if (optimalDistance < minDistance) {
    optimalDistance = minDistance;
  }

  // For very large polygons, cap at maximum distance
  if (optimalDistance > maxDistance) {
    optimalDistance = maxDistance;
  }

  return optimalDistance;
}
