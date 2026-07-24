import axios from "axios";
 
// Base URL comes from an environment variable, never hardcoded.
// Vite only exposes env vars prefixed with VITE_ to client code,
// and they must be read via import.meta.env (not process.env).
//
// Set it in a .env or .env.local file at your project root:
//   VITE_API_BASE_URL=https://your-backend-host
//
// On Google Cloud Shell specifically: the backend's web-preview URL
// changes every session (e.g. https://8000-cs-xxxxx-default.cs.cloudshell.dev),
// so update .env.local with the fresh URL each time you restart Cloud Shell,
// then restart `npm run dev` (Vite only reads .env files at startup).
const baseURL = import.meta.env.VITE_API_BASE_URL;
 
if (!baseURL) {
  // Fail loudly in dev rather than silently hitting the wrong host.
  console.warn(
    "VITE_API_BASE_URL is not set — API calls will fail. Add it to .env.local."
  );
}
 
const api = axios.create({
  baseURL,
});
 
export default api;