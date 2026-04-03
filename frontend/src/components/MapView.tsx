'use client';

/**
 * MapView — Interactive Leaflet map component
 *
 * Features:
 * - Dark tile layer (CartoDB Dark Matter)
 * - View mode: Shows parcel boundaries as green polygons
 * - Edit mode: Polygon draw tool for boundary mapping
 * - Marker popups with crop/parcel info
 * - Responsive: Full-width on mobile
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
}

export interface MapPolygon {
  id: string;
  positions: [number, number][];
  label?: string;
  color?: string;
  fillColor?: string;
}

interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  markers?: MapMarker[];
  polygons?: MapPolygon[];
  editable?: boolean;
  onPolygonComplete?: (points: [number, number][]) => void;
  height?: string;
  className?: string;
}

// Dynamic import wrapper to prevent SSR issues with Leaflet
const MapViewInner = dynamic(() => import('./MapViewInner'), {
  ssr: false,
  loading: () => (
    <div className="w-full bg-cultivax-elevated rounded-xl flex items-center justify-center animate-pulse"
         style={{ height: '400px' }}>
      <div className="text-cultivax-text-muted text-sm">Loading map...</div>
    </div>
  ),
});

export default function MapView(props: MapViewProps) {
  return <MapViewInner {...props} />;
}
