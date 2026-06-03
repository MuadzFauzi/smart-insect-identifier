/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        serif:  ['Playfair Display', 'Georgia', 'serif'],
        sans:   ['DM Sans', 'system-ui', 'sans-serif'],
        mono:   ['DM Mono', 'monospace'],
      },
      colors: {
        parchment: {
          50:  '#fdfaf4',
          100: '#f9f2e3',
          200: '#f0e0bf',
          300: '#e5c98a',
          400: '#d4a853',
          500: '#b8882e',
        },
        forest: {
          50:  '#f0f7f0',
          100: '#dceedd',
          200: '#b4d9b7',
          300: '#7dbd83',
          400: '#4a9d52',
          500: '#2d7d35',
          600: '#1e5e25',
          700: '#164519',
          800: '#0f2f11',
          900: '#091a0a',
        },
        ink: {
          50:  '#f5f5f0',
          100: '#e8e8e0',
          200: '#d0d0c4',
          300: '#a8a896',
          400: '#7a7a6a',
          500: '#555548',
          600: '#3a3a30',
          700: '#282820',
          800: '#1a1a14',
          900: '#0e0e0a',
        },
      },
      animation: {
        'fade-up':     'fadeUp 0.6s ease forwards',
        'fade-in':     'fadeIn 0.4s ease forwards',
        'scan':        'scan 2s ease-in-out infinite',
        'bar-fill':    'barFill 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-slow':  'pulse 3s ease-in-out infinite',
        'spin-slow':   'spin 3s linear infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scan: {
          '0%, 100%': { transform: 'translateY(0%)' },
          '50%':       { transform: 'translateY(100%)' },
        },
        barFill: {
          '0%':   { width: '0%' },
          '100%': { width: 'var(--bar-width)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}