"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useUiStore } from "@/store/ui";
import { Sidebar } from "@/components/dashboard/sidebar";
import { TopBar } from "@/components/dashboard/topbar";

export default function VendorLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, initialize } = useAuthStore();
  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed);

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/auth/login");
      return;
    }
    if (user?.role !== "vendor") {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, user, router]);

  if (isLoading || !isAuthenticated || user?.role !== "vendor") {
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
        <TopBar />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
