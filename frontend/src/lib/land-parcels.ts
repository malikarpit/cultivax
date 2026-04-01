import { apiDelete, apiGet, apiPost, apiPut } from '@/lib/api';
import type { LandParcel, LandParcelCreate, LandParcelUpdate } from '@/lib/types';

export async function listLandParcels(includeDeleted = false): Promise<LandParcel[]> {
  const query = includeDeleted ? '?include_deleted=true' : '';
  return apiGet<LandParcel[]>(`/api/v1/land-parcels${query}`);
}

export async function getLandParcel(parcelId: string): Promise<LandParcel> {
  return apiGet<LandParcel>(`/api/v1/land-parcels/${parcelId}`);
}

export async function createLandParcel(payload: LandParcelCreate): Promise<LandParcel> {
  return apiPost<LandParcel>('/api/v1/land-parcels', payload);
}

export async function updateLandParcel(
  parcelId: string,
  payload: LandParcelUpdate
): Promise<LandParcel> {
  return apiPut<LandParcel>(`/api/v1/land-parcels/${parcelId}`, payload);
}

export async function deleteLandParcel(parcelId: string): Promise<void> {
  await apiDelete<void>(`/api/v1/land-parcels/${parcelId}`);
}

export async function restoreLandParcel(parcelId: string): Promise<void> {
  await apiPost<void>(`/api/v1/land-parcels/${parcelId}/restore`, {});
}
