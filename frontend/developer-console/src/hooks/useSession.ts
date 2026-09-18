import { useSyncExternalStore } from "react";

import { getApiBaseUrl, getApiKey, subscribe } from "@/lib/auth/session";

/** Reactive view of the console session. Never exposes the raw key. */
export function useSession(): { connected: boolean; baseUrl: string } {
  const connected = useSyncExternalStore(
    subscribe,
    () => Boolean(getApiKey()),
    () => false,
  );
  const baseUrl = useSyncExternalStore(
    subscribe,
    () => getApiBaseUrl(),
    () => "",
  );
  return { connected, baseUrl };
}
