'use client';

/**
 * Weather Intelligence Dashboard
 * 
 * Reference: stitch_landing_page 3/weather_dashboard
 * Sections:
 *  1. Alert banner (heat/storm warnings)
 *  2. Hero weather card (6xl temp) + 5-day outlook sidebar
 *  3. Historical Rainfall bar chart + Soil Moisture SVG projection
 *  4. Bento grid: Solar, Leaf Temp, Air Pressure, Audit Status
 */

import { useState, useEffect } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import {
  Sun, Cloud, CloudRain, Wind, Droplets, Thermometer,
  AlertTriangle, X, Zap, ShieldCheck, Gauge,
  CloudLightning, CloudSnow, CloudSun,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, AreaChart, Area,
} from 'recharts';
import clsx from 'clsx';
import { useAuth } from '@/context/AuthContext';
import { weatherApi } from '@/services/weather';
import { WeatherRiskResponse } from '@/types/weather';

/* ─── Mock Data ──────────────────────────────────────────── */

const RAINFALL_DATA = [
  { day: 'MON', mm: 1.2 },
  { day: 'TUE', mm: 4.8 },
  { day: 'WED', mm: 0.5 },
  { day: 'THU', mm: 0.2 },
  { day: 'FRI', mm: 6.2 },
  { day: 'SAT', mm: 2.8 },
  { day: 'SUN', mm: 0.9 },
];

const SOIL_MOISTURE_DATA = [
  { day: 'Mon', actual: 35, projected: null },
  { day: 'Tue', actual: 32, projected: null },
  { day: 'Wed', actual: 38, projected: null },
  { day: 'Thu', actual: 30, projected: null },
  { day: 'Fri', actual: 25, projected: 25 },
  { day: 'Sat', actual: null, projected: 22 },
  { day: 'Sun', actual: null, projected: 18 },
];

const FORECAST = [
  { day: 'TUE', icon: Sun, iconColor: 'text-m3-secondary', high: 34, low: 22 },
  { day: 'WED', icon: Droplets, iconColor: 'text-m3-primary', high: 28, low: 19, active: true },
  { day: 'THU', icon: Cloud, iconColor: 'text-m3-primary', high: 24, low: 17 },
  { day: 'FRI', icon: Wind, iconColor: 'text-m3-on-surface-variant', high: 26, low: 18 },
  { day: 'SAT', icon: Sun, iconColor: 'text-m3-secondary', high: 31, low: 21 },
];

/* ─── Growth Gauge SVG ───────────────────────────────────── */

function GrowthGauge({ percent, color, label }: { percent: number; color: string; label: string }) {
  return (
    <div className="text-center">
      <div className="relative w-12 h-12 flex items-center justify-center mx-auto">
        <svg className="absolute inset-0 -rotate-90" viewBox="0 0 36 36">
          <circle
            cx="18" cy="18" r="16"
            fill="none" stroke="#242a3a" strokeWidth="3"
            strokeDasharray="100 100"
          />
          <circle
            cx="18" cy="18" r="16"
            fill="none" stroke={color} strokeWidth="3"
            strokeDasharray={`${percent} 100`}
            strokeLinecap="round"
            className="transition-all duration-700"
          />
        </svg>
        <span className="text-[10px] font-bold font-mono">{percent}%</span>
      </div>
      <span className="text-[8px] uppercase tracking-tighter text-m3-on-surface-variant block mt-1">
        {label}
      </span>
    </div>
  );
}

/* ─── Page Component ─────────────────────────────────────── */

export default function WeatherDashboardPage() {
  const { user } = useAuth();
  const [alertDismissed, setAlertDismissed] = useState(false);
  const [weatherData, setWeatherData] = useState<WeatherRiskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorLocal, setErrorLocal] = useState<string | null>(null);

  useEffect(() => {
    // Determine default coords based on user region if we wanted to, or fallback to Delhi
    const fetchWeather = async (lat = 28.61, lng = 77.23) => {
      try {
        const res = await weatherApi.getWeatherByCoords(lat, lng);
        setWeatherData(res);
      } catch (err: any) {
        setErrorLocal(err.message || 'Failed to fetch weather');
      } finally {
        setLoading(false);
      }
    };
    fetchWeather();
  }, []);

  const handleLocateMe = () => {
    if ("geolocation" in navigator) {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          try {
            const res = await weatherApi.getWeatherByCoords(pos.coords.latitude, pos.coords.longitude);
            setWeatherData(res);
            setAlertDismissed(false); // Reset alerts so they show up
          } catch(err: any) {
            setErrorLocal(err.message);
          } finally {
            setLoading(false);
          }
        },
        (err) => {
          alert("Location access denied or unavailable.");
          setLoading(false);
        }
      );
    }
  };

  const activeAlerts = weatherData?.alerts || [];
  const currentTemp = weatherData ? Math.round(weatherData.weather_data.temperature) : 32;
  const currentDesc = weatherData ? weatherData.weather_data.description : 'Partly Cloudy';
  const currentHum = weatherData ? Math.round(weatherData.weather_data.humidity) : 48;
  const currentWind = weatherData ? Math.round(weatherData.weather_data.wind_speed_kmh) : 12;

  return (
    <ProtectedRoute>
    <div className="animate-fade-in space-y-8">
      {/* ═══ Header Action ═══ */}
      <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Weather Intelligence</h2>
          <button onClick={handleLocateMe} disabled={loading} className="bg-m3-primary/10 hover:bg-m3-primary/20 text-m3-primary text-sm font-bold px-4 py-2 rounded-xl transition-colors">
            {loading ? 'Locating...' : 'Use My GPS Location'}
          </button>
      </div>

      {/* ═══ Alert Banner ═══ */}
      {!alertDismissed && activeAlerts.map((alert, idx) => (
        <div key={idx} className="p-4 rounded-xl bg-m3-error-container/20 border border-m3-error/20 flex items-center justify-between animate-slide-down mb-4">
          <div className="flex items-center gap-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${alert.severity === 'CRITICAL' ? 'bg-m3-error/20 text-m3-error' : 'bg-orange-500/20 text-orange-500'}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-m3-error text-sm uppercase">{alert.code} Warning</h4>
              <p className="text-m3-on-surface-variant text-sm">
                {alert.message}
              </p>
            </div>
          </div>
          <button
            onClick={() => setAlertDismissed(true)}
            className="text-m3-on-surface hover:text-m3-error transition-colors px-4 py-1 text-sm font-bold uppercase tracking-widest font-mono"
          >
            Dismiss
          </button>
        </div>
      ))}

      {/* ═══ Hero Row: Weather + 5-Day ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Hero Weather Card */}
        <section className="lg:col-span-8 glass-card rounded-3xl p-8 relative overflow-hidden flex flex-col justify-between">
          <div className="absolute top-0 right-0 w-64 h-64 bg-m3-primary/5 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />
          <div className="relative z-10 flex-grow flex flex-col justify-between">
            <div className="flex justify-between items-start mb-8">
              <div>
                <div className="flex items-center gap-3">
                    <span className="mono-label tracking-[0.2em] uppercase">
                    Current Conditions • {user?.region || 'Delhi'}
                    </span>
                    {weatherData && (
                        <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${weatherData.is_fallback ? 'bg-orange-500/10 text-orange-500 border border-orange-500/20' : 'bg-m3-primary/10 text-m3-primary border border-m3-primary/20'}`}>
                            {weatherData.is_fallback ? 'Fallback' : 'Live'}
                        </span>
                    )}
                </div>
                <h1 className="text-6xl md:text-7xl font-black mt-2 tracking-tighter font-mono">
                  {currentTemp}<span className="text-m3-primary">°C</span>
                </h1>
                <p className="text-m3-on-surface-variant mt-1 font-medium capitalize flex items-center gap-2">
                  {currentDesc}. 
                  {weatherData && weatherData.weather_risk_score > 0.5 && <span className="text-orange-400">High Risk Detected</span>}
                </p>
              </div>
              <Cloud className="w-16 h-16 text-m3-primary opacity-60" />
            </div>

            {/* Metric Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-auto">
              <div className="bg-m3-surface-container-low rounded-xl p-4 transition-colors hover:bg-m3-surface-container">
                <span className="mono-label block mb-1 text-m3-on-surface-variant">Humidity</span>
                <span className="font-mono text-xl md:text-2xl font-bold">{currentHum}%</span>
              </div>
              <div className="bg-m3-surface-container-low rounded-xl p-4 transition-colors hover:bg-m3-surface-container">
                <span className="mono-label block mb-1 text-m3-on-surface-variant">Wind Speed</span>
                <span className="font-mono text-xl md:text-2xl font-bold text-m3-secondary">
                  {currentWind}<span className="text-sm font-normal ml-1">km/h</span>
                </span>
              </div>
              <div className="bg-m3-surface-container-low rounded-xl p-4 transition-colors hover:bg-m3-surface-container">
                <span className="mono-label block mb-1 text-m3-on-surface-variant">Risk Score</span>
                <span className={`font-mono text-xl md:text-2xl font-bold ${weatherData?.weather_risk_score && weatherData.weather_risk_score > 0.5 ? 'text-m3-error' : 'text-m3-primary'}`}>
                    {weatherData ? Math.round(weatherData.weather_risk_score * 100) : '--'}
                </span>
              </div>
              <div className="bg-m3-surface-container-low rounded-xl p-4 transition-colors hover:bg-m3-surface-container">
                <span className="mono-label block mb-1 text-m3-on-surface-variant">Data Source</span>
                <span className="font-mono text-lg font-bold capitalize pt-1 block truncate">
                    {weatherData?.source || 'Loading...'}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* 5-Day Forecast */}
        <section className="lg:col-span-4 space-y-4">
          <h3 className="text-sm font-bold uppercase tracking-widest text-m3-on-surface-variant ml-2">
            5-Day Outlook
          </h3>
          <div className="space-y-3">
            {FORECAST.map((day) => {
              const Icon = day.icon;
              return (
                <div
                  key={day.day}
                  className={clsx(
                    'glass-card rounded-xl p-4 flex items-center justify-between transition-colors',
                    day.active
                      ? 'bg-m3-surface-container-high border-m3-primary/20'
                      : 'hover:bg-m3-surface-container-high'
                  )}
                >
                  <span className="w-12 font-semibold text-sm">{day.day}</span>
                  <Icon className={clsx('w-5 h-5', day.iconColor)} />
                  <div className="flex gap-4 font-mono text-sm">
                    <span className="text-m3-on-surface font-bold">{day.high}°</span>
                    <span className="text-m3-on-surface-variant">{day.low}°</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      {/* ═══ Charts Row ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Historical Rainfall */}
        <section className="glass-card rounded-3xl p-8 border border-m3-outline-variant/10">
          <div className="flex justify-between items-center mb-8">
            <h3 className="font-bold text-lg text-m3-on-surface">Historical Rainfall</h3>
            <span className="mono-label">Last 7 Days (mm)</span>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={RAINFALL_DATA} barCategoryGap="15%">
                <CartesianGrid strokeDasharray="3 3" stroke="#2f3445" vertical={false} />
                <XAxis
                  dataKey="day"
                  tick={{ fontSize: 10, fill: '#85948b' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#85948b' }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: 'rgba(90, 240, 179, 0.05)' }}
                  contentStyle={{
                    background: '#242a3a',
                    border: '1px solid #3c4a42',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontFamily: 'JetBrains Mono',
                    color: '#dde2f8',
                  }}
                  formatter={(value: any) => [`${value} mm`, 'Rainfall']}
                />
                <Bar
                  dataKey="mm"
                  fill="#2f3445"
                  radius={[6, 6, 0, 0]}
                  activeBar={{
                    fill: 'rgba(90, 240, 179, 0.4)',
                    stroke: '#5af0b3',
                    strokeWidth: 1,
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Soil Moisture Projection */}
        <section className="glass-card rounded-3xl p-8 border border-m3-outline-variant/10 relative">
          <div className="flex justify-between items-center mb-8">
            <h3 className="font-bold text-lg text-m3-on-surface">Soil Moisture Projection</h3>
            <div className="flex gap-3">
              <span className="inline-flex items-center gap-1.5 text-[10px] text-m3-on-surface-variant font-mono">
                <span className="w-2 h-2 rounded-full bg-m3-primary" /> ACTUAL
              </span>
              <span className="inline-flex items-center gap-1.5 text-[10px] text-m3-on-surface-variant font-mono">
                <span className="w-2 h-2 rounded-full border border-dashed border-m3-primary/50" /> PROJECTION
              </span>
            </div>
          </div>

          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={SOIL_MOISTURE_DATA}>
                <defs>
                  <linearGradient id="moistureGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#5af0b3" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#5af0b3" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2f3445" vertical={false} />
                <XAxis
                  dataKey="day"
                  tick={{ fontSize: 10, fill: '#85948b' }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: '#85948b' }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 50]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    background: '#242a3a',
                    border: '1px solid #3c4a42',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontFamily: 'JetBrains Mono',
                    color: '#dde2f8',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="actual"
                  stroke="#5af0b3"
                  fill="url(#moistureGrad)"
                  strokeWidth={2}
                  connectNulls={false}
                  name="Actual"
                />
                <Area
                  type="monotone"
                  dataKey="projected"
                  stroke="#5af0b3"
                  strokeDasharray="5 5"
                  fill="none"
                  strokeWidth={1.5}
                  connectNulls={false}
                  name="Projected"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Growth Gauges overlay */}
          <div className="absolute bottom-6 right-6 flex items-center gap-6 bg-m3-surface-container-lowest/80 backdrop-blur px-6 py-4 rounded-2xl border border-m3-outline-variant/10">
            <GrowthGauge percent={72} color="#5af0b3" label="Satur." />
            <GrowthGauge percent={45} color="#ffb95f" label="Growth" />
          </div>
        </section>
      </div>

      {/* ═══ Bento Widgets ═══ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card p-6 rounded-2xl border border-m3-outline-variant/10 flex flex-col justify-between">
          <div>
            <Zap className="w-6 h-6 text-m3-primary mb-2" />
            <h5 className="mono-label font-bold">Solar Efficiency</h5>
          </div>
          <div className="mt-4">
            <p className="font-mono text-2xl font-bold">94%</p>
            <p className="text-[10px] text-m3-primary mt-1 uppercase">Optimal Production</p>
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-m3-outline-variant/10 flex flex-col justify-between">
          <div>
            <Thermometer className="w-6 h-6 text-m3-secondary mb-2" />
            <h5 className="mono-label font-bold">Leaf Temperature</h5>
          </div>
          <div className="mt-4">
            <p className="font-mono text-2xl font-bold">29.4°C</p>
            <p className="text-[10px] text-m3-on-surface-variant mt-1 uppercase">Nominal Range</p>
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-m3-outline-variant/10 flex flex-col justify-between">
          <div>
            <Gauge className="w-6 h-6 text-m3-primary mb-2" />
            <h5 className="mono-label font-bold">Air Pressure</h5>
          </div>
          <div className="mt-4">
            <p className="font-mono text-2xl font-bold">
              1014 <span className="text-xs">hPa</span>
            </p>
            <p className="text-[10px] text-m3-on-surface-variant mt-1 uppercase">Stable Conditions</p>
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-m3-outline-variant/10 flex flex-col justify-between">
          <div>
            <ShieldCheck className="w-6 h-6 text-m3-primary mb-2" />
            <h5 className="mono-label font-bold">Audit Status</h5>
          </div>
          <div className="mt-4">
            <p className="text-sm font-semibold text-m3-on-surface">Climate Compliance Met</p>
            <div className="w-full bg-m3-surface-container-highest h-1 rounded-full mt-2 overflow-hidden">
              <div className="h-full bg-m3-primary w-full rounded-full" />
            </div>
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  );
}
