"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { TeacherDashboard } from "@/types";
import { StatsCard } from "@/components/dashboard/stats-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BookOpen,
  Video,
  Users,
  ClipboardList,
  Eye,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const LEVEL_THEMES: Record<string, { gradient: string; label: string }> = {
  "6eme": { gradient: "from-orange-500 to-red-500", label: "6ème" },
  "5eme": { gradient: "from-pink-500 to-rose-500", label: "5ème" },
  "4eme": { gradient: "from-emerald-500 to-teal-500", label: "4ème" },
  "3eme": { gradient: "from-amber-500 to-orange-600", label: "3ème" },
};

const DEFAULT_THEME = { gradient: "from-blue-500 to-indigo-600", label: "—" };

export default function TeacherDashboardPage() {
  const { isAuthenticated } = useAuthStore();
  const [data, setData] = useState<TeacherDashboard | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    api.getTeacherDashboard().then(setData).catch(console.error);
  }, [isAuthenticated]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Espace Professeur</h1>
          <p className="text-muted-foreground">Animez vos cours et accompagnez vos élèves</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Mes Cours"
          value={data?.total_courses ?? "—"}
          icon={BookOpen}
        />
        <StatsCard
          title="Sessions Prévues"
          value={data?.upcoming_sessions ?? "—"}
          icon={Video}
        />
        <StatsCard
          title="Élèves Inscrits"
          value={data?.total_students ?? "—"}
          icon={Users}
        />
        <StatsCard
          title="Devoirs Actifs"
          value={data?.active_homework ?? "—"}
          icon={ClipboardList}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Mes Cours</CardTitle>
        </CardHeader>
        <CardContent>
          {!data ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-56 rounded-xl border bg-muted/30 animate-pulse" />
              ))}
            </div>
          ) : data.courses.length === 0 ? (
            <p className="text-muted-foreground">
              Aucun cours ne vous est assigné pour le moment. Contactez l&apos;administration.
            </p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {data.courses.map((course) => {
                const theme = LEVEL_THEMES[course.grade_level ?? ""] ?? DEFAULT_THEME;
                const isIncomplete = course.chapter_count === 0;
                return (
                  <Card
                    key={course.id}
                    className="overflow-hidden hover:shadow-lg transition-all group"
                  >
                    <div
                      className={`h-24 bg-gradient-to-br ${theme.gradient} relative flex items-center justify-center`}
                    >
                      <div className="text-white text-center">
                        <div className="text-3xl font-bold">{theme.label}</div>
                        <div className="text-[10px] uppercase tracking-wider opacity-90">
                          {course.subject ?? "Cours"}
                        </div>
                      </div>
                      {!course.is_active && (
                        <div className="absolute top-2 left-2 rounded-full bg-yellow-500 text-white text-[10px] font-semibold px-2 py-0.5">
                          Inactif
                        </div>
                      )}
                      {isIncomplete && (
                        <div
                          className="absolute top-2 right-2 flex items-center gap-1 rounded-full bg-yellow-500/90 text-white text-[10px] font-semibold px-2 py-0.5"
                          title="Ce cours n'a encore aucun chapitre. L'admin doit ajouter le contenu."
                        >
                          <AlertCircle className="h-3 w-3" />
                          Aucun chapitre
                        </div>
                      )}
                    </div>
                    <CardContent className="pt-4 space-y-3">
                      <div>
                        <h3 className="font-semibold line-clamp-2 min-h-[3rem]">
                          {course.title}
                        </h3>
                        <p className="text-xs text-muted-foreground line-clamp-1 mt-1">
                          {course.description || "Pas de description"}
                        </p>
                      </div>

                      <div className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-1 text-muted-foreground">
                          <BookOpen className="h-3 w-3" />
                          {course.chapter_count}{" "}
                          {course.chapter_count > 1 ? "chapitres" : "chapitre"}
                        </span>
                        <span className="flex items-center gap-1 text-muted-foreground">
                          <Users className="h-3 w-3" />
                          {course.student_count}{" "}
                          {course.student_count > 1 ? "élèves" : "élève"}
                        </span>
                      </div>

                      {course.avg_progress !== null && (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground">
                              Progression moyenne
                            </span>
                            <span className="font-medium">
                              {course.avg_progress}%
                            </span>
                          </div>
                          <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                            <div
                              className={`h-full rounded-full bg-gradient-to-r ${theme.gradient}`}
                              style={{ width: `${course.avg_progress}%` }}
                            />
                          </div>
                        </div>
                      )}

                      <Link href={`/teacher/courses/${course.id}/content`}>
                        <Button size="sm" className="w-full">
                          <Eye className="h-4 w-4 mr-1" /> Voir contenu
                        </Button>
                      </Link>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
