import { useState } from 'react';
import { mediaService, MediaUploadResponse } from '../services/media';

interface UploadOptions {
  onSuccess?: (response: MediaUploadResponse) => void;
  onError?: (error: Error) => void;
  sourceChannel?: string;
  geoVerified?: boolean;
}

export const useMediaUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const upload = async (
    cropId: string,
    file: File,
    options?: UploadOptions
  ) => {
    setIsUploading(true);
    setError(null);

    try {
      // Optional: Add EXIF extraction for coordinates here
      const lat = undefined;
      const lng = undefined;

      const response = await mediaService.uploadMedia(
        cropId,
        file,
        options?.sourceChannel || 'web',
        options?.geoVerified || false,
        lat,
        lng
      );
      
      options?.onSuccess?.(response);
      return response;
    } catch (err: any) {
      setError(err as Error);
      options?.onError?.(err as Error);
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  return { upload, isUploading, error };
};
