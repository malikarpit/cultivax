'use client';

import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import Map, {
  Marker,
  Source,
  Layer,
  NavigationControl,
  GeolocateControl,
  FullscreenControl,
  MapRef,
} from 'react-map-gl/maplibre';
import type { MapLayerMouseEvent } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Search, CheckCircle2, RotateCcw } from 'lucide-react';
import clsx from 'clsx';
import type { MapMarker, MapPolygon, MapViewProps } from './MapView';

// Dark terrain base style from Carto Voyager
const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

// Default center: India
const DEFAULT_CENTER: [number, number] = [22.5, 78.9]; // [Lat, Lng]
const DEFAULT_ZOOM = 5;

export default function MapViewInner({
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  markers = [],
  polygons = [],
  editable = false,
  onPolygonComplete,
  onChangeCenter,
  onMarkerDragEnd,
  className = 'h-[500px]',
}: MapViewProps) {
  const mapRef = useRef<MapRef>(null);

  // Drawing state (Array of [lat, lng])
  const [points, setPoints] = useState<[number, number][]>(() => {
    if (editable && polygons.length > 0) {
      const draft = polygons.find(p => p.id === 'draft') || polygons[0];
      if (draft && draft.positions) return [...draft.positions];
    }
    return [];
  });
  
  // Search Overlay
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);

  // Ensure map flies to new center when explicitly provided via props
  useEffect(() => {
    if (center && center[0] !== DEFAULT_CENTER[0]) {
      mapRef.current?.flyTo({ center: [center[1], center[0]], zoom: 13, duration: 1500 });
    }
  }, [center]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    setSearching(true);
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=1`);
      const data = await res.json();
      if (data && data.length > 0) {
        const newLat = Number(data[0].lat);
        const newLng = Number(data[0].lon);
        mapRef.current?.flyTo({
          center: [newLng, newLat],
          zoom: 15,
          duration: 2000
        });
        onChangeCenter?.([newLat, newLng]);
      }
    } catch (err) {
      console.error("Geocoding failed", err);
    } finally {
      setSearching(false);
    }
  };

  // Map Click Handler for Drawing Mode
  const onMapClick = useCallback((e: any) => {
    if (!editable) return;
    // e.lngLat contains native MapBox coordinates {lng, lat}
    const newPoint: [number, number] = [e.lngLat.lat, e.lngLat.lng];
    
    setPoints(prev => {
      const updated = [...prev, newPoint];
      // Auto-update parent if it's already a complete polygon being appended
      if (updated.length >= 3) {
        onPolygonComplete?.(updated);
      }
      return updated;
    });
  }, [editable, onPolygonComplete]);

  const onVertexDragEnd = useCallback((index: number, newLng: number, newLat: number) => {
    setPoints(prev => {
      const updated = [...prev];
      updated[index] = [newLat, newLng]; // Maplibre emits lng,lat. We store lat,lng
      onPolygonComplete?.(updated);
      return updated;
    });
  }, [onPolygonComplete]);

  // Vertex Deletion Logic
  const onVertexDelete = useCallback((index: number) => {
    setPoints(prev => {
      const updated = prev.filter((_, i) => i !== index);
      onPolygonComplete?.(updated);
      return updated;
    });
  }, [onPolygonComplete]);

  const clearDrawing = () => {
    setPoints([]);
    onPolygonComplete?.([]);
  };

  // Build GeoJSON for the Active Drawing Polygon
  const drawingGeoJSON = useMemo(() => {
    if (points.length < 3) return null;
    
    // Mapbox needs coordinates in [Lng, Lat] format!
    const coordinates = points.map(p => [p[1], p[0]]);
    // Close the polygon
    coordinates.push([points[0][1], points[0][0]]);

    return {
      type: 'FeatureCollection' as const,
      features: [
        {
          type: 'Feature' as const,
          properties: {},
          geometry: {
            type: 'Polygon' as const,
            coordinates: [coordinates]
          }
        }
      ]
    };
  }, [points]);

  return (
    <div className={clsx('w-full rounded-xl overflow-hidden relative border border-cultivax-border shadow-lg shadow-black/20', className)}>
      
      {/* ─── Advanced Glassmorphic HUD Overlays ─── */}
      <div className="absolute top-4 left-4 z-[2] flex flex-col gap-2">
        
        {/* Nominatim Village Search */}
        <form onSubmit={handleSearch} className="flex items-center bg-cultivax-surface/80 backdrop-blur-md border border-cultivax-border rounded-lg overflow-hidden shadow-glow-green/10 transition-all focus-within:border-cultivax-primary">
          <input
            type="text"
            placeholder="Search village or district..."
            className="bg-transparent text-cultivax-text-primary px-4 py-2 w-48 sm:w-64 focus:outline-none text-sm placeholder:text-cultivax-text-muted"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit" disabled={searching} className="p-2 text-cultivax-text-muted hover:text-cultivax-primary transition-colors pr-3">
            {searching ? <div className="w-4 h-4 rounded-full border-2 border-cultivax-primary border-t-transparent animate-spin" /> : <Search className="w-4 h-4" />}
          </button>
        </form>

        {/* Edit Controls */}
        {editable && points.length > 0 && (
          <div className="flex gap-2 animate-fade-in mt-1">
            <button
              onClick={(e) => { e.preventDefault(); clearDrawing(); }}
              className="flex items-center gap-1.5 bg-cultivax-elevated/90 backdrop-blur-md border border-cultivax-border px-3 py-1.5 rounded-lg text-xs font-medium text-cultivax-text-secondary hover:text-red-400 hover:border-red-400/50 transition-colors shadow-sm"
              title="Clear all points"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Clear Points
            </button>
            {points.length >= 3 && (
              <div className="flex items-center gap-1.5 bg-cultivax-primary/20 backdrop-blur-md border border-cultivax-primary/50 px-3 py-1.5 rounded-lg text-xs font-medium text-cultivax-primary shadow-sm animate-pulse-light">
                <CheckCircle2 className="w-3.5 h-3.5" /> Area Calculated
              </div>
            )}
          </div>
        )}
      </div>

      {editable && points.length === 0 && (
        <div className="absolute top-16 left-4 z-[2] bg-cultivax-surface/90 backdrop-blur-md border border-cultivax-border rounded-lg px-4 py-2.5 text-xs text-cultivax-text-primary shadow-lg max-w-xs animate-fade-in border-l-4 border-l-cultivax-primary">
          Click on the map to drop boundary points. Drag corner nodes to fine-tune your field.
        </div>
      )}

      {/* ─── WebGL Map Engine ─── */}
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: center[1],
          latitude: center[0],
          zoom: zoom
        }}
        mapStyle={MAP_STYLE}
        onClick={onMapClick}
        interactiveLayerIds={['drawing-fill', 'existing-fill']}
      >
        <GeolocateControl position="top-right" positionOptions={{ enableHighAccuracy: true }} trackUserLocation />
        <FullscreenControl position="top-right" />
        <NavigationControl position="top-right" visualizePitch />

        {/* Existing Props Polygons */}
        {polygons.filter(p => !(editable && p.id === 'draft')).map((poly) => {
          // Mapbox requires [lng, lat]
          let coords = poly.positions.map(p => [p[1], p[0]]);
          if (coords.length >= 3) coords.push(coords[0]); // auto-close
          
          return (
            <Source key={poly.id} type="geojson" data={{
              type: 'Feature',
              properties: {},
              geometry: { type: 'Polygon', coordinates: [coords] }
            }}>
              <Layer
                id={`existing-fill-${poly.id}`}
                type="fill"
                paint={{
                  'fill-color': poly.fillColor || '#10B981',
                  'fill-opacity': 0.15,
                }}
              />
              <Layer
                id={`existing-line-${poly.id}`}
                type="line"
                paint={{
                  'line-color': poly.color || '#059669',
                  'line-width': 2,
                }}
              />
            </Source>
          );
        })}

        {/* Existing Markers */}
        {markers.map((marker) => (
          <Marker
            key={marker.id}
            longitude={marker.lng}
            latitude={marker.lat}
            anchor="bottom"
            draggable={editable || marker.draggable === true}
            onDragEnd={(e) => {
              if (onMarkerDragEnd) {
                onMarkerDragEnd(marker.id, e.lngLat.lat, e.lngLat.lng);
              }
            }}
          >
            <div className="flex flex-col items-center group cursor-pointer">
              <div className="bg-cultivax-surface/90 backdrop-blur-sm border border-cultivax-border px-2 py-1 rounded text-xs font-semibold text-white shadow-sm mb-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                {marker.label}
              </div>
              <svg width="24" height="36" viewBox="0 0 24 36" className="drop-shadow-lg scale-90 group-hover:scale-100 transition-transform">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 9 12 24 12 24s12-15 12-24C24 5.37 18.63 0 12 0z" fill={marker.color || "#10B981"}/>
                <circle cx="12" cy="12" r="5" fill="white"/>
              </svg>
            </div>
          </Marker>
        ))}

        {/* Live Drawing Polygon Layer */}
        {drawingGeoJSON && (
          <Source id="drawing-source" type="geojson" data={drawingGeoJSON}>
            <Layer
              id="drawing-fill"
              type="fill"
              paint={{
                'fill-color': '#10B981',
                'fill-opacity': 0.25,
              }}
            />
            <Layer
              id="drawing-line"
              type="line"
              paint={{
                'line-color': '#34D399',
                'line-width': 2,
                'line-dasharray': [2, 2],
              }}
            />
          </Source>
        )}

        {/* Draggable Vertex Nodes for live editing */}
        {editable && points.map((point, index) => (
          <Marker
            key={`vertex-${index}`}
            longitude={point[1]}
            latitude={point[0]}
            draggable={editable}
            onDragEnd={(e: any) => onVertexDragEnd(index, e.lngLat.lng, e.lngLat.lat)}
            anchor="center"
          >
            <div 
              className="w-4 h-4 bg-white border-2 border-cultivax-primary rounded-full shadow-md cursor-move hover:scale-125 transition-transform"
              onContextMenu={(e) => {
                e.preventDefault();
                onVertexDelete(index);
              }}
              onDoubleClick={(e) => {
                e.stopPropagation();
                onVertexDelete(index);
              }}
              title="Drag to move, Double-click (or Right-click) to delete vertex"
            />
          </Marker>
        ))}

      </Map>
    </div>
  );
}
