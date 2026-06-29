"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useUiStore } from "@/store/ui";
import { Sidebar } from "@/components/dashboard/sidebar";
import { TopBar } from "@/components/dashboard/topbar";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, initialize } = useAuthStore();
  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed);

  // Immersive routes (chapter lesson player) hide the topbar and main padding for full focus.
  const immersive = /^\/student\/courses\/[^/]+\/chapters\/[^/]+/.test(pathname ?? "");

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/auth/login");
      return;
    }
    if (user?.role !== "student") {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, user, router]);

  if (isLoading || !isAuthenticated || user?.role !== "student") {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-pulse">Chargement...</div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className={`flex-1 transition-[padding] duration-200 ${sidebarCollapsed ? "pl-16" : "pl-64"}`}>
        {!immersive && <TopBar />}
        <main className={immersive ? "" : "p-6"}>{children}</main>
      </div>
    </div>
  );
}
