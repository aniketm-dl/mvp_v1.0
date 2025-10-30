/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Neon green and blue theme from darpanlabs.ai
        neon: {
          green: '#B8FF00',
          blue: '#00D4FF',
          darkbg: '#000000',
          surface: '#0A0A0A',
          surfacelight: '#1A1A1A',
          text: '#FFFFFF',
          textsecondary: '#A0A0B0',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #B8FF00, 0 0 10px #B8FF00, 0 0 15px #B8FF00' },
          '100%': { boxShadow: '0 0 10px #B8FF00, 0 0 20px #B8FF00, 0 0 30px #B8FF00' },
        }
      },
    },
  },
  plugins: [],
}
