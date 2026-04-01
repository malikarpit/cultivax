import { apiGet, apiPost, apiDelete } from '../lib/api';

export interface MediaUploadResponse {
  media_id: string;
  analysis_status: string;
  preview_url: string;
  uploaded_at: string;
}

export interface MediaDetailResponse {
  media_id: string;
  crop_instance_id: string;
  mime_type?: string;
  file_size_bytes?: number;
  analysis_status: string;
  image_quality_score?: number;
  pest_probability?: number;
  stress_probability?: number;
  confidence_score?: number;
  is_quarantined: boolean;
  created_at: string;
  download_url: string;
}

export interface MediaListResponse {
  media_id: string;
  analysis_status: string;
  image_quality_score?: number;
  pest_probability?: number;
  stress_probability?: number;
  created_at: string;
}

export const mediaService = {
  uploadMedia: async (cropId: string, file: File, sourceChannel: string = 'web', geoVerified: boolean = false, lat?: number, lng?: number): Promise<MediaUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_channel', sourceChannel);
    formData.append('geo_verified', geoVerified.toString());
    if (lat) formData.append('capture_lat', lat.toString());
    if (lng) formData.append('capture_lng', lng.toString());
    
    const response = await apiPost<MediaUploadResponse>(`/api/v1/crops/${cropId}/media`, formData);
    return response;
  },

  listMedia: async (cropId: string, status?: string): Promise<MediaListResponse[]> => {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    const response = await apiGet<MediaListResponse[]>(`/api/v1/crops/${cropId}/media${query}`);
    return response;
  },

  getMediaDetail: async (mediaId: string): Promise<MediaDetailResponse> => {
    const response = await apiGet<MediaDetailResponse>(`/api/v1/media/${mediaId}`);
    return response;
  },

  deleteMedia: async (mediaId: string): Promise<void> => {
    await apiDelete(`/api/v1/media/${mediaId}`);
  },
};
