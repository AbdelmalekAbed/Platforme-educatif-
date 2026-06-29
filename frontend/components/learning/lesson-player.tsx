"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { CourseFull, ChapterWithItems, ChapterItem } from "@/types";
import { Button } from "@/components/ui/button";
import { VideoPlayer } from "@/components/learning/video-player";
import { PdfViewer } from "@/components/learning/pdf-viewer";
import { QuizRunner } from "@/components/learning/quiz-runner";
import {
  ArrowLeft,
  Download,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
  PanelTopClose,
  PanelTopOpen,
  Play,
  FileText,
  HelpCircle,
  CheckCircle2,
  BookOpen,
  Trophy,
  Sparkles,
} from "lucide-react";

type Tab = "parcours" | "apprenants" | "remarque";

const KIND_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  video: Play,
  pdf: FileText,
  exercise: FileText,
  correction: FileText,
  fiche: BookOpen,
};

const KIND_LABELS: Record<string, string> = {
  video: "video",
  pdf: "pdf",
  exercise: "pdf",
  correction: "pdf",
  fiche: "pdf",
};

interface LessonPlayerProps {
  courseId: string;
  chapterId: string;
  /** URL of the course program / overview page (back arrow). */
  backHref: string;
  /** Builder for inter-chapter navigation links (e.g. sidebar "other chapters" and "next chapter" routing). */
  chapterHref: (courseId: string, chapterId: string) => string;
  /** URL to return to after course completion. */
  coursesHomeHref: string;
  /** "student" tracks progress (marks resources completed). "teacher" just navigates without mutating state. */
  role: "student" | "teacher";
}

export function LessonPlayer({
  courseId,
  chapterId,
  backHref,
  chapterHref,
  coursesHomeHref,
  role,
}: LessonPlayerProps) {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  const [course, setCourse] = useState<CourseFull | null>(null);
  const [activeChapter, setActiveChapter] = useState<ChapterWithItems | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("parcours");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  // "Mode lecture" for PDFs: hides the in-app info/nav bar so the document gets the full height.
  const [pdfImmersive, setPdfImmersive] = useState(false);
  const [activeItemId, setActiveItemId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [remarque, setRemarque] = useState("");
  const [showCompletion, setShowCompletion] = useState(false);
  // Resources auto-marked completed during this mount, to avoid duplicate POSTs.
  const completedRef = useRef<Set<string>>(new Set());

  // Fetch the WHOLE course (all chapters + items) once per course. This MUST stay keyed on
  // courseId ONLY — never on chapterId. Switching chapters is a pure in-memory selection (see the
  // derive effect below). Re-introducing chapterId here would refetch + flash the loading skeleton
  // on every notion change (the "reload" bug) and reset the scroll container. Keep this invariant.
  const loadCourse = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await api.getCourseFull(courseId);
      setCourse(data);
    } catch (err) {
      console.error(err);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    if (!isAuthenticated || !courseId) return;
    loadCourse();
  }, [isAuthenticated, courseId, loadCourse]);

  // Derive the active chapter from the route param against the already-loaded course. Runs on
  // chapterId/course change with no network and no loading state → instant notion switch, and the
  // <main> scroll container is never unmounted so its scroll position is preserved.
  useEffect(() => {
    if (!course) return;
    const ch = course.chapters.find((c) => c.id === chapterId) ?? course.chapters[0] ?? null;
    setActiveChapter(ch);
    if (ch && ch.items.length > 0) {
      setActiveItemId((current) =>
        current && ch.items.some((i) => i.id === current) ? current : ch.items[0].id
      );
    } else {
      setActiveItemId(null);
    }
  }, [chapterId, course]);

  const activeItem: ChapterItem | undefined = activeChapter?.items.find(
    (i) => i.id === activeItemId
  );
  const itemIndex = activeChapter?.items.findIndex((i) => i.id === activeItemId) ?? -1;
  const totalItems = activeChapter?.items_count ?? 0;

  const goPrev = () => {
    if (!activeChapter || itemIndex <= 0) return;
    setActiveItemId(activeChapter.items[itemIndex - 1].id);
  };

  const goNext = () => {
    if (!activeChapter) return;
    if (itemIndex >= 0 && itemIndex < activeChapter.items.length - 1) {
      setActiveItemId(activeChapter.items[itemIndex + 1].id);
      return;
    }
    if (!course) return;
    const currentChapterIdx = course.chapters.findIndex((c) => c.id === activeChapter.id);
    const nextChapter = course.chapters
      .slice(currentChapterIdx + 1)
      .find((c) => c.items.length > 0);
    if (nextChapter) {
      router.push(chapterHref(courseId, nextChapter.id), { scroll: false });
    } else {
      setShowCompletion(true);
    }
  };

  // Mark a resource as completed as soon as the student opens it, so the progress bar reflects
  // consultation. PDFs (iframe) and embedded videos (YouTube/Vimeo iframe) expose no reliable
  // "finished" event, so opening the item is the trigger. Quizzes are excluded — they only count
  // once passed. Deduped via completedRef + the is_completed flag so it fires at most once per item
  // and never loops when loadCourse refetches.
  useEffect(() => {
    if (role !== "student") return;
    if (!activeItem || activeItem.item_type !== "resource") return;
    if (activeItem.is_completed || completedRef.current.has(activeItem.id)) return;
    const id = activeItem.id;
    completedRef.current.add(id);
    api
      .markResourceCompleted(id)
      .then(() => loadCourse(true))
      .catch((err) => console.error(err));
  }, [activeItem, role, loadCourse]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 rounded bg-muted/30 animate-pulse" />
        <div className="h-[70vh] rounded-xl bg-muted/30 animate-pulse" />
      </div>
    );
  }

  if (showCompletion && course) {
    const firstChapterWithItems = course.chapters.find((c) => c.items.length > 0);
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-primary/5 via-background to-purple-500/5 px-6">
        <div className="max-w-xl text-center space-y-6">
          <div className="relative inline-flex items-center justify-center">
            <div className="absolute -inset-6 rounded-full bg-gradient-to-br from-amber-400/30 to-orange-500/30 blur-2xl animate-pulse" />
            <div className="relative flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg">
              <Trophy className="h-12 w-12 text-white" />
            </div>
            <Sparkles className="absolute -top-2 -right-2 h-6 w-6 text-amber-400 animate-pulse" />
            <Sparkles className="absolute -bottom-1 -left-3 h-5 w-5 text-orange-400 animate-pulse" />
          </div>

          <div className="space-y-2">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-amber-500 via-orange-500 to-pink-500 bg-clip-text text-transparent">
              {role === "teacher" ? "Fin du parcours" : "Félicitations !"}
            </h1>
            <p className="text-lg text-foreground">
              {role === "teacher" ? "Tu as parcouru tout " : "Tu viens de terminer "}
              <span className="font-semibold">{course.title}</span>.
            </p>
            {role === "student" && (
              <p className="text-muted-foreground">
                Chaque chapitre maîtrisé est un pas de plus vers ta réussite.
                Continue sur ta lancée — l&apos;effort que tu fournis aujourd&apos;hui
                construit ton avenir. 🚀
              </p>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <Link href={coursesHomeHref}>
              <Button variant="default" size="lg">
                Retour à mes cours
              </Button>
            </Link>
            {firstChapterWithItems && (
              <Button
                variant="outline"
                size="lg"
                onClick={() => {
                  setShowCompletion(false);
                  setActiveItemId(firstChapterWithItems.items[0].id);
                  if (firstChapterWithItems.id !== activeChapter?.id) {
                    router.push(chapterHref(courseId, firstChapterWithItems.id), { scroll: false });
                  }
                }}
              >
                Revoir le cours
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!course || !activeChapter) {
    return <div className="text-center text-muted-foreground py-16">Chapitre introuvable.</div>;
  }

  const isLastInChapter = itemIndex >= activeChapter.items.length - 1;
  const currentChapterIdx = course.chapters.findIndex((c) => c.id === activeChapter.id);
  const hasNextChapter = course.chapters
    .slice(currentChapterIdx + 1)
    .some((c) => c.items.length > 0);
  const nextLabel = !isLastInChapter
    ? "Suivant"
    : hasNextChapter
    ? "Chapitre suivant"
    : "Terminer le cours";

  return (
    <div className="flex h-screen flex-col bg-background">
      <div className="flex items-center justify-between border-b bg-card px-4 py-2">
        <div className="flex items-center gap-2">
          <Link href={backHref}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" /> Back to program
            </Button>
          </Link>
          <button
            onClick={() => setSidebarOpen((s) => !s)}
            className="rounded-md p-2 hover:bg-accent"
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {sidebarOpen && (
          <aside className="w-80 shrink-0 border-r bg-card overflow-y-auto">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-base leading-tight line-clamp-2">
                {course.title}
              </h2>
              {role === "student" && (
                <div className="mt-3 flex items-center gap-2">
                  <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${Math.round(course.progress_percent)}%` }}
                    />
                  </div>
                  <span className="text-xs font-semibold text-primary">
                    {Math.round(course.progress_percent)} %
                  </span>
                </div>
              )}
            </div>

            <div className="grid grid-cols-3 border-b text-sm">
              {(["parcours", "apprenants", "remarque"] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setActiveTab(t)}
                  className={`px-3 py-2.5 font-medium capitalize transition-colors relative ${
                    activeTab === t
                      ? "text-primary"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {t === "remarque" ? "Remarque" : t === "apprenants" ? "Apprenants" : "Parcours"}
                  {activeTab === t && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                  )}
                </button>
              ))}
            </div>

            <div className="p-2">
              {activeTab === "parcours" && (
                <div className="space-y-1">
                  {course.chapters.map((chapter, cIdx) => {
                    // The whole chapter list is rendered in fixed order. The active notion stays at
                    // its own position — highlighted and expanded in place — instead of being pulled
                    // up to a header. So nothing "jumps to the top" when switching notions.
                    const isActiveChapter = chapter.id === activeChapter.id;
                    const chCompleted = chapter.items.filter((i) => i.is_completed).length;
                    const chPercent = chapter.items_count
                      ? Math.round((chCompleted / chapter.items_count) * 100)
                      : 0;
                    return (
                      <div key={chapter.id}>
                        {isActiveChapter ? (
                          <div className="flex items-center gap-2 rounded-lg bg-accent/60 px-3 py-2 text-sm font-semibold">
                            <span className="w-5 text-xs opacity-70">{cIdx + 1}.</span>
                            <span className="min-w-0 flex-1 line-clamp-1">{chapter.title}</span>
                            {role === "student" && (
                              <span className="shrink-0 text-[10px] font-semibold text-primary">
                                {chPercent}%
                              </span>
                            )}
                          </div>
                        ) : (
                          <Link
                            href={chapterHref(courseId, chapter.id)}
                            scroll={false}
                            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
                          >
                            <span className="w-5 text-xs opacity-70">{cIdx + 1}.</span>
                            <span className="min-w-0 flex-1 line-clamp-1">{chapter.title}</span>
                            {role === "student" &&
                              (chPercent === 100 ? (
                                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-green-500" />
                              ) : (
                                <span className="shrink-0 text-[10px] opacity-60">{chPercent}%</span>
                              ))}
                          </Link>
                        )}

                        {isActiveChapter && (
                          <div className="ml-3 mt-0.5 space-y-0.5 border-l pl-2">
                            {chapter.items.length === 0 && (
                              <div className="py-6 text-center text-sm text-muted-foreground">
                                Aucun contenu dans cette notion.
                              </div>
                            )}
                            {chapter.items.map((item, idx) => {
                              const isActive = activeItemId === item.id;
                              const Icon =
                                item.item_type === "resource"
                                  ? KIND_ICONS[item.kind] ?? FileText
                                  : HelpCircle;
                              const label =
                                item.item_type === "resource"
                                  ? KIND_LABELS[item.kind] ?? item.kind
                                  : "quiz";
                              return (
                                <button
                                  key={item.id}
                                  onClick={() => setActiveItemId(item.id)}
                                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-colors ${
                                    isActive
                                      ? "bg-primary text-primary-foreground"
                                      : "hover:bg-accent"
                                  }`}
                                >
                                  <span className="w-5 text-xs opacity-70">{idx + 1}.</span>
                                  <Icon className="h-4 w-4 shrink-0" />
                                  <div className="min-w-0 flex-1">
                                    <div className="line-clamp-1">{item.title}</div>
                                    <div className={`text-[10px] ${isActive ? "opacity-80" : "opacity-60"}`}>
                                      {label}
                                    </div>
                                  </div>
                                  {role === "student" && item.is_completed && (
                                    <CheckCircle2
                                      className={`h-4 w-4 ${
                                        isActive ? "text-primary-foreground" : "text-green-500"
                                      }`}
                                    />
                                  )}
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {activeTab === "apprenants" && (
                <div className="text-center text-sm text-muted-foreground py-12 px-4">
                  La liste des apprenants inscrits à ce chapitre sera disponible prochainement.
                </div>
              )}

              {activeTab === "remarque" && (
                <div className="p-3 space-y-2">
                  <p className="text-xs text-muted-foreground">
                    Notez vos remarques personnelles sur ce chapitre.
                  </p>
                  <textarea
                    value={remarque}
                    onChange={(e) => setRemarque(e.target.value)}
                    placeholder="Écrire une remarque..."
                    className="min-h-[200px] w-full rounded-md border bg-background p-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </div>
              )}
            </div>
          </aside>
        )}

        <main className="flex flex-1 flex-col overflow-hidden bg-muted/20">
          {!activeItem ? (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              {activeChapter.items.length === 0
                ? "Aucun contenu dans ce chapitre."
                : "Sélectionnez un élément pour commencer."}
            </div>
          ) : activeItem.item_type === "quiz" ? (
            <div className="flex-1 overflow-y-auto p-6">
              <div className="max-w-3xl mx-auto space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                      <HelpCircle className="h-3.5 w-3.5" /> Quiz
                    </div>
                    <h1 className="text-2xl font-bold">{activeItem.title}</h1>
                    <p className="text-sm text-muted-foreground mt-1">
                      Étape {itemIndex + 1} / {totalItems}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {itemIndex > 0 && (
                      <Button variant="outline" size="sm" onClick={goPrev}>
                        <ChevronLeft className="h-4 w-4 mr-1" /> Précédent
                      </Button>
                    )}
                    <Button size="sm" onClick={goNext}>
                      {nextLabel}
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
                <QuizRunner
                  quizId={activeItem.id}
                  onCompleted={role === "student" ? () => loadCourse(true) : undefined}
                  readOnly={role === "teacher"}
                />
              </div>
            </div>
          ) : activeItem.kind === "video" ? (
            <div className="flex-1 overflow-y-auto p-6">
              <div className="max-w-5xl mx-auto space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs uppercase tracking-wider text-muted-foreground">
                      {KIND_LABELS[activeItem.kind] ?? activeItem.kind}
                    </div>
                    <h1 className="text-2xl font-bold">{activeItem.title}</h1>
                    <p className="text-sm text-muted-foreground mt-1">
                      Étape {itemIndex + 1} / {totalItems}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {itemIndex > 0 && (
                      <Button variant="outline" size="sm" onClick={goPrev}>
                        <ChevronLeft className="h-4 w-4 mr-1" /> Précédent
                      </Button>
                    )}
                    <Button size="sm" onClick={goNext}>
                      {nextLabel}
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>

                <div className="rounded-xl border bg-card p-4 shadow-sm">
                  <VideoPlayer url={activeItem.url} title={activeItem.title} />
                </div>
              </div>
            </div>
          ) : (
            // PDF / document — fills the whole pane edge-to-edge (inspired by Hedacademy). A single
            // compact bar carries the context + download + navigation; the iframe takes all the rest.
            <div className="relative flex h-full flex-col">
              {!pdfImmersive && (
                <div className="flex items-center justify-between gap-3 border-b bg-card px-4 py-2">
                  <div className="min-w-0">
                    <div className="text-[11px] uppercase tracking-wider text-muted-foreground">
                      {KIND_LABELS[activeItem.kind] ?? activeItem.kind} · Étape {itemIndex + 1} / {totalItems}
                    </div>
                    <h1 className="truncate text-base font-semibold leading-tight">
                      {activeItem.title}
                    </h1>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <a
                      href={activeItem.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hidden items-center gap-1 text-sm text-muted-foreground hover:text-primary sm:flex"
                    >
                      <Download className="h-4 w-4" />
                      <span>Télécharger</span>
                    </a>
                    {itemIndex > 0 && (
                      <Button variant="outline" size="sm" onClick={goPrev}>
                        <ChevronLeft className="h-4 w-4 mr-1" /> Précédent
                      </Button>
                    )}
                    <Button size="sm" onClick={goNext}>
                      {nextLabel}
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                    <div className="mx-0.5 h-6 w-px bg-border" />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setPdfImmersive(true)}
                      title="Mode lecture — masquer la barre pour agrandir le PDF"
                      aria-label="Masquer la barre"
                    >
                      <PanelTopClose className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
              <div className="min-h-0 flex-1 p-3">
                {/* Adaptive width: when the Parcours panel is closed the pane is wide, so let the
                    document grow (~1280px) to use the freed space; otherwise keep it centered (~1024px). */}
                <div
                  className={`mx-auto h-full w-full ${
                    sidebarOpen ? "max-w-5xl" : "max-w-7xl"
                  }`}
                >
                  <PdfViewer url={activeItem.url} title={activeItem.title} fill />
                </div>
              </div>
              {pdfImmersive && (
                <button
                  onClick={() => setPdfImmersive(false)}
                  title="Afficher la barre"
                  aria-label="Afficher la barre"
                  className="absolute right-3 top-2.5 z-20 flex h-8 w-8 items-center justify-center rounded-full border bg-card/90 text-muted-foreground shadow-md backdrop-blur transition-colors hover:bg-card hover:text-foreground"
                >
                  <PanelTopOpen className="h-4 w-4" />
                </button>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
