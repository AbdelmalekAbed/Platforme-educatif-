"use client";

import { create } from "zustand";
import { api } from "@/services/api";
import type { PublicSettings } from "@/types";

interface PlatformState {
  /** Cached public settings (name, description, etc.). null until loaded. */
  settings: PublicSettings | null;
  /** A single in-flight promise so concurrent useEffects don't double-fetch. */
  loadPromise: Promise<PublicSettings | null> | null;
  /** Triggers a fetch if not already cached/in-flight. Idempotent. */
  ensureLoaded: () => Promise<PublicSettings | null>;
  /** Forces a re-fetch (e.g. after the admin saves the platform section). */
  refresh: () => Promise<PublicSettings | null>;
}

const DEFAULT_NAME = "EdTech Platform";

export const usePlatformStore = create<PlatformState>((set, get) => ({
  settings: null,
  loadPromise: null,
  ensureLoaded: () => {
    const state = get();
    if (state.settings) return Promise.resolve(state.settings);
    if (state.loadPromise) return state.loadPromise;
    const promise = api
      .getPublicSettings()
      .then((s) => {
        set({ settings: s, loadPromise: null });
        if (typeof document !== "undefined") {
          document.title = s.name || DEFAULT_NAME;
        }
        return s;
      })
      .catch(() => {
        // Network/auth errors shouldn't block the UI — fall back to defaults.
        set({ loadPromise: null });
        return null;
      });
    set({ loadPromise: promise });
    return promise;
  },
  refresh: () => {
    set({ settings: null, loadPromise: null });
    return get().ensureLoaded();
  },
}));
