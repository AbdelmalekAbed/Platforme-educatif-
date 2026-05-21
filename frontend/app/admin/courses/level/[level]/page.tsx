"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { CourseListItem } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  ArrowLeft,
  BookOpen,
  Layers,
  ToggleLeft,
  ToggleRight,
  Trash2,
} from "lucide-react";

const PAGE_SIZE = 12;

const LEVEL_LABELS: Record<string, string> = {
  "6eme": "6ème",
  "5eme": "5ème",
  "4eme": "4ème",
  "3eme": "3ème",
};

export default function AdminLevelCoursesPage() {
  const params = useParams<{ level: string }>();
  const level = params.level;
  const { isAuthenticated } = useAuthStore();
  const [items, setItems] = useState<CourseListItem[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const loadInitial = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getCoursesByLevel(level, 0, PAGE_SIZE);
      setItems(res.items);
      setHasMore(res.has_more);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [level]);

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
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMore(false);
    }
  };

  const handleToggle = async (id: string) => {
    try {
      const res = await api.adminToggleCourse(id);
      setItems((prev) =>
        prev.map((c) => (c.id === id ? { ...c, is_active: res.is_active } : c))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Supprimer ce cours ? Cette action est irréversible.")) return;
    try {
      await api.adminDeleteCourse(id);
      setItems((prev) => prev.filter((c) => c.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/admin/courses">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" /> Retour au catalogue
          </Button>
        </Link>
      </div>

      <div className="rounded-xl bg-gradient-to-r from-primary/10 via-primary/5 to-background border p-6">
        <div className="flex items-end gap-4">
          <div className="rounded-xl bg-primary text-primary-foreground p-4 text-3xl font-bold">
            {LEVEL_LABELS[level] ?? level}
          </div>
          <div>
            <h1 className="text-2xl font-bold">Cours — {LEVEL_LABELS[level] ?? level}</h1>
            <p className="text-muted-foreground text-sm">
              {total} {total > 1 ? "cours" : "cours"} à ce niveau
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-56 rounded-xl border bg-muted/30 animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <BookOpen className="h-12 w-12 mb-4 opacity-30" />
            <p>Aucun cours à ce niveau pour le moment.</p>
            <p className="text-sm mt-1">
              Retournez au catalogue pour en créer un.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {items.map((course) => (
              <Card
                key={course.id}
                className="overflow-hidden hover:shadow-lg transition-all"
              >
                <div className="h-28 bg-gradient-to-br from-blue-500 to-indigo-600 relative">
                  {course.thumbnail_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={course.thumbnail_url}
                      alt={course.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-white">
                      <BookOpen className="h-10 w-10 opacity-50" />
                    </div>
                  )}
                  <div className="absolute top-2 right-2">
                    {course.is_active ? (
                      <span className="rounded-full bg-green-500 text-white text-[10px] font-semibold px-2 py-0.5">
                        Actif
                      </span>
                    ) : (
                      <span className="rounded-full bg-red-500 text-white text-[10px] font-semibold px-2 py-0.5">
                        Inactif
                      </span>
                    )}
                  </div>
                </div>
                <CardContent className="pt-4 space-y-3">
                  <div>
                    <h3 className="font-semibold line-clamp-2 min-h-[3rem]">
                      {course.title}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      {course.teacher_name}
                      {course.subject ? ` · ${course.subject}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center justify-between gap-2 pt-1">
                    <Link
                      href={`/admin/courses/${course.id}/content`}
                      className="flex-1"
                    >
                      <Button size="sm" className="w-full">
                        <Layers className="h-4 w-4 mr-1" /> Gérer
                      </Button>
                    </Link>
                    <button
                      onClick={() => handleToggle(course.id)}
                      title={course.is_active ? "Désactiver" : "Activer"}
                      className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                    >
                      {course.is_active ? (
                        <ToggleRight className="h-5 w-5 text-green-600" />
                      ) : (
                        <ToggleLeft className="h-5 w-5 text-red-400" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(course.id)}
                      title="Supprimer"
                      className="rounded-md p-2 text-muted-foreground hover:bg-red-50 hover:text-red-600 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </CardContent>
              </Card>
            ))}
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
