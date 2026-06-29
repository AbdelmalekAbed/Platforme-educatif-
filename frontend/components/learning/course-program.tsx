"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { CourseFull, ChapterWithItems } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  ArrowLeft,
  BookOpen,
  ChevronRight,
  CheckCircle2,
  Circle,
  Layers,
  Loader2,
} from "lucide-react";

interface CourseProgramProps {
  courseId: string;
  /** URL of the page hosting the course list (back arrow target). Either a static string or a builder that gets the loaded course. */
  backHref: string | ((course: CourseFull | null) => string);
  /** Builder for chapter detail links (e.g. `/student/courses/X/chapters/Y` or `/teacher/courses/X/chapters/Y`). */
  chapterHref: (courseId: string, chapterId: string) => string;
  /** When true, hide per-student progress bars and completion ticks (teacher preview). */
  hideProgress?: boolean;
  /** When true, show the "I already know this course/chapter" checkboxes (student-only). */
  showKnownActions?: boolean;
}

export function CourseProgram({
  courseId,
  backHref,
  chapterHref,
  hideProgress = false,
  showKnownActions = false,
}: CourseProgramProps) {
  const { isAuthenticated } = useAuthStore();
  const [course, setCourse] = useState<CourseFull | null>(null);
  const [loading, setLoading] = useState(true);
  const [togglingCourse, setTogglingCourse] = useState(false);
  const [togglingChapter, setTogglingChapter] = useState<Record<string, boolean>>({});

  const refresh = useCallback(async () => {
    try {
      const data = await api.getCourseFull(courseId);
      setCourse(data);
    } catch (err) {
      console.error(err);
    }
  }, [courseId]);

  useEffect(() => {
    if (!isAuthenticated || !courseId) return;
    setLoading(true);
    api
      .getCourseFull(courseId)
      .then(setCourse)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [isAuthenticated, courseId]);

  const toggleCourseKnown = async () => {
    if (!course) return;
    const willKnow = !course.is_known;
    setTogglingCourse(true);
    setCourse({
      ...course,
      is_known: willKnow,
      progress_percent: willKnow ? 100 : course.progress_percent,
    });
    try {
      if (willKnow) await api.markCourseKnown(courseId);
      else await api.unmarkCourseKnown(courseId);
      await refresh();
    } catch (err) {
      console.error(err);
      // Revert
      setCourse(course);
    } finally {
      setTogglingCourse(false);
    }
  };

  const toggleChapterKnown = async (chapter: ChapterWithItems) => {
    if (!course) return;
    const willKnow = !chapter.is_known;
    setTogglingChapter((s) => ({ ...s, [chapter.id]: true }));
    setCourse({
      ...course,
      chapters: course.chapters.map((c) =>
        c.id === chapter.id ? { ...c, is_known: willKnow } : c
      ),
    });
    try {
      if (willKnow) await api.markChapterKnown(chapter.id);
      else await api.unmarkChapterKnown(chapter.id);
      await refresh();
    } catch (err) {
      console.error(err);
      setCourse(course);
    } finally {
      setTogglingChapter((s) => ({ ...s, [chapter.id]: false }));
    }
  };

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

  const resolvedBackHref = typeof backHref === "function" ? backHref(course) : backHref;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link href={resolvedBackHref}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" /> Retour
          </Button>
        </Link>
      </div>

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
                <Layers className="h-4 w-4" />
                {course.chapters.length} chapitres
              </span>
              <span className="flex items-center gap-1.5">
                <BookOpen className="h-4 w-4" />
                {totalItems} contenus
              </span>
            </div>

            {showKnownActions && (
              <label
                className={`mt-3 inline-flex items-center gap-2 text-sm cursor-pointer select-none rounded-md px-3 py-1.5 transition-colors ${
                  course.is_known ? "bg-white/25" : "bg-white/10 hover:bg-white/20"
                }`}
              >
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-white"
                  checked={!!course.is_known}
                  disabled={togglingCourse}
                  onChange={toggleCourseKnown}
                />
                <span>Je connais déjà tout ce cours</span>
                {togglingCourse && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              </label>
            )}
          </div>

          {!hideProgress && (
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
          )}
        </div>
      </div>

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
                <Card
                  key={chapter.id}
                  className="hover:shadow-md hover:border-primary/30 transition-all group mb-3"
                >
                  <CardContent className="p-5">
                    <div className="flex items-center gap-4">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-lg">
                        {idx + 1}
                      </div>
                      <Link
                        href={chapterHref(courseId, chapter.id)}
                        className="flex-1 min-w-0 cursor-pointer"
                      >
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
                          {!hideProgress && (
                            <span className="flex items-center gap-1">
                              {percent === 100 ? (
                                <CheckCircle2 className="h-3 w-3 text-green-500" />
                              ) : (
                                <Circle className="h-3 w-3" />
                              )}
                              {percent}%
                            </span>
                          )}
                        </div>
                        {!hideProgress && chapter.items_count > 0 && (
                          <div className="h-1 rounded-full bg-secondary overflow-hidden mt-2">
                            <div
                              className="h-full bg-primary rounded-full transition-all"
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                        )}
                      </Link>
                      <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
                    </div>

                    {showKnownActions && (
                      <label
                        className={`mt-3 flex items-center gap-2 text-xs cursor-pointer select-none rounded-md px-2 py-1.5 transition-colors ${
                          chapter.is_known
                            ? "bg-green-50 text-green-800 hover:bg-green-100"
                            : "text-muted-foreground hover:bg-accent"
                        }`}
                      >
                        <input
                          type="checkbox"
                          className="h-3.5 w-3.5 accent-green-600"
                          checked={!!chapter.is_known}
                          disabled={!!togglingChapter[chapter.id] || course.is_known}
                          onChange={() => toggleChapterKnown(chapter)}
                        />
                        <span className="flex-1">
                          {course.is_known
                            ? "Cours entier marqué connu"
                            : "Je connais déjà ce chapitre"}
                        </span>
                        {togglingChapter[chapter.id] && (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        )}
                      </label>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
