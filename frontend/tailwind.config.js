/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Luxury Architectural Mineral Palette
        brand: {
          charcoal: '#2C3639',
          slate: '#3F4E4F',
          bronze: '#A27B5C',
          linen: '#DCD7C9',
          card: '#FFFFFF',
          'card-warm': '#F5F2EB',
          accent: '#A27B5C',
          'accent-hover': '#8e694b',
        },
        risk: {
          normal: '#2E7D32',
          elevated: '#A27B5C',
          extreme: '#C23B22',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
        display: ['Newsreader', 'Playfair Display', 'Georgia', 'serif'],
      },
      boxShadow: {
        'warm': '0 4px 20px -2px rgba(44, 54, 57, 0.08), 0 2px 6px -1px rgba(44, 54, 57, 0.04)',
        'warm-lg': '0 12px 32px -4px rgba(44, 54, 57, 0.12), 0 4px 12px -2px rgba(44, 54, 57, 0.06)',
        'bronze': '0 4px 14px 0 rgba(162, 123, 92, 0.35)',
      },
    },
  },
  plugins: [],
}
