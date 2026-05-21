"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { LevelInfo } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { GraduationCap, BookOpen } from "lucide-react";

const LEVEL_THEMES: Record<string, { gradient: string; accent: string }> = {
  "6eme": { gradient: "from-orange-500 to-red-500", accent: "text-orange-600" },
  "5eme": { gradient: "from-pink-500 to-rose-500", accent: "text-pink-600" },
  "4eme": { gradient: "from-emerald-500 to-teal-500", accent: "text-emerald-600" },
  "3eme": { gradient: "from-amber-500 to-orange-600", accent: "text-amber-600" },
};

interface LevelCatalogProps {
  title: string;
  subtitle: string;
  /** Base path for level links; the level code is appended (e.g. /teacher/courses/level → /teacher/courses/level/6eme). */
  levelHrefBase: string;
  /** Optional action slot rendered next to the title (e.g. "+ Nouveau Cours"). */
  action?: React.ReactNode;
  /** Optional footer banner. Defaults to the program description for student-facing catalogs. */
  footer?: React.ReactNode;
}

export function LevelCatalog({
  title,
  subtitle,
  levelHrefBase,
  action,
  footer,
}: LevelCatalogProps) {
  const { isAuthenticated } = useAuthStore();
  const [levels, setLevels] = useState<LevelInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) return;
    api
      .getLevels()
      .then(setLevels)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">{title}</h1>
          <p className="text-muted-foreground mt-1">{subtitle}</p>
        </div>
        {action}
      </div>

      <section>
        <div className="flex items-center gap-2 mb-4">
          <div className="rounded-full bg-primary/10 px-4 py-1.5 text-sm font-semibold text-primary">
            Collège
          </div>
        </div>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-48 rounded-xl border bg-muted/30 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {levels.map((level) => {
              const theme = LEVEL_THEMES[level.code] ?? LEVEL_THEMES["3eme"];
              return (
                <Link
                  key={level.code}
                  href={`${levelHrefBase}/${level.code}`}
                >
                  <Card className="overflow-hidden cursor-pointer hover:shadow-lg transition-all hover:-translate-y-1 group h-full">
                    <div
                      className={`h-32 bg-gradient-to-br ${theme.gradient} relative flex items-center justify-center`}
                    >
                      <div className="absolute inset-0 bg-black/10 group-hover:bg-black/0 transition-colors" />
                      <div className="text-white text-center relative z-10">
                        <div className="text-5xl font-bold">{level.label}</div>
                        <div className="text-xs uppercase tracking-wider mt-1 opacity-90">
                          Mathématiques
                        </div>
                      </div>
                    </div>
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <BookOpen className="h-4 w-4" />
                          <span>
                            {level.course_count}{" "}
                            {level.course_count > 1 ? "cours" : "cours"}
                          </span>
                        </div>
                        <span className={`text-sm font-medium ${theme.accent}`}>
                          Voir →
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </section>

      {footer ?? (
        <section className="mt-12 rounded-xl border bg-gradient-to-br from-primary/5 via-background to-primary/5 p-8">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-primary/10 p-3">
              <GraduationCap className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">
                L&apos;intégralité du programme de mathématiques
              </h2>
              <p className="text-muted-foreground text-sm mt-1">
                Tous les chapitres du programme officiel — fiches, exercices,
                vidéos et quiz dans chaque chapitre.
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
