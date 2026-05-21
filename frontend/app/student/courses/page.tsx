"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { Course } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { BookOpen, GraduationCap, Search, ChevronRight, Layers } from "lucide-react";

const LEVEL_THEMES: Record<string, { gradient: string; accent: string; label: string }> = {
  "6eme": { gradient: "from-orange-500 to-red-500", accent: "text-orange-600", label: "6ème" },
  "5eme": { gradient: "from-pink-500 to-rose-500", accent: "text-pink-600", label: "5ème" },
  "4eme": { gradient: "from-emerald-500 to-teal-500", accent: "text-emerald-600", label: "4ème" },
  "3eme": { gradient: "from-amber-500 to-orange-600", accent: "text-amber-600", label: "3ème" },
};

const LEVEL_ORDER = ["6eme", "5eme", "4eme", "3eme"];

const ALL = "all";

export default function StudentCoursesPage() {
  const { isAuthenticated } = useAuthStore();
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState<string>(ALL);

  useEffect(() => {
    if (!isAuthenticated) return;
    api
      .getCourses()
      .then(setCourses)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  const availableLevels = useMemo(() => {
    const set = new Set<string>();
    courses.forEach((c) => {
      if (c.grade_level) set.add(c.grade_level);
    });
    return Array.from(set).sort((a, b) => {
      const ia = LEVEL_ORDER.indexOf(a);
      const ib = LEVEL_ORDER.indexOf(b);
      if (ia === -1 && ib === -1) return a.localeCompare(b);
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });
  }, [courses]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return courses.filter((c) => {
      if (levelFilter !== ALL && c.grade_level !== levelFilter) return false;
      if (!q) return true;
      return (
        c.title.toLowerCase().includes(q) ||
        (c.subject ?? "").toLowerCase().includes(q) ||
        (c.description ?? "").toLowerCase().includes(q)
      );
    });
  }, [courses, search, levelFilter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">Mes cours</h1>
          <p className="text-muted-foreground mt-1">
            Retrouvez tous les cours auxquels vous êtes inscrit
          </p>
        </div>
        <Link
          href="/student/catalog"
          className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
        >
          <GraduationCap className="h-4 w-4" />
          Explorer le catalogue
        </Link>
      </div>

      <div className="flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher un cours, une matière..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setLevelFilter(ALL)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              levelFilter === ALL
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-background hover:bg-accent"
            }`}
          >
            Tous
          </button>
          {availableLevels.map((lvl) => {
            const theme = LEVEL_THEMES[lvl];
            const active = levelFilter === lvl;
            return (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                  active
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-background hover:bg-accent"
                }`}
              >
                {theme?.label ?? lvl}
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-48 rounded-xl border bg-muted/30 animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <Layers className="h-12 w-12 mx-auto mb-3 text-muted-foreground/40" />
            {courses.length === 0 ? (
              <>
                <p className="text-muted-foreground">
                  Vous n&apos;êtes inscrit à aucun cours pour le moment.
                </p>
                <Link
                  href="/student/catalog"
                  className="inline-flex items-center gap-2 mt-4 text-sm font-medium text-primary hover:underline"
                >
                  <GraduationCap className="h-4 w-4" />
                  Découvrir les cours disponibles
                </Link>
              </>
            ) : (
              <p className="text-muted-foreground">
                Aucun cours ne correspond à votre recherche.
              </p>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((course) => {
            const theme = course.grade_level ? LEVEL_THEMES[course.grade_level] : undefined;
            return (
              <Link key={course.id} href={`/student/courses/${course.id}`}>
                <Card className="overflow-hidden cursor-pointer hover:shadow-lg transition-all hover:-translate-y-1 group h-full">
                  <div
                    className={`h-28 bg-gradient-to-br ${
                      theme?.gradient ?? "from-primary to-primary/60"
                    } relative flex items-center justify-center`}
                  >
                    <div className="absolute inset-0 bg-black/10 group-hover:bg-black/0 transition-colors" />
                    <div className="text-white text-center relative z-10 px-4">
                      <div className="text-xs uppercase tracking-wider opacity-90">
                        {course.subject ?? "Cours"}
                      </div>
                      <div className="text-2xl font-bold mt-1 line-clamp-2">
                        {theme?.label ?? course.grade_level ?? course.title}
                      </div>
                    </div>
                  </div>
                  <CardContent className="pt-4 space-y-2">
                    <h3 className="font-semibold text-base line-clamp-1 group-hover:text-primary transition-colors">
                      {course.title}
                    </h3>
                    {course.description && (
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {course.description}
                      </p>
                    )}
                    <div className="flex items-center justify-between pt-2">
                      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <BookOpen className="h-3.5 w-3.5" />
                        {course.is_active ? "Actif" : "Terminé"}
                      </span>
                      <span
                        className={`flex items-center gap-1 text-sm font-medium ${
                          theme?.accent ?? "text-primary"
                        }`}
                      >
                        Voir <ChevronRight className="h-3.5 w-3.5" />
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
