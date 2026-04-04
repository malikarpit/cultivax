import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cultivax: {
          // Core backgrounds
          bg: '#0B0F19',
          surface: '#111827',
          elevated: '#1F2937',
          
          // Borders
          border: '#1F2937',
          'border-highlight': '#374151',
          
          // Primary brand
          primary: '#10B981',
          'primary-hover': '#059669',
          'primary-light': '#10B98120',
          
          // Accent
          accent: '#F59E0B',
          'accent-hover': '#D97706',
          'accent-light': '#F59E0B20',
          
          // Semantic
          danger: '#EF4444',
          'danger-light': '#EF444420',
          info: '#3B82F6',
          'info-light': '#3B82F620',
          
          // Text
          'text-primary': '#F9FAFB',
          'text-secondary': '#9CA3AF',
          'text-muted': '#6B7280',
          
          // Card
          card: '#1E293B',
          'card-hover': '#334155',
        },
        // M3-inspired surface system for glass cards
        'm3': {
          'surface-dim': '#0d1322',
          'surface': '#0d1322',
          'surface-bright': '#33394a',
          'surface-container-lowest': '#080e1d',
          'surface-container-low': '#151b2b',
          'surface-container': '#191f2f',
          'surface-container-high': '#242a3a',
          'surface-container-highest': '#2f3445',
          'on-surface': '#dde2f8',
          'on-surface-variant': '#bbcac0',
          'outline': '#85948b',
          'outline-variant': '#3c4a42',
          'primary': '#5af0b3',
          'primary-container': '#34d399',
          'on-primary': '#003825',
          'secondary': '#ffb95f',
          'secondary-container': '#ee9800',
          'on-secondary': '#472a00',
          'tertiary': '#bfd8ff',
          'tertiary-container': '#8ebdff',
          'error': '#ffb4ab',
          'error-container': '#93000a',
          'inverse-surface': '#dde2f8',
          'inverse-on-surface': '#2a3040',
          'surface-tint': '#45dfa4',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        headline: ['Inter', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1.15' }],
        '6xl': ['3.75rem', { lineHeight: '1.1' }],
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'glow-green': '0 0 20px rgba(16, 185, 129, 0.15)',
        'glow-amber': '0 0 20px rgba(245, 158, 11, 0.15)',
        'glow-red': '0 0 20px rgba(239, 68, 68, 0.15)',
        'glow-blue': '0 0 20px rgba(59, 130, 246, 0.15)',
        'glow-primary-nav': '0 24px 24px rgba(69, 223, 164, 0.06)',
        'card': '0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.4)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.4), 0 2px 4px rgba(0, 0, 0, 0.3)',
        'elevated': '0 10px 40px rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'spin-slow': 'spin 3s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 5px rgba(16, 185, 129, 0.2)' },
          '50%': { boxShadow: '0 0 20px rgba(16, 185, 129, 0.5)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      screens: {
        'xs': '475px',
      },
    },
  },
  plugins: [],
}
export default config
