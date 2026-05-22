import tailwindForms from '@tailwindcss/forms';
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: { extend: { colors: { primary: { 400: '#818cf8', 500: '#6366f1', 600: '#4f46e5' }, groq: { 500: '#f97316', 600: '#ea580c' }, gemini: { 500: '#4285f4', 600: '#3367d6' } } } },
  plugins: [tailwindForms],
};