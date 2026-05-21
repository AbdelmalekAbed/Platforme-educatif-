"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { CourseFull } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  ArrowLeft,
  BookOpen,
  ChevronRight,
  CheckCircle2,
  Circle,
  Layers,
  User,
} from "lucide-react";

export default function StudentCoursePage() {
  const params = useParams<{ id: string }>();
  const courseId = params.id;
  const { isAuthenticated } = useAuthStore();
  const [course, setCourse] = useState<CourseFull | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !courseId) return;
    api
      .getCourseFull(courseId)
      .then(setCourse)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [isAuthenticated, courseId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 rounded bg-muted/30 animate-pulse" />
        <div className="h-40 rounded-xl bg-muted/30 animate-pulse" />
        <div className="h-64 rounded-xl bg-muted/30 animate-pulse" />
      </div>
    );
  }

  if (!course) {
    return (
      <Card>
        <CardContent className="py-16 text-center text-muted-foreground">
          Cours introuvable.
        </CardContent>
      </Card>
    );
  }

  const totalItems = course.chapters.reduce((acc, c) => acc + c.items_count, 0);
  const completedItems = course.chapters.reduce(
    (acc, c) => acc + c.items.filter((i) => i.is_completed).length,
    0
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link href={`/student/catalog/${course.grade_level ?? ""}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" /> Retour
          </Button>
        </Link>
      </div>

      {/* Hero */}
      <div className="rounded-xl bg-gradient-to-r from-primary via-primary/90 to-primary/70 text-primary-foreground p-8">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm opacity-90">
              {course.grade_level && (
                <span className="rounded-full bg-white/20 px-3 py-0.5">
                  {course.grade_level}
                </span>
              )}
              {course.subject && (
                <span className="rounded-full bg-white/20 px-3 py-0.5">
                  {course.subject}
                </span>
              )}
            </div>
            <h1 className="text-3xl font-bold">{course.title}</h1>
            {course.description && (
              <p className="text-sm opacity-90 max-w-2xl">{course.description}</p>
            )}
            <div className="flex items-center gap-4 text-sm opacity-90 pt-2">
              <span className="flex items-center gap-1.5">
                <User className="h-4 w-4" />
                {course.teacher_name}
              </span>
              <span className="flex items-center gap-1.5">
                <Layers className="h-4 w-4" />
                {course.chapters.length} chapitres
              </span>
              <span className="flex items-center gap-1.5">
                <BookOpen className="h-4 w-4" />
                {totalItems} contenus
              </span>
            </div>
          </div>

          <div className="bg-white/15 rounded-xl p-4 min-w-[180px]">
            <div className="text-xs opacity-90 uppercase tracking-wider">Progression</div>
            <div className="text-3xl font-bold mt-1">
              {Math.round(course.progress_percent)}%
            </div>
            <div className="text-xs opacity-90 mt-1">
              {completedItems} / {totalItems} contenus
            </div>
            <div className="h-2 rounded-full bg-white/20 overflow-hidden mt-2">
              <div
                className="h-full bg-white rounded-full transition-all"
                style={{ width: `${course.progress_percent}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Chapters */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Programme du cours</h2>
        {course.chapters.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <Layers className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>Aucun chapitre n&apos;est encore disponible.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {course.chapters.map((chapter, idx) => {
              const completed = chapter.items.filter((i) => i.is_completed).length;
              const percent = chapter.items_count
                ? Math.round((completed / chapter.items_count) * 100)
                : 0;
              return (
                <Link
                  key={chapter.id}
                  href={`/student/courses/${courseId}/chapters/${chapter.id}`}
                >
                  <Card className="hover:shadow-md hover:border-primary/30 transition-all cursor-pointer group mb-3">
                    <CardContent className="p-5">
                      <div className="flex items-center gap-4">
                        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-lg">
                          {idx + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-lg group-hover:text-primary transition-colors">
                            {chapter.title}
                          </h3>
                          {chapter.description && (
                            <p className="text-sm text-muted-foreground line-clamp-1 mt-0.5">
                              {chapter.description}
                            </p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <BookOpen className="h-3 w-3" />
                              {chapter.items_count} contenus
                            </span>
                            <span className="flex items-center gap-1">
                              {percent === 100 ? (
                                <CheckCircle2 className="h-3 w-3 text-green-500" />
                              ) : (
                                <Circle className="h-3 w-3" />
                              )}
                              {percent}%
                            </span>
                          </div>
                          {chapter.items_count > 0 && (
                            <div className="h-1 rounded-full bg-secondary overflow-hidden mt-2">
                              <div
                                className="h-full bg-primary rounded-full transition-all"
                                style={{ width: `${percent}%` }}
                              />
                            </div>
                          )}
                        </div>
                        <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
