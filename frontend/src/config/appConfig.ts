/**
 * Application Configuration
 *
 * This deployment serves data and images directly from the bundled
 * public assets. Blob storage hooks were removed to keep the setup
 * minimal while we validate the frontend.
 */

// Backend API endpoint for SSE events (orchestrator API)
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://investmentresearchbackend.agreeablewave-76bf5979.eastus.azurecontainerapps.io';

/**
 * Resolve the URL for a JSON file under the public/data folder.
 */
export function getDataUrl(filename: string): string {
  return `/data/${filename}`;
}

/**
 * Resolve the URL for an image under the public/images folder.
 */
export function getImageUrl(filename: string): string {
  return `/images/${filename}`;
}

/**
 * Fetch a JSON payload from the bundled assets.
 */
export async function fetchBlobJson(filename: string): Promise<any> {
  const url = getDataUrl(filename);
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch ${filename}: ${response.statusText}`);
  }

  return response.json();
}
