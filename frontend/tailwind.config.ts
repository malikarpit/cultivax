import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cultivax: {
          primary: '#10B981',
          secondary: '#059669',
          dark: '#064E3B',
          light: '#D1FAE5',
          accent: '#F59E0B',
          bg: '#0F172A',
          surface: '#1E293B',
          card: '#334155',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
