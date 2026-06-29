"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { CourseListItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, BookOpen, Play, CheckCircle2, Loader2 } from "lucide-react";

const PAGE_SIZE = 4;

const LEVEL_LABELS: Record<string, string> = {
  "6eme": "6ème",
  "5eme": "5ème",
  "4eme": "4ème",
  "3eme": "3ème",
};

export default function LevelCoursesPage() {
  const params = useParams<{ level: string }>();
  const level = params.level;
  const { isAuthenticated } = useAuthStore();
  const [items, setItems] = useState<CourseListItem[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [levelProgress, setLevelProgress] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [togglingKnown, setTogglingKnown] = useState<Record<string, boolean>>({});

  const loadInitial = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getCoursesByLevel(level, 0, PAGE_SIZE);
      setItems(res.items);
      setHasMore(res.has_more);
      setTotal(res.total);
      setLevelProgress(res.level_progress_percent ?? 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [level]);

  const refreshLevelProgress = useCallback(async () => {
    try {
      const res = await api.getCoursesByLevel(level, 0, items.length || PAGE_SIZE);
      setLevelProgress(res.level_progress_percent ?? 0);
      // Sync individual course progress too (a single known toggle changes others' aggregated state).
      setItems((prev) =>
        prev.map((c) => {
          const fresh = res.items.find((x) => x.id === c.id);
          return fresh ?? c;
        })
      );
    } catch (err) {
      console.error(err);
    }
  }, [level, items.length]);

  const toggleKnown = async (course: CourseListItem) => {
    const id = course.id;
    setTogglingKnown((s) => ({ ...s, [id]: true }));
    // Optimistic update
    const willKnow = !course.is_known;
    setItems((prev) =>
      prev.map((c) =>
        c.id === id
          ? { ...c, is_known: willKnow, progress_percent: willKnow ? 100 : c.progress_percent }
          : c
      )
    );
    try {
      if (willKnow) await api.markCourseKnown(id);
      else await api.unmarkCourseKnown(id);
      await refreshLevelProgress();
    } catch (err) {
      console.error(err);
      // Revert on error
      setItems((prev) =>
        prev.map((c) =>
          c.id === id
            ? { ...c, is_known: course.is_known, progress_percent: course.progress_percent }
            : c
        )
      );
    } finally {
      setTogglingKnown((s) => ({ ...s, [id]: false }));
    }
  };

  useEffect(() => {
    if (!isAuthenticated || !level) return;
    loadInitial();
  }, [isAuthenticated, level, loadInitial]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const res = await api.getCoursesByLevel(level, items.length, PAGE_SIZE);
      setItems((prev) => [...prev, ...res.items]);
      setHasMore(res.has_more);
      setLevelProgress(res.level_progress_percent ?? 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/student/catalog">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" /> Retour au catalogue
          </Button>
        </Link>
      </div>

      <div className="rounded-xl bg-gradient-to-r from-primary/10 via-primary/5 to-background border p-6">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div className="flex items-end gap-4">
            <div className="rounded-xl bg-primary text-primary-foreground p-4 text-3xl font-bold">
              {LEVEL_LABELS[level] ?? level}
            </div>
            <div>
              <h1 className="text-2xl font-bold">Mathématiques — {LEVEL_LABELS[level] ?? level}</h1>
              <p className="text-muted-foreground text-sm">
                {total} {total > 1 ? "cours disponibles" : "cours disponible"}
              </p>
            </div>
          </div>
          {total > 0 && (
            <div className="min-w-[220px]">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-semibold text-muted-foreground uppercase tracking-wider">
                  Progression du niveau
                </span>
                <span className="font-bold text-primary">{Math.round(levelProgress)}%</span>
              </div>
              <div className="h-2 rounded-full bg-secondary overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary to-primary/70 rounded-full transition-all"
                  style={{ width: `${levelProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-64 rounded-xl border bg-muted/30 animate-pulse"
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <BookOpen className="h-12 w-12 mb-4 opacity-30" />
            <p>Aucun cours disponible pour ce niveau pour le moment.</p>
            <p className="text-sm mt-1">Revenez bientôt — le contenu est en préparation.</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {items.map((course) => {
              const started = (course.progress_percent ?? 0) > 0;
              const completed = (course.progress_percent ?? 0) >= 100;
              return (
                <Card
                  key={course.id}
                  className="overflow-hidden hover:shadow-lg transition-all hover:-translate-y-1 group"
                >
                  <div className="h-32 bg-gradient-to-br from-blue-500 to-indigo-600 relative">
                    {course.thumbnail_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={course.thumbnail_url}
                        alt={course.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center text-white">
                        <BookOpen className="h-12 w-12 opacity-50" />
                      </div>
                    )}
                    {completed && (
                      <div className="absolute top-2 right-2 bg-green-500 text-white rounded-full p-1">
                        <CheckCircle2 className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                  <CardContent className="pt-4 space-y-2">
                    {/* Header block: title + progress sit tightly together. */}
                    <div className="space-y-2">
                      <h3 className="font-semibold line-clamp-2 min-h-[3rem]">
                        {course.title}
                      </h3>

                      {/* Progress slot — always rendered for layout consistency.
                          Adapts its label/style to: not-started / in-progress / completed. */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span
                            className={
                              completed
                                ? "text-green-600 font-medium"
                                : started
                                ? "text-muted-foreground"
                                : "text-muted-foreground italic"
                            }
                          >
                            {completed
                              ? "Cours terminé"
                              : started
                              ? "Progression"
                              : "Pas encore commencé"}
                          </span>
                          {started && (
                            <span className="font-medium tabular-nums">
                              {Math.round(course.progress_percent)}%
                            </span>
                          )}
                        </div>
                        <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              completed ? "bg-green-500" : "bg-primary"
                            }`}
                            style={{ width: `${started ? course.progress_percent : 0}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Extra top margin so the progress bar isn't squashed against the button. */}
                    <Link href={`/student/courses/${course.id}`} className="block !mt-6">
                      <Button className="w-full" variant={started ? "default" : "outline"}>
                        <Play className="h-4 w-4 mr-2" />
                        {completed
                          ? "Revoir"
                          : started
                          ? "Continuer à apprendre"
                          : "Commencer à apprendre"}
                      </Button>
                    </Link>

                    <label
                      className={`flex items-center gap-2 text-xs cursor-pointer select-none px-2 py-1.5 rounded-md transition-colors ${
                        course.is_known
                          ? "bg-green-50 text-green-800 hover:bg-green-100"
                          : "text-muted-foreground hover:bg-accent"
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="h-3.5 w-3.5 accent-green-600"
                        checked={!!course.is_known}
                        disabled={!!togglingKnown[course.id]}
                        onChange={() => toggleKnown(course)}
                      />
                      <span className="flex-1">Je connais déjà ce cours</span>
                      {togglingKnown[course.id] && (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      )}
                    </label>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {hasMore && (
            <div className="flex justify-center pt-4">
              <Button
                variant="outline"
                onClick={loadMore}
                disabled={loadingMore}
                size="lg"
              >
                {loadingMore ? "Chargement..." : "Afficher plus"}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
