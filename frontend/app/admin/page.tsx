"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import type { PlatformStats } from "@/types";
import { StatsCard } from "@/components/dashboard/stats-card";
import { Users, BookOpen, GraduationCap, DollarSign, UserCheck, TrendingUp } from "lucide-react";

export default function AdminDashboard() {
  const [stats, setStats] = useState<PlatformStats | null>(null);

  useEffect(() => {
    api.getStats().then(setStats).catch(console.error);
  }, []);

  if (!stats) {
    return <div className="animate-pulse">Chargement des statistiques...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Tableau de bord Admin</h1>
        <p className="text-muted-foreground">Vue d&apos;ensemble de la plateforme</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <StatsCard
          title="Total Utilisateurs"
          value={stats.total_users}
          icon={Users}
          description="Tous les utilisateurs enregistrés"
        />
        <StatsCard
          title="Élèves"
          value={stats.total_students}
          icon={GraduationCap}
          description="Élèves actifs"
        />
        <StatsCard
          title="Professeurs"
          value={stats.total_teachers}
          icon={UserCheck}
          description="Professeurs actifs"
        />
        <StatsCard
          title="Cours"
          value={stats.total_courses}
          icon={BookOpen}
          description="Cours disponibles"
        />
        <StatsCard
          title="Inscriptions"
          value={stats.total_enrollments}
          icon={TrendingUp}
          description="Inscriptions actives"
        />
        <StatsCard
          title="Revenus"
          value={`${Math.round(stats.total_revenue)} €`}
          icon={DollarSign}
          description="Revenus totaux"
        />
      </div>
    </div>
  );
}
