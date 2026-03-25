/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        surface: {
          50: '#f8f7f4',
          100: '#f0efe8',
          200: '#e2e0d5',
          300: '#ccc9b8',
          800: '#2a2924',
          900: '#1c1b18',
          950: '#0f0e0c',
        },
        accent: {
          DEFAULT: '#e85d26',
          light: '#f4845f',
          dark: '#c44415',
        },
        correct: '#22c55e',
        incorrect: '#ef4444',
      },
      animation: {
        'slide-up': 'slideUp 0.4s ease-out',
        'fade-in': 'fadeIn 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'score-pop': 'scorePop 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 },
        },
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(232, 93, 38, 0.4)' },
          '50%': { boxShadow: '0 0 20px 4px rgba(232, 93, 38, 0.2)' },
        },
        scorePop: {
          '0%': { transform: 'scale(0.5)', opacity: 0 },
          '70%': { transform: 'scale(1.1)' },
          '100%': { transform: 'scale(1)', opacity: 1 },
        },
      },
    },
  },
  plugins: [],
};
