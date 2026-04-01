export interface WeatherAlertItem {
    code: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    message: string;
    starts_at?: string;
    ends_at?: string;
}

export interface WeatherDataSchema {
    temperature: number;
    humidity: number;
    wind_speed_kmh: number;
    rainfall_mm: number;
    description: string;
    uv_index?: number;
    forecast_3d: any[];
}

export interface WeatherRiskResponse {
    weather_data: WeatherDataSchema;
    weather_risk_score: number;
    alerts: WeatherAlertItem[];
    source: string;
    is_fallback: boolean;
    weather_confidence: number;
    updated_at: string;
    ttl_seconds: number;
    crop_impact?: string;
    coordinate_source?: string;
}
