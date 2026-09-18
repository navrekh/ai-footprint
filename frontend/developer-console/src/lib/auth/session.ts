/**
 * Console credential storage (ADR-012).
 *
 * The developer API key is held in sessionStorage only — never
 * localStorage, never cookies, never the URL, never a log line.
 * sessionStorage is not an XSS defence; it only bounds the lifetime of
 * the credential to the browser tab session.
 */

const KEY_STORAGE_KEY = "aifootprint.console.apiKey";
const BASE_URL_STORAGE_KEY = "aifootprint.console.apiBaseUrl";

export const DEFAULT_API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || "";

type Listener = () => void;
const listeners = new Set<Listener>();

function emit(): void {
  listeners.forEach((listener) => listener());
}

function safeSession(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export function getApiKey(): string | null {
  return safeSession()?.getItem(KEY_STORAGE_KEY) ?? null;
}

export function getApiBaseUrl(): string {
  const stored = safeSession()?.getItem(BASE_URL_STORAGE_KEY);
  return normalizeBaseUrl(stored || DEFAULT_API_BASE_URL);
}

export function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, "");
}

export function setSession(baseUrl: string, apiKey: string): void {
  const storage = safeSession();
  if (!storage) return;
  storage.setItem(BASE_URL_STORAGE_KEY, normalizeBaseUrl(baseUrl));
  storage.setItem(KEY_STORAGE_KEY, apiKey);
  emit();
}

export function clearSession(): void {
  const storage = safeSession();
  if (!storage) return;
  storage.removeItem(KEY_STORAGE_KEY);
  storage.removeItem(BASE_URL_STORAGE_KEY);
  emit();
}

export function isConnected(): boolean {
  return Boolean(getApiKey());
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
