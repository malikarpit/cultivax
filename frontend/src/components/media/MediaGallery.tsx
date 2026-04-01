import React, { useEffect, useState } from 'react';
import { mediaService, MediaListResponse } from '../../services/media';
import { useTranslation } from 'react-i18next';
import { Image as ImageIcon, Video, Loader2, AlertTriangle, ShieldCheck } from 'lucide-react';

interface MediaGalleryProps {
  cropId: string;
  refreshKey?: number;
}

export function MediaGallery({ cropId, refreshKey = 0 }: MediaGalleryProps) {
  const { t } = useTranslation();
  const [mediaItems, setMediaItems] = useState<MediaListResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMedia() {
      try {
        setLoading(true);
        const data = await mediaService.listMedia(cropId);
        setMediaItems(data);
      } catch (err) {
        console.error('Failed to fetch media', err);
      } finally {
        setLoading(false);
      }
    }
    fetchMedia();
  }, [cropId, refreshKey]);

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
      </div>
    );
  }

  if (mediaItems.length === 0) {
    return (
      <div className="text-center p-8 bg-black/10 rounded-2xl border border-white/5">
        <ImageIcon className="w-12 h-12 text-white/20 mx-auto mb-3" />
        <p className="text-white/60">{t('media.noMedia', 'No media uploaded yet.')}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {mediaItems.map((item) => (
        <MediaCard key={item.media_id} item={item} />
      ))}
    </div>
  );
}

function MediaCard({ item }: { item: MediaListResponse }) {
  const [imageUrl, setImageUrl] = useState<string>('');
  
  // Format date
  const date = new Date(item.created_at).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric'
  });

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'analyzed': return 'text-emerald-400';
      case 'pending': return 'text-amber-400';
      case 'failed': return 'text-red-400';
      default: return 'text-white/50';
    }
  };

  return (
    <div className="group relative rounded-2xl overflow-hidden border border-white/10 bg-black/40 hover:border-emerald-500/50 hover:shadow-[0_0_20px_rgba(16,185,129,0.15)] transition-all duration-300 transform aspect-square cursor-pointer">
      {/* Background Image Loading */}
      <img
        src={`/api/v1/media/${item.media_id}/download?variant=preview`}
        alt="Crop media"
        className="object-cover w-full h-full opacity-80 group-hover:scale-110 group-hover:opacity-100 transition-transform duration-500"
        loading="lazy"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
      
      {/* Analysis overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent p-4 flex flex-col justify-end">
        <p className="text-sm font-medium text-white mb-1">{date}</p>
        
        <div className="flex items-center gap-2">
           <span className={`text-xs capitalize font-medium ${getStatusColor(item.analysis_status)}`}>
             {item.analysis_status}
           </span>
           {item.analysis_status === 'analyzed' && (
              <div className="flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                {item.pest_probability && item.pest_probability > 0.6 && (
                  <span className="bg-red-500/20 text-red-300 text-[10px] px-1.5 py-0.5 rounded border border-red-500/20" title="Pest Detected">P</span>
                )}
                {item.stress_probability && item.stress_probability > 0.6 && (
                  <span className="bg-amber-500/20 text-amber-300 text-[10px] px-1.5 py-0.5 rounded border border-amber-500/20" title="Stress Detected">S</span>
                )}
              </div>
           )}
        </div>
      </div>
    </div>
  );
}
