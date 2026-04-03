'use client';

/**
 * MapViewInner — Actual Leaflet map implementation
 * Loaded via dynamic import from MapView to prevent SSR issues.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polygon,
  useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';
import clsx from 'clsx';
import type { MapMarker, MapPolygon } from './MapView';

// Fix default marker icon issue with webpack
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = defaultIcon;

// Custom green marker
const greenIcon = L.icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="36" viewBox="0 0 24 36">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 9 12 24 12 24s12-15 12-24C24 5.37 18.63 0 12 0z" fill="#10B981"/>
      <circle cx="12" cy="12" r="5" fill="white"/>
    </svg>
  `),
  iconSize: [24, 36],
  iconAnchor: [12, 36],
  popupAnchor: [0, -36],
});

// Dark tile layer
const DARK_TILES = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';

// Default center: India
const DEFAULT_CENTER: [number, number] = [22.5, 78.9];
const DEFAULT_ZOOM = 5;

interface MapViewInnerProps {
  center?: [number, number];
  zoom?: number;
  markers?: MapMarker[];
  polygons?: MapPolygon[];
  editable?: boolean;
  onPolygonComplete?: (points: [number, number][]) => void;
  height?: string;
  className?: string;
}

// Drawing component for polygon creation
function DrawingCanvas({
  onPolygonComplete,
}: {
  onPolygonComplete?: (points: [number, number][]) => void;
}) {
  const [points, setPoints] = useState<[number, number][]>([]);
  const [isDrawing, setIsDrawing] = useState(true);

  useMapEvents({
    click(e) {
      if (!isDrawing) return;
      const newPoint: [number, number] = [e.latlng.lat, e.latlng.lng];
      setPoints((prev) => [...prev, newPoint]);
    },
    dblclick(e) {
      if (!isDrawing || points.length < 3) return;
      e.originalEvent.preventDefault();
      setIsDrawing(false);
      onPolygonComplete?.(points);
    },
  });

  if (points.length < 2) return null;

  return (
    <>
      {/* Show current polygon being drawn */}
      <Polygon
        positions={points}
        pathOptions={{
          color: '#10B981',
          fillColor: '#10B981',
          fillOpacity: 0.15,
          weight: 2,
          dashArray: isDrawing ? '5, 10' : undefined,
        }}
      />
      {/* Show vertex markers */}
      {points.map((point, i) => (
        <Marker key={i} position={point} icon={greenIcon}>
          <Popup>
            <span className="text-xs">
              Point {i + 1}: {point[0].toFixed(5)}, {point[1].toFixed(5)}
            </span>
          </Popup>
        </Marker>
      ))}
    </>
  );
}

export default function MapViewInner({
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  markers = [],
  polygons = [],
  editable = false,
  onPolygonComplete,
  height = '400px',
  className,
}: MapViewInnerProps) {
  return (
    <div className={clsx('w-full rounded-xl overflow-hidden relative', className)} style={{ height }}>
      {/* Drawing instructions */}
      {editable && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1000] bg-cultivax-surface/95 border border-cultivax-border rounded-lg px-4 py-2 text-xs text-cultivax-text-secondary backdrop-blur-sm">
          Click to add points, double-click to finish polygon
        </div>
      )}

      <MapContainer
        center={center}
        zoom={zoom}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
        attributionControl={true}
      >
        <TileLayer url={DARK_TILES} attribution={TILE_ATTRIBUTION} />

        {/* Existing polygons */}
        {polygons.map((poly) => (
          <Polygon
            key={poly.id}
            positions={poly.positions}
            pathOptions={{
              color: poly.color || '#10B981',
              fillColor: poly.fillColor || '#10B981',
              fillOpacity: 0.2,
              weight: 2,
            }}
          >
            {poly.label && (
              <Popup>
                <div className="text-sm font-medium">{poly.label}</div>
              </Popup>
            )}
          </Polygon>
        ))}

        {/* Markers */}
        {markers.map((marker) => (
          <Marker
            key={marker.id}
            position={[marker.lat, marker.lng]}
            icon={greenIcon}
          >
            {(marker.label || marker.popup) && (
              <Popup>
                <div>
                  <div className="text-sm font-medium">{marker.label}</div>
                  {marker.popup && (
                    <div className="text-xs text-gray-500 mt-1">{marker.popup}</div>
                  )}
                </div>
              </Popup>
            )}
          </Marker>
        ))}

        {/* Drawing canvas */}
        {editable && <DrawingCanvas onPolygonComplete={onPolygonComplete} />}
      </MapContainer>
    </div>
  );
}
