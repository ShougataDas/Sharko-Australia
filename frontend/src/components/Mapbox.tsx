/* eslint-disable @typescript-eslint/no-explicit-any */
import mapboxgl from "mapbox-gl";
import { useEffect, useRef, useState, useMemo } from "react";
import "mapbox-gl/dist/mapbox-gl.css";
import pinIcon from "../assets/image.png";
import {
  processGeoJsonFeatures,
  findFeatureCenter,
  calculateOptimalCameraDistance,
  GeoJsonData,
} from "../utils/geoJsonLoader";
import { ChevronRight, MessageCircle } from "lucide-react";
import { Link } from "react-router-dom";
import AIAssistant from "./AIAssistant";

// Set the access token
const accessToken = import.meta.env.VITE_MAPBOX_TOKEN as string;

// Sharks tracked by this dataset cluster around Australian waters, so once a
// prediction lands we fly the globe there.
const AUSTRALIA_CENTER: [number, number] = [133.7751, -25.2744];
const AUSTRALIA_ZOOM = 3.5;

// Wide, whole-earth starting view so the Australia fly-in is visible after the
// first prediction completes, instead of the globe just appearing there.
const GLOBE_START_CENTER: [number, number] = [30, 10];
const GLOBE_START_ZOOM = 0.8;

// Local (not UTC) today, formatted for the date input and the predict API.
const getTodayDateString = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export default function Mapbox() {
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const [presenceGeoJsonData, setPresenceGeoJsonData] =
    useState<GeoJsonData | null>(null);
  const [habitatGeoJsonData, setHabitatGeoJsonData] =
    useState<GeoJsonData | null>(null);
  const [currentlySelected, setCurrentlySelected] = useState<string | null>(
    "presence"
  );
  const [selectedDate, setSelectedDate] = useState<string>(getTodayDateString);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSharkPicker, setShowSharkPicker] = useState<boolean>(false);
  const [selectedSharkName, setSelectedSharkName] = useState<string>("");
  const [sharksDict, setSharksDict] = useState<any[] | null>(null);
  const [selectedSharkDetails, setSelectedSharkDetails] = useState<any>(null);
  const [isAIAssistantOpen, setIsAIAssistantOpen] = useState<boolean>(false);
  const [isMapStyleReady, setIsMapStyleReady] = useState(false);

  // Load GeoJSON / clustered data
  const loadPresenceData = async (date: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `https://midul914-sharko-api.hf.space/predict/presence?date=${date}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      const data = await response.json();

      setPresenceGeoJsonData(data.presence_geojson_data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load GeoJSON data"
      );
      console.error("Error loading GeoJSON:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadHabitatData = async (date: string, sharkName: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `https://midul914-sharko-api.hf.space/predict/habitat?date=${date}&shark_name=${sharkName}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      const data = await response.json();
      setHabitatGeoJsonData(data.habitat_geojson_data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load GeoJSON data"
      );
      console.error("Error loading GeoJSON:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentlySelected === "presence") {
      loadPresenceData(selectedDate);
    } else {
      if (selectedSharkName === "") return;
      loadHabitatData(selectedDate, selectedSharkName);
    }
  }, [selectedDate, currentlySelected, selectedSharkName]);

  // Load sharks dictionary once
  useEffect(() => {
    const loadSharks = async () => {
      try {
        const res = await fetch("/sharks.json");
        if (res.ok) {
          const dict = await res.json();
          setSharksDict(dict);
        }
      } catch (e) {
        console.warn("Failed to load sharks.json", e);
      }
    };
    loadSharks();
  }, []);

  // Process GeoJSON features into Mapbox-compatible data
  const processedFeatures = useMemo(() => {
    if (!currentlySelected) return [];
    if (!presenceGeoJsonData && !habitatGeoJsonData) return [];
    if (currentlySelected === "presence" && presenceGeoJsonData) {
      return processGeoJsonFeatures(presenceGeoJsonData, 1000);
    }
    if (currentlySelected === "habitat" && habitatGeoJsonData) {
      return processGeoJsonFeatures(habitatGeoJsonData, 1000);
    }
    return [];
  }, [presenceGeoJsonData, habitatGeoJsonData, currentlySelected]);

  // Initialize map only once
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    mapboxgl.accessToken = accessToken;

    try {
      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/standard-satellite",
        center: GLOBE_START_CENTER,
        zoom: GLOBE_START_ZOOM,
        antialias: false,
        preserveDrawingBuffer: true,
        maxTileCacheSize: 50,
        renderWorldCopies: false,
        projection: "globe",
      });

      mapRef.current.on("style.load", () => {
        mapRef.current?.setFog({});
      });

      // Only touch sources/layers once the style has actually finished loading.
      mapRef.current.on("load", () => {
        setIsMapStyleReady(true);
      });

      mapRef.current.on("error", (e) => {
        console.error("Map error:", e);
      });
    } catch (error) {
      console.error("Failed to initialize map:", error);
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []); // Only run once

  // Update map data when data changes
  useEffect(() => {
    if (!mapRef.current || loading || !isMapStyleReady) return;

    const currentData =
      currentlySelected === "presence"
        ? presenceGeoJsonData
        : habitatGeoJsonData;
    console.log(habitatGeoJsonData, selectedSharkName);
    if (!currentData) return;

    // Smoothly recenter the globe on Australia once a prediction is ready.
    mapRef.current.flyTo({
      center: AUSTRALIA_CENTER,
      zoom: AUSTRALIA_ZOOM,
      duration: 4000,
      essential: true,
    });

    // Remove existing layers and sources
    if (mapRef.current.getLayer("polygon-fill")) {
      mapRef.current.removeLayer("polygon-fill");
    }
    if (mapRef.current.getLayer("polygon-outline")) {
      mapRef.current.removeLayer("polygon-outline");
    }
    if (mapRef.current.getSource("polygons")) {
      mapRef.current.removeSource("polygons");
    }

    // Remove existing markers
    document.querySelectorAll(".mapboxgl-marker").forEach((marker) => {
      marker.remove();
    });
    console.log(currentData, selectedSharkName);
    // Add new data
    mapRef.current.addSource("polygons", {
      type: "geojson",
      data: currentData as GeoJSON.GeoJSON,
    });

    // Add polygon layer
    mapRef.current.addLayer({
      id: "polygon-fill",
      type: "fill",
      source: "polygons",
      paint: {
        "fill-color": currentlySelected === "presence" ? "#ff0000" : "#00ff00",
        "fill-opacity": 0.5,
      },
    });

    // Add polygon outline
    mapRef.current.addLayer({
      id: "polygon-outline",
      type: "line",
      source: "polygons",
      paint: {
        "line-color": currentlySelected === "presence" ? "#ff0000" : "#00ff00",
        "line-width": 2,
      },
    });

    // Add markers for each feature center
    processedFeatures.forEach((feature) => {
      const centerPosition = findFeatureCenter(feature.positions);

      const marker = new mapboxgl.Marker({
        element: createMarkerElement(feature.properties),
      })
        .setLngLat([centerPosition[0], centerPosition[1]])
        .addTo(mapRef.current!);

      // Add click handler
      marker.getElement().addEventListener("click", () => {
        const cameraDistance = calculateOptimalCameraDistance(
          feature.positions as [number, number][],
          1,
          5000
        );
        mapRef.current!.flyTo({
          center: [centerPosition[0], centerPosition[1]],
          zoom: Math.log2(156543.03392 / (cameraDistance * 900)),
          duration: 2000,
        });
      });
    });
  }, [
    presenceGeoJsonData,
    habitatGeoJsonData,
    processedFeatures,
    loading,
    isMapStyleReady,
  ]);

  // Create custom marker element
  const createMarkerElement = (properties: any) => {
    const el = document.createElement("div");
    el.className = "marker";
    el.style.backgroundImage = `url(${pinIcon})`;
    el.style.width = "32px";
    el.style.height = "32px";
    el.style.backgroundSize = "contain";
    el.style.cursor = "pointer";
    el.title = `${properties.cluster_id}_center`;
    return el;
  };

  if (error) {
    return (
      <div className="relative w-full h-screen">
        <div
          id="map-container"
          className="w-full h-screen"
          ref={mapContainerRef}
        ></div>
        <div className="absolute top-0 left-0 w-full h-full bg-black bg-opacity-50 backdrop-blur-sm flex justify-center items-center z-[2000]">
          <div className="bg-black bg-opacity-70 backdrop-blur-md border border-gray-300 border-opacity-30 p-8 rounded-2xl shadow-2xl text-center max-w-md">
            <div className="text-lg text-red-400 font-bold mb-2">
              ⚠️ Error Loading Data
            </div>
            <div className="text-sm text-gray-300 mb-5">{error}</div>
            <button
              onClick={() => loadPresenceData(selectedDate)}
              className="px-5 py-2 bg-blue-600 bg-opacity-80 text-white border border-blue-500 border-opacity-50 rounded-xl cursor-pointer text-sm hover:bg-opacity-100 transition-all duration-300"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-screen">
      <div
        id="map-container"
        className="w-full h-screen"
        ref={mapContainerRef}
      ></div>

      {!loading && (
        <>
          <div className="absolute top-5 left-5 z-[100] flex flex-col gap-3">
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 p-4 rounded-2xl shadow-2xl">
              <label className="mr-4 mb-2 text-sm font-bold text-white drop-shadow-lg">
                Select Date:
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="p-3 bg-white/20 backdrop-blur-md border border-white/30 rounded-xl text-sm min-w-[150px] text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-white/50 focus:bg-white/30 transition-all duration-300"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setCurrentlySelected("presence")}
                className={`px-6 py-3 text-white border border-white/20 rounded-xl cursor-pointer text-sm font-bold transition-all duration-300 backdrop-blur-lg shadow-lg ${
                  currentlySelected === "presence"
                    ? "bg-red-500/30"
                    : "bg-white/10 hover:bg-white/20"
                }`}
              >
                Shark Presence
              </button>
              <button
                onClick={() => {
                  setCurrentlySelected("habitat");
                  setShowSharkPicker(true);
                }}
                className={`px-6 py-3 text-white border border-white/20 rounded-xl cursor-pointer text-sm font-bold transition-all duration-300 backdrop-blur-lg shadow-lg ${
                  currentlySelected === "habitat"
                    ? "bg-green-500/30"
                    : "bg-white/10 hover:bg-white/20"
                }`}
              >
                Shark Habitat
              </button>
            </div>
            <div className="fixed left-8 top-1/2 -translate-y-1/2 z-50 flex flex-col gap-3">
              {/* Hidden for now (keep markup/code in place for later re-enable) */}
              <Link to="/tag" className="hidden">
                <button className="bg-blue-500/30 hover:bg-blue-500/60 text-white shadow-2xl backdrop-blur-sm border border-white/20 rounded-2xl px-6 py-6 group hover:cursor-pointer">
                  <ChevronRight className="w-6 h-6 group-hover:translate-x-1 transition-transform inline" />
                  <span className="ml-2 font-semibold">
                    Proposed Tag Design
                  </span>
                </button>
              </Link>

              {/* Hidden for now (keep markup/code in place for later re-enable) */}
              <button
                onClick={() => setIsAIAssistantOpen(true)}
                className="hidden bg-green-500/30 hover:bg-green-500/60 text-white shadow-2xl backdrop-blur-sm border border-white/20 rounded-2xl px-6 py-6 group hover:cursor-pointer"
              >
                <MessageCircle className="w-6 h-6 group-hover:scale-110 transition-transform inline" />
                <span className="ml-2 font-semibold">AI Assistant</span>
              </button>

              <button
                onClick={() => window.location.reload()}
                className="bg-emerald-500/30 hover:bg-emerald-500/60 text-white shadow-2xl backdrop-blur-sm border border-white/20 rounded-2xl px-6 py-6 group hover:cursor-pointer"
              >
                <svg
                  className="w-6 h-6 group-hover:rotate-180 transition-transform inline"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span className="ml-2 font-semibold">Restart Story</span>
              </button>
            </div>
          </div>

          <div className="absolute top-48 left-5 z-[100] bg-white/10 backdrop-blur-lg border border-white/20 text-white px-4 py-2 rounded-xl text-xs shadow-lg">
            Currently showing:{" "}
            {currentlySelected === "presence"
              ? "Shark Presence"
              : "Shark Habitat"}{" "}
            |{" "}
            {new Date(selectedDate).toLocaleDateString("en-US", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </div>
        </>
      )}

      {showSharkPicker && sharksDict && (
        <div className="absolute inset-0 z-[2500] flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl p-6 w-[90%] max-w-xl text-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">Select Shark Species</h3>
              <button
                onClick={() => setShowSharkPicker(false)}
                className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20"
              >
                Close
              </button>
            </div>
            <div className="max-h-[50vh] overflow-y-auto pr-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {sharksDict.map((shark) => (
                <button
                  key={shark.scientificName}
                  onClick={() => {
                    setSelectedSharkName(shark.common_name);
                    setSelectedSharkDetails(shark);
                    setShowSharkPicker(false);
                    loadHabitatData(selectedDate, shark.common_name);
                  }}
                  className="text-left w-full px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20"
                >
                  <div className="text-sm font-semibold truncate">
                    {shark.common_name || shark.scientificName}
                  </div>
                  <div className="text-xs text-white/80 truncate">
                    {shark.scientificName}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {currentlySelected === "habitat" && selectedSharkDetails && (
        <div className="absolute top-5 right-5 z-[1200] text-white">
          <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl p-5 w-[400px] max-h-[90vh] overflow-y-auto">
            <div className="mb-4">
              <img
                src={selectedSharkDetails.image_url}
                alt={selectedSharkDetails.common_name}
                className="w-full aspect-video object-contain rounded-xl border border-white/20 mb-4"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                }}
              />
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-bold leading-tight">
                  {selectedSharkDetails.common_name}
                </h3>
                <span className="text-xs bg-white/10 border border-white/20 px-2 py-0.5 rounded-lg flex-shrink-0">
                  {selectedSharkDetails.iucn_status}
                </span>
              </div>
              <div className="font-mono text-[10px] opacity-80 mb-2">
                {selectedSharkDetails.scientificName}
              </div>
              <div className="text-xs text-white/80 leading-relaxed">
                {selectedSharkDetails.description}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs mb-4">
              <div className="bg-white/10 rounded-lg p-2 border border-white/10">
                <div className="opacity-80">Temp Range</div>
                <div className="font-semibold">
                  {selectedSharkDetails.min_temp_c}–
                  {selectedSharkDetails.max_temp_c}°C
                </div>
              </div>
              <div className="bg-white/10 rounded-lg p-2 border border-white/10">
                <div className="opacity-80">Max Length</div>
                <div className="font-semibold">
                  {selectedSharkDetails.max_length_m} m
                </div>
              </div>
              <div className="bg-white/10 rounded-lg p-2 border border-white/10">
                <div className="opacity-80">Diet</div>
                <div className="font-semibold truncate">
                  {selectedSharkDetails.diet}
                </div>
              </div>
              <div className="bg-white/10 rounded-lg p-2 border border-white/10">
                <div className="opacity-80">Habitat</div>
                <div className="font-semibold truncate">
                  {selectedSharkDetails.habitat_zone}
                </div>
              </div>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-white/10 rounded-lg p-3 border border-white/10">
                <div className="opacity-80 mb-1">Reproduction</div>
                <div className="font-semibold">
                  {selectedSharkDetails.reproduction}
                </div>
              </div>

              <div className="bg-white/10 rounded-lg p-3 border border-white/10">
                <div className="opacity-80 mb-1">Lifespan</div>
                <div className="font-semibold">
                  {selectedSharkDetails.lifespan_years} years
                </div>
              </div>

              <div className="bg-white/10 rounded-lg p-3 border border-white/10">
                <div className="opacity-80 mb-1">Distribution</div>
                <div className="font-semibold">
                  {selectedSharkDetails.distribution}
                </div>
              </div>

              <div className="bg-white/10 rounded-lg p-3 border border-white/10">
                <div className="opacity-80 mb-1">Primary Threats</div>
                <div className="font-semibold">
                  {selectedSharkDetails.primary_threats}
                </div>
              </div>

              <div className="bg-white/10 rounded-lg p-3 border border-white/10">
                <div className="opacity-80 mb-1">Distinctive Feature</div>
                <div className="font-semibold leading-relaxed">
                  {selectedSharkDetails.distinctive_feature}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="absolute top-0 left-0 w-full h-full bg-black/30 backdrop-blur-sm flex justify-center items-center z-[2000]">
          <div className="bg-white/10 backdrop-blur-xl border border-white/20 p-8 rounded-2xl shadow-2xl text-center">
            <div className="w-12 h-12 border-4 border-white/20 border-t-blue-400 rounded-full animate-spin mx-auto mb-6"></div>
            <div className="text-lg text-white font-bold drop-shadow-lg">
              Predicting...
            </div>
            <div className="text-sm text-white/80 mt-2 drop-shadow-md">
              Date:{" "}
              {new Date(selectedDate).toLocaleDateString("en-US", {
                day: "numeric",
                month: "long",
                year: "numeric",
              })}
            </div>
            <div className="text-sm text-white/80 mt-2 drop-shadow-md">
              It may take a minute to predict.
            </div>
          </div>
        </div>
      )}

      <AIAssistant
        isOpen={isAIAssistantOpen}
        onClose={() => setIsAIAssistantOpen(false)}
      />
    </div>
  );
}
