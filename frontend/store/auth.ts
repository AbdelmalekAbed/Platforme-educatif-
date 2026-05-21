import { create } from "zustand";
import { api } from "@/services/api";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: string;
  }) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  initialize: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password) => {
    const tokens = await api.login(email, password);
    api.setToken(tokens.access_token);
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);

    const user = await api.getMe();
    set({
      user,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  register: async (data) => {
    await api.register(data);
  },

  logout: () => {
    api.setToken(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  loadUser: async () => {
    try {
      const user = await api.getMe();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      get().logout();
    }
  },

  initialize: () => {
    api.setOnAuthFailure(() => get().logout());
    const token = localStorage.getItem("access_token");
    const refresh = localStorage.getItem("refresh_token");
    if (token) {
      api.setToken(token);
      set({ accessToken: token, refreshToken: refresh });
      get().loadUser();
    } else {
      set({ isLoading: false });
    }
  },
}));
