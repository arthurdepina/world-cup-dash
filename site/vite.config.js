import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages serves from https://<user>.github.io/<repo>/, so we need a
// leading base path in production. The workflow sets VITE_BASE at build time.
export default defineConfig(({ mode }) => ({
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  build: { outDir: "dist", sourcemap: false },
}));
