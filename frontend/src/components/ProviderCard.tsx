/**
 * Provider Card — Displays service provider details in the marketplace.
 * Shows trust score, specializations, verification status, and service CTA.
 */

'use client';

interface ProviderCardProps {
  id: string;
  business_name: string;
  region: string;
  service_types: string[];
  crop_specializations: string[];
  trust_score: number;
  is_verified: boolean;
  completed_requests: number;
  response_time_hours?: number;
  onRequestService?: (providerId: string) => void;
}

const trustColor = (score: number): string => {
  if (score >= 0.8) return 'text-green-400';
  if (score >= 0.5) return 'text-yellow-400';
  return 'text-red-400';
};

const trustBarColor = (score: number): string => {
  if (score >= 0.8) return 'bg-green-500';
  if (score >= 0.5) return 'bg-yellow-500';
  return 'bg-red-500';
};

export default function ProviderCard({
  id,
  business_name,
  region,
  service_types,
  crop_specializations,
  trust_score,
  is_verified,
  completed_requests,
  response_time_hours,
  onRequestService,
}: ProviderCardProps) {
  return (
    <div className="card hover:scale-[1.02] cursor-pointer group">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-lg truncate">{business_name}</h3>
            {is_verified && (
              <span className="flex-shrink-0 bg-green-500/20 text-green-400 text-xs px-2 py-0.5 rounded-full font-medium">
                ✓ Verified
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-0.5">{region}</p>
        </div>
      </div>

      {/* Trust Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-1.5">
          <span className="text-gray-400">Trust Score</span>
          <span className={`font-semibold ${trustColor(trust_score)}`}>
            {(trust_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${trustBarColor(trust_score)}`}
            style={{ width: `${trust_score * 100}%` }}
          />
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 gap-3 text-sm mb-4">
        <div className="bg-cultivax-bg/50 rounded-lg px-3 py-2">
          <span className="text-gray-400 text-xs block">Completed Jobs</span>
          <span className="font-medium">{completed_requests}</span>
        </div>
        {response_time_hours !== undefined && (
          <div className="bg-cultivax-bg/50 rounded-lg px-3 py-2">
            <span className="text-gray-400 text-xs block">Avg Response</span>
            <span className="font-medium">{response_time_hours}h</span>
          </div>
        )}
      </div>

      {/* Service Types */}
      {service_types.length > 0 && (
        <div className="mb-3">
          <span className="text-xs text-gray-400 block mb-1.5">Services</span>
          <div className="flex flex-wrap gap-1.5">
            {service_types.map((type) => (
              <span
                key={type}
                className="bg-blue-500/15 text-blue-400 text-xs px-2 py-0.5 rounded-full"
              >
                {type}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Crop Specializations */}
      {crop_specializations.length > 0 && (
        <div className="mb-4">
          <span className="text-xs text-gray-400 block mb-1.5">Crop Specializations</span>
          <div className="flex flex-wrap gap-1.5">
            {crop_specializations.map((crop) => (
              <span
                key={crop}
                className="bg-cultivax-primary/15 text-cultivax-primary text-xs px-2 py-0.5 rounded-full capitalize"
              >
                {crop}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* CTA */}
      {onRequestService && (
        <button
          onClick={() => onRequestService(id)}
          className="w-full btn-primary text-sm py-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
        >
          Request Service
        </button>
      )}
    </div>
  );
}
