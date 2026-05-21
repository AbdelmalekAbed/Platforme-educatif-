import { create } from "zustand";

const STORAGE_KEY = "sidebar-collapsed";

const readInitial = (): boolean => {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(STORAGE_KEY) === "1";
};

interface UiState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useUiStore = create<UiState>((set, get) => ({
  sidebarCollapsed: readInitial(),
  toggleSidebar: () => {
    const next = !get().sidebarCollapsed;
    set({ sidebarCollapsed: next });
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
    }
  },
  setSidebarCollapsed: (collapsed) => {
    set({ sidebarCollapsed: collapsed });
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    }
  },
}));
