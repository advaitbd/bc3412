// frontend/tailwind.config.js

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html", // Checks the main HTML file
    "./src/**/*.{js,ts,jsx,tsx}", // Checks all JS, TS, JSX, TSX files in src/**
  ],
  theme: {
    extend: {}, // You can add customizations here later
  },
  plugins: [],
};
