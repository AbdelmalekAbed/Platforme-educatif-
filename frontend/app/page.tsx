"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";

export default function HomePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/auth/login");
      return;
    }
    // Redirect based on role
    switch (user?.role) {
      case "admin":
        router.replace("/admin");
        break;
      case "teacher":
        router.replace("/teacher");
        break;
      case "vendor":
        router.replace("/vendor");
        break;
      default:
        router.replace("/student");
    }
  }, [isAuthenticated, isLoading, user, router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="animate-pulse text-lg">Chargement...</div>
    </div>
  );
}
