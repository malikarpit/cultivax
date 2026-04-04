/**
 * Shared frontend types for parcel-linked crop flows.
 */

export type LandAreaUnit = 'acres' | 'hectares' | 'bigha';

export interface GPSCoordinates {
  lat: number;
  lng: number;
  boundary_polygon?: [number, number][];
  computed_area_acres?: number;
  centroid?: { lat: number; lng: number };
}

export interface SoilInfo {
  primary?: string;
  ph?: number;
  organic_matter?: string;
}

export interface LandParcel {
  id: string;
  farmer_id: string;
  is_deleted: boolean;
  parcel_name: string;
  region: string;
  sub_region?: string | null;
  land_area?: number | null;
  land_area_unit: LandAreaUnit;
  soil_type?: SoilInfo | null;
  gps_coordinates: GPSCoordinates;
  irrigation_source?: string | null;
  area_from_polygon?: number | null;
  centroid?: { lat: number; lng: number } | null;
  created_at: string;
  updated_at: string;
}

export interface LandParcelCreate {
  parcel_name: string;
  region: string;
  sub_region?: string;
  land_area?: number;
  land_area_unit?: LandAreaUnit;
  soil_type?: SoilInfo;
  gps_coordinates: GPSCoordinates;
  irrigation_source?: string;
}

export interface LandParcelUpdate {
  parcel_name?: string;
  region?: string;
  sub_region?: string;
  land_area?: number;
  land_area_unit?: LandAreaUnit;
  soil_type?: SoilInfo;
  gps_coordinates?: GPSCoordinates;
  irrigation_source?: string;
}

export interface ParcelSelectorProps {
  value?: string | null;
  excludeIds?: string[];
  onSelect: (parcel: LandParcel | null) => void;
  onCreateNew?: () => void;
  disabled?: boolean;
  className?: string;
}

export interface CropRecommendation {
  id: string;
  crop_instance_id: string;
  recommendation_type: string;
  priority_rank: number;
  message_key: string;
  message_parameters?: Record<string, unknown> | null;
  basis?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
  status: string;
  created_at: string;
}

export type SimulationActionType =
  | 'irrigation'
  | 'fertilizer'
  | 'pesticide'
  | 'fungicide'
  | 'herbicide'
  | 'pruning'
  | 'thinning'
  | 'transplanting'
  | 'harvesting'
  | 'monitoring'
  | 'soil_amendment'
  | 'weeding'
  | 'inspection'
  | 'delayed_action'
  | 'other';

export interface HypotheticalAction {
  action_type: SimulationActionType;
  action_date?: string;
  metadata?: Record<string, unknown>;
}

export interface SimulationRequest {
  hypothetical_actions: HypotheticalAction[];
}

export interface SimulationStateSnapshot {
  state: string;
  stress: number;
  risk: number;
  day_number: number;
  stage?: string | null;
}

export interface SimulationActionBreakdown {
  action_index: number;
  action_type: string;
  action_date?: string | null;
  day_delta: number;
  day_number_before: number;
  day_number_after: number;
  stage_before?: string | null;
  stage_after?: string | null;
  stress_delta: number;
  stress_after: number;
  risk_delta: number;
  risk_after: number;
  details?: Record<string, unknown>;
}

export interface SimulationResponse {
  current_state: SimulationStateSnapshot;
  projected_state: SimulationStateSnapshot;
  deltas: {
    stress: number;
    risk: number;
    days: number;
    stage_changed: boolean;
  };
  action_breakdowns: SimulationActionBreakdown[];
  state_transitions: Array<{
    from_stage?: string | null;
    to_stage?: string | null;
    at_action: number;
    at_day: number;
  }>;
  warnings: string[];
  actions_applied: number;

  // Backward-compatible scalar fields returned by backend.
  projected_stress: number;
  projected_risk: number;
  projected_day_number: number;
  projected_stage?: string | null;
}

export interface YieldRecord {
  id: string;
  crop_instance_id: string;
  reported_yield: number;
  yield_unit: string;
  harvest_date?: string | null;
  ml_yield_value?: number | null;
  biological_cap?: number | null;
  bio_cap_applied: boolean;
  yield_verification_score?: number | null;
  verification_metadata?: Record<string, unknown> | null;
  quality_grade?: string | null;
  moisture_pct?: number | null;
  notes?: string | null;
  created_at: string;
}
