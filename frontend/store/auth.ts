import { create } from "zustand";
import { persist } from "zustand/middleware";
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

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
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
          // Erreur réseau / Neon endormie pendant une revalidation de fond :
          // on conserve l'utilisateur en cache plutôt que de le déconnecter.
          // Un vrai 401 est déjà géré par api.onAuthFailure -> logout().
          if (!get().user) get().logout();
          else set({ isLoading: false });
        }
      },

      initialize: () => {
        api.setOnAuthFailure(() => get().logout());
        // persist tourne en skipHydration : on hydrate manuellement ici (dans un
        // useEffect, donc côté client uniquement) pour éviter un mismatch
        // d'hydratation SSR. localStorage est synchrone -> l'état est appliqué
        // avant la ligne suivante.
        void useAuthStore.persist.rehydrate();

        const token = localStorage.getItem("access_token");
        const refresh = localStorage.getItem("refresh_token");
        if (token) {
          api.setToken(token);
          set({ accessToken: token, refreshToken: refresh });
        }

        if (get().user && token) {
          // user déjà connu (persisté au précédent chargement) : on peint l'UI
          // immédiatement et on revalide en arrière-plan, sans bloquer l'écran
          // derrière "Chargement..." le temps d'un aller-retour vers Neon.
          set({ isAuthenticated: true, isLoading: false });
          void get().loadUser();
        } else if (token) {
          // Token présent mais pas de user persisté : on doit attendre getMe.
          void get().loadUser();
        } else {
          set({ isLoading: false, isAuthenticated: false, user: null });
        }
      },
    }),
    {
      name: "auth-store",
      // On ne persiste que l'identité (les tokens vivent dans leurs propres clés
      // localStorage, gérées par le client API).
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      // Hydratation manuelle dans initialize() -> pas de mismatch SSR/client.
      skipHydration: true,
    }
  )
);
