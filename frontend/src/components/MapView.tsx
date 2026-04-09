'use client';

/**
 * MapView — Interactive MapLibre GL map component
 *
 * Features:
 * - Fluid WebGL engine (MapLibre)
 * - Draggable boundary nodes
 * - Auto-geolocation & Nominatim Geocoding
 * - Real-time polygon rendering
 * - Area Calculation (Turf.js)
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import dynamic from 'next/dynamic';
import clsx from 'clsx';

// Types
export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  label: string;
  popup?: string;
  color?: string;
  draggable?: boolean;
}

export interface MapPolygon {
  id: string;
  positions: [number, number][]; // [lat, lng] array
  label?: string;
  color?: string;
  fillColor?: string;
}

export interface MapViewProps {
  center?: [number, number]; // [lat, lng]
  zoom?: number;
  markers?: MapMarker[];
  polygons?: MapPolygon[];
  editable?: boolean;
  onPolygonComplete?: (points: [number, number][]) => void;
  onChangeCenter?: (center: [number, number]) => void;
  onMarkerDragEnd?: (markerId: string, lat: number, lng: number) => void;
  className?: string;
}

// Dynamic import wrapper to prevent SSR issues with WebGL Contexts
const MapViewInner = dynamic(() => import('./MapViewInner'), {
  ssr: false,
  loading: () => (
    <div className="w-full bg-cultivax-elevated rounded-xl flex items-center justify-center animate-pulse h-[500px]">
      <div className="text-cultivax-text-muted text-sm flex flex-col items-center gap-3">
        <svg className="w-8 h-8 animate-spin text-cultivax-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>
        Loading WebGL Engine...
      </div>
    </div>
  ),
});

export default function MapView(props: MapViewProps) {
  return <MapViewInner {...props} />;
}
