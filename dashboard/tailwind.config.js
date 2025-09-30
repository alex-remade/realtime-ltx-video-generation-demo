/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // FAL Brand Colors - Light Theme (flattened structure)
        'fal-gray': {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
          950: '#030712'
        },
        'fal-primary': {
          400: '#8b5cf6',
          500: '#6d28d9',
          600: '#5b21b6',
          700: '#4c1d95'
        },
        'fal-green': {
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d'
        },
        'fal-yellow': {
          400: '#facc15',
          500: '#eab308',
          600: '#ca8a04',
          700: '#a16207'
        },
        'fal-blue': {
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8'
        },
        'fal-red': {
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c'
        },
        // Also keep the nested structure for backward compatibility
        fal: {
          light: '#ffffff',
          lighter: '#fafafa',
          gray: {
            50: '#f9fafb',
            100: '#f3f4f6',
            200: '#e5e7eb',
            300: '#d1d5db',
            400: '#9ca3af',
            500: '#6b7280',
            600: '#4b5563',
            700: '#374151',
            800: '#1f2937',
            900: '#111827',
            950: '#030712'
          },
          primary: {
            400: '#8b5cf6',
            500: '#6d28d9',
            600: '#5b21b6',
            700: '#4c1d95'
          },
          green: {
            400: '#4ade80',
            500: '#22c55e',
            600: '#16a34a',
            700: '#15803d'
          },
          yellow: {
            400: '#facc15',
            500: '#eab308',
            600: '#ca8a04',
            700: '#a16207'
          },
          blue: {
            400: '#60a5fa',
            500: '#3b82f6',
            600: '#2563eb',
            700: '#1d4ed8'
          },
          red: {
            400: '#f87171',
            500: '#ef4444',
            600: '#dc2626',
            700: '#b91c1c'
          }
        },
        // Legacy colors for compatibility
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        success: '#22c55e',
        warning: '#eab308',
        danger: '#ef4444',
      },
      fontFamily: {
        'sans': ['Focal', 'Inter', 'system-ui', 'sans-serif'],
        'focal': ['Focal', 'Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      fontWeight: {
        'light': '300',
        'normal': '300',  // Map normal to light
        'medium': '400',  // Map medium to regular
        'semibold': '500', // Map semibold to medium
        'bold': '500',    // Map bold to medium (lighter than usual)
        'extrabold': '700' // Keep true bold for when really needed
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        }
      }
    },
  },
  plugins: [],
}
