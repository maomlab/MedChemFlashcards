import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development the SPA runs on :5173 and proxies API calls to the
// FastAPI server on :8000. In production the built assets can be served
// statically (optionally by FastAPI itself).
//
// `base` defaults to "/" and is overridden by VITE_BASE for subpath deploys
// (e.g. a GitHub project page at https://<user>.github.io/<repo>/).
export default defineConfig({
  base: process.env.VITE_BASE || "/",
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
