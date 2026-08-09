import axios from 'axios';

export const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();

export const apiClient = axios.create({
  baseURL: apiBaseUrl || undefined,
  timeout: Number(import.meta.env.VITE_API_TIMEOUT_MS) || 5000,
  headers: { 'Content-Type': 'application/json' },
});
