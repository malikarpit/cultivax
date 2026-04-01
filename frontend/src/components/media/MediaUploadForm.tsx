import React, { useState, useRef } from 'react';
import { Camera, Image as ImageIcon, X, Upload, Loader2, AlertCircle } from 'lucide-react';
import { useMediaUpload } from '../../hooks/useMediaUpload';
import { useTranslation } from 'react-i18next';

interface MediaUploadFormProps {
  cropId: string;
  onSuccess?: () => void;
}

export function MediaUploadForm({ cropId, onSuccess }: MediaUploadFormProps) {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewSize, setPreviewSize] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const { upload, isUploading, error } = useMediaUpload();

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
      alert(t('media.invalidType', 'Please upload an image or video file.'));
      return;
    }
    const sizeMb = file.size / (1024 * 1024);
    if (sizeMb > 20) {
      alert(t('media.fileTooLarge', 'File must be under 20MB.'));
      return;
    }
    
    setSelectedFile(file);
    setPreviewSize(`${sizeMb.toFixed(1)} MB`);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      await upload(cropId, selectedFile, {
        sourceChannel: 'web',
        geoVerified: false,
        onSuccess: () => {
          setSelectedFile(null);
          setPreviewSize(null);
          if (onSuccess) onSuccess();
        }
      });
    } catch (err) {
      console.error('Upload failed', err);
    }
  };

  const getPreviewUrl = () => {
    return selectedFile ? URL.createObjectURL(selectedFile) : '';
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm">
      <h3 className="text-xl font-semibold text-white/90 mb-4 flex items-center gap-2">
        <Camera className="w-5 h-5 text-emerald-400" />
        {t('media.uploadPhoto', 'Upload Crop Photo')}
      </h3>
      
      {!selectedFile ? (
        <label 
          className={`flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
            dragActive ? 'border-emerald-500 bg-emerald-500/10' : 'border-white/20 hover:border-emerald-400/50 hover:bg-white/5'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <Upload className="w-10 h-10 text-white/40 mb-3" />
            <p className="mb-2 text-sm text-white/70">
              <span className="font-semibold text-emerald-400">{t('media.clickToUpload', 'Click to upload')}</span> {t('media.orDragDrop', 'or drag and drop')}
            </p>
            <p className="text-xs text-white/50">JPG, PNG, WEBP (Max 20MB)</p>
          </div>
          <input 
            ref={fileInputRef}
            type="file" 
            className="hidden" 
            accept="image/*,video/*"
            onChange={handleChange}
          />
        </label>
      ) : (
        <div className="relative rounded-xl overflow-hidden border border-white/10 bg-black/30 w-full mb-4">
          {selectedFile.type.startsWith('image/') ? (
            <img 
              src={getPreviewUrl()} 
              alt="Preview" 
              className="w-full h-48 object-cover"
            />
          ) : (
            <div className="w-full h-48 flex items-center justify-center text-white/50">
               <ImageIcon className="w-12 h-12" /> Video Selected
            </div>
          )}
          
          <div className="absolute top-0 right-0 p-2">
            <button
              type="button"
              onClick={() => setSelectedFile(null)}
              className="p-1.5 bg-red-500/80 hover:bg-red-500 text-white rounded-lg backdrop-blur-md transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <div className="absolute bottom-0 inset-x-0 p-3 bg-gradient-to-t from-black/80 to-transparent">
            <p className="text-sm font-medium text-white truncate">{selectedFile.name}</p>
            <p className="text-xs text-white/70">{previewSize}</p>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <p className="text-sm text-red-200">
            {error.message || t('media.uploadFailed', 'Failed to upload media. Please try again.')}
          </p>
        </div>
      )}

      <div className="mt-6 flex justify-end">
        <button
          type="submit"
          disabled={!selectedFile || isUploading}
          className="px-6 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-white font-medium shadow-lg rounded-xl flex items-center gap-2 placeholder:transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t('common.processing', 'Processing...')}
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              {t('common.submit', 'Submit')}
            </>
          )}
        </button>
      </div>
    </form>
  );
}
