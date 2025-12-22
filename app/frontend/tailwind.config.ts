import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        medical: {
          blue: {
            DEFAULT: '#0284c7',
            light: '#0ea5e9',
            dark: '#0369a1',
          },
          teal: {
            DEFAULT: '#0891b2',
            light: '#06b6d4',
            dark: '#0e7490',
          },
          green: {
            DEFAULT: '#059669',
            light: '#10b981',
          },
        },
      },
    },
  },
  plugins: [],
};

export default config;

