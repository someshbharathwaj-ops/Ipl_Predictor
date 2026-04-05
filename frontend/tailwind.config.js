/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        night: "#07111f",
        panel: "#0f1a2d",
        accent: "#27f5d1",
        ember: "#ff7b54",
        gold: "#ffd166",
      },
      boxShadow: {
        neon: "0 0 30px rgba(39, 245, 209, 0.2)",
      },
    },
  },
  plugins: [],
};
