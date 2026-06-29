"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { api } from "@/services/api";
import type { AdminCourse, PlatformStats, User } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart3,
  Users,
  DollarSign,
  GraduationCap,
  BookOpen,
  UserCheck,
  TrendingUp,
  Filter,
  Download,
} from "lucide-react";

type Range = "7d" | "30d" | "90d" | "all";

const RANGES: { key: Range; label: string; days: number | null }[] = [
  { key: "7d", label: "7 jours", days: 7 },
  { key: "30d", label: "30 jours", days: 30 },
  { key: "90d", label: "90 jours", days: 90 },
  { key: "all", label: "Tout", days: null },
];

const ROLE_COLORS: Record<string, string> = {
  student: "#7c3aed",
  teacher: "#10b981",
  admin: "#0ea5e9",
  vendor: "#f59e0b",
};

const ROLE_LABEL: Record<string, string> = {
  student: "Élèves",
  teacher: "Professeurs",
  admin: "Admins",
  vendor: "Vendeurs",
};

const BAR_COLORS = ["#7c3aed", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#6366f1"];

export default function AdminAnalyticsPage() {
  const [range, setRange] = useState<Range>("30d");
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [users, setUsers] = useState<User[] | null>(null);
  const [courses, setCourses] = useState<AdminCourse[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getStats(), api.getUsers(undefined, 1000), api.getAdminCourses()])
      .then(([s, u, c]) => {
        if (cancelled) return;
        setStats(s);
        setUsers(u);
        setCourses(c);
      })
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : "Erreur"));
    return () => {
      cancelled = true;
    };
  }, []);

  const loading = !stats || !users || !courses;

  // Filter users by selected range (signups within last N days).
  const filteredUsers = useMemo(() => {
    if (!users) return [];
    const cfg = RANGES.find((r) => r.key === range)!;
    if (cfg.days === null) return users;
    const cutoff = Date.now() - cfg.days * 86400_000;
    return users.filter((u) => new Date(u.created_at).getTime() >= cutoff);
  }, [users, range]);

  // Signups per day series — empty days included so the line is continuous.
  const signupsSeries = useMemo(() => {
    if (!users) return [];
    const cfg = RANGES.find((r) => r.key === range)!;
    const days = cfg.days ?? Math.max(30, daysSpan(users));
    const buckets = new Map<string, { eleves: number; profs: number }>();
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(today.getDate() - i);
      buckets.set(dateKey(d), { eleves: 0, profs: 0 });
    }
    for (const u of users) {
      const created = new Date(u.created_at);
      created.setHours(0, 0, 0, 0);
      const key = dateKey(created);
      const slot = buckets.get(key);
      if (!slot) continue;
      if (u.role === "student") slot.eleves += 1;
      else if (u.role === "teacher") slot.profs += 1;
    }
    return Array.from(buckets.entries()).map(([k, v]) => ({
      day: formatShortDate(k),
      ...v,
    }));
  }, [users, range]);

  // Role distribution (donut).
  const roleDistribution = useMemo(() => {
    if (!users) return [];
    const counts = new Map<string, number>();
    for (const u of users) counts.set(u.role, (counts.get(u.role) ?? 0) + 1);
    return Array.from(counts.entries()).map(([role, value]) => ({
      name: ROLE_LABEL[role] ?? role,
      role,
      value,
    }));
  }, [users]);

  // Courses grouped by subject (bar).
  const coursesBySubject = useMemo(() => {
    if (!courses) return [];
    const counts = new Map<string, number>();
    for (const c of courses) {
      const k = c.subject?.trim() || "Sans matière";
      counts.set(k, (counts.get(k) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([name, cours]) => ({ name, cours }))
      .sort((a, b) => b.cours - a.cours);
  }, [courses]);

  // Courses grouped by grade level (bar).
  const coursesByLevel = useMemo(() => {
    if (!courses) return [];
    const counts = new Map<string, number>();
    for (const c of courses) {
      const k = c.grade_level?.trim() || "Sans niveau";
      counts.set(k, (counts.get(k) ?? 0) + 1);
    }
    return Array.from(counts.entries())
      .map(([name, cours]) => ({ name, cours }))
      .sort((a, b) => b.cours - a.cours);
  }, [courses]);

  // Top teachers by number of courses owned.
  const topTeachers = useMemo(() => {
    if (!courses) return [];
    const counts = new Map<string, { name: string; cours: number; actifs: number }>();
    for (const c of courses) {
      const entry = counts.get(c.teacher_id) ?? {
        name: c.teacher_name,
        cours: 0,
        actifs: 0,
      };
      entry.cours += 1;
      if (c.is_active) entry.actifs += 1;
      counts.set(c.teacher_id, entry);
    }
    return Array.from(counts.values())
      .sort((a, b) => b.cours - a.cours)
      .slice(0, 5);
  }, [courses]);

  if (error) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-red-600">{error}</CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <BarChart3 className="h-8 w-8" /> Analytiques
        </h1>
        <div className="animate-pulse text-muted-foreground">Chargement des données...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <BarChart3 className="h-8 w-8" /> Analytiques
          </h1>
          <p className="text-muted-foreground">
            Vue d&apos;ensemble de votre plateforme — données réelles.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-lg border bg-card p-1">
            <Filter className="h-4 w-4 ml-2 text-muted-foreground" />
            {RANGES.map((r) => (
              <button
                key={r.key}
                onClick={() => setRange(r.key)}
                className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                  range === r.key
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
          <Button variant="outline" size="sm" disabled>
            <Download className="h-4 w-4 mr-2" /> Exporter
          </Button>
        </div>
      </div>

      {/* KPI cards — global totals from /admin/stats. */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <Kpi label="Utilisateurs" value={stats.total_users} icon={Users} accent="text-violet-600" />
        <Kpi
          label="Élèves"
          value={stats.total_students}
          icon={GraduationCap}
          accent="text-sky-600"
        />
        <Kpi
          label="Professeurs"
          value={stats.total_teachers}
          icon={UserCheck}
          accent="text-emerald-600"
        />
        <Kpi label="Cours" value={stats.total_courses} icon={BookOpen} accent="text-amber-600" />
        <Kpi
          label="Inscriptions"
          value={stats.total_enrollments}
          icon={TrendingUp}
          accent="text-pink-600"
        />
        <Kpi
          label="Revenus"
          value={`${formatNumber(stats.total_revenue)} €`}
          icon={DollarSign}
          accent="text-rose-600"
        />
      </div>

      {/* Signups timeline + role distribution */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Inscriptions sur la période</CardTitle>
            <p className="text-xs text-muted-foreground">
              {filteredUsers.length} compte{filteredUsers.length > 1 ? "s" : ""} créé
              {filteredUsers.length > 1 ? "s" : ""} sur les{" "}
              {RANGES.find((r) => r.key === range)!.label.toLowerCase()}.
            </p>
          </CardHeader>
          <CardContent>
            {users.length === 0 ? (
              <EmptyChart message="Aucun utilisateur enregistré pour l'instant." />
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={signupsSeries} margin={{ top: 5, right: 16, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      dataKey="day"
                      tick={{ fontSize: 11 }}
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 11 }}
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Line
                      type="monotone"
                      dataKey="eleves"
                      name="Élèves"
                      stroke="#7c3aed"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="profs"
                      name="Professeurs"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Répartition par rôle</CardTitle>
            <p className="text-xs text-muted-foreground">Tous les comptes confondus.</p>
          </CardHeader>
          <CardContent>
            {roleDistribution.length === 0 ? (
              <EmptyChart message="Aucun utilisateur." />
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={roleDistribution}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                    >
                      {roleDistribution.map((entry, i) => (
                        <Cell
                          key={entry.role}
                          fill={ROLE_COLORS[entry.role] ?? BAR_COLORS[i % BAR_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Courses by subject + by level */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cours par matière</CardTitle>
          </CardHeader>
          <CardContent>
            {coursesBySubject.length === 0 ? (
              <EmptyChart message="Aucun cours créé pour l'instant." />
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={coursesBySubject} layout="vertical" margin={{ left: 24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      type="number"
                      allowDecimals={false}
                      tick={{ fontSize: 11 }}
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      tick={{ fontSize: 11 }}
                      stroke="hsl(var(--muted-foreground))"
                      width={120}
                    />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="cours" fill="#0ea5e9" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cours par niveau</CardTitle>
          </CardHeader>
          <CardContent>
            {coursesByLevel.length === 0 ? (
              <EmptyChart message="Aucun cours créé pour l'instant." />
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={coursesByLevel}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 11 }}
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 11 }}
                      stroke="hsl(var(--muted-foreground))"
                    />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="cours" fill="#10b981" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top teachers */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Top professeurs (par nombre de cours)</CardTitle>
        </CardHeader>
        <CardContent>
          {topTeachers.length === 0 ? (
            <EmptyChart message="Aucun cours créé par un professeur pour l'instant." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-3 font-medium">Professeur</th>
                    <th className="pb-3 font-medium text-right">Cours</th>
                    <th className="pb-3 font-medium text-right">Cours actifs</th>
                  </tr>
                </thead>
                <tbody>
                  {topTeachers.map((t, i) => (
                    <tr key={t.name + i} className="border-b last:border-0">
                      <td className="py-3 font-medium">
                        <span className="text-muted-foreground mr-2">#{i + 1}</span>
                        {t.name}
                      </td>
                      <td className="py-3 text-right tabular-nums">{t.cours}</td>
                      <td className="py-3 text-right tabular-nums">{t.actifs}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-center pt-2">
        Données réelles tirées de <code>/api/v1/admin/stats</code>,{" "}
        <code>/api/v1/admin/users</code> et <code>/api/v1/admin/courses</code>. Revenus mensuels, taux
        de complétion et activité hebdomadaire seront ajoutés une fois les endpoints backend
        correspondants en place.
      </p>
    </div>
  );
}

// ---------- helpers ----------

function dateKey(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function formatShortDate(iso: string): string {
  const [, m, d] = iso.split("-");
  return `${d}/${m}`;
}

function formatNumber(n: number): string {
  return n.toLocaleString("fr-FR", { maximumFractionDigits: 0 });
}

function daysSpan(users: User[]): number {
  if (users.length === 0) return 30;
  const oldest = users.reduce(
    (min, u) => Math.min(min, new Date(u.created_at).getTime()),
    Date.now()
  );
  return Math.max(7, Math.ceil((Date.now() - oldest) / 86400_000));
}

const tooltipStyle: React.CSSProperties = {
  background: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: 8,
  fontSize: 12,
};

function Kpi({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold mt-1 tabular-nums truncate">
              {typeof value === "number" ? formatNumber(value) : value}
            </p>
          </div>
          <div className={`rounded-full bg-muted/60 p-2 shrink-0 ${accent}`}>
            <Icon className="h-4 w-4" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="h-72 flex items-center justify-center text-sm text-muted-foreground text-center px-4">
      {message}
    </div>
  );
}
