import { apiGet } from '@/lib/api';
import { WeatherRiskResponse } from '@/types/weather';

export const weatherApi: {
    getWeatherByCoords: (lat: number, lng: number) => Promise<WeatherRiskResponse>;
    getCropWeatherRisk: (cropId: string) => Promise<WeatherRiskResponse>;
} = {
    getWeatherByCoords: async (lat: number, lng: number) => {
        return apiGet(`/api/v1/weather?lat=${lat}&lng=${lng}`);
    },
    getCropWeatherRisk: async (cropId: string) => {
        return apiGet(`/api/v1/weather/risk?crop_id=${cropId}`);
    }
};
