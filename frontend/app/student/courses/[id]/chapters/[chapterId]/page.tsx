"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { CourseFull, ChapterWithItems, ChapterItem } from "@/types";
import { Button } from "@/components/ui/button";
import { VideoPlayer } from "@/components/learning/video-player";
import { PdfViewer } from "@/components/learning/pdf-viewer";
import { QuizRunner } from "@/components/learning/quiz-runner";
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
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

export default function ChapterDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string; chapterId: string }>();
  const courseId = params.id;
  const chapterId = params.chapterId;
  const { isAuthenticated } = useAuthStore();

  const [course, setCourse] = useState<CourseFull | null>(null);
  const [activeChapter, setActiveChapter] = useState<ChapterWithItems | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("parcours");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeItemId, setActiveItemId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [remarque, setRemarque] = useState("");
  const [showCompletion, setShowCompletion] = useState(false);

  const loadCourse = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const data = await api.getCourseFull(courseId);
      setCourse(data);
      const ch = data.chapters.find((c) => c.id === chapterId) ?? data.chapters[0] ?? null;
      setActiveChapter(ch ?? null);
      if (ch && ch.items.length > 0) {
        setActiveItemId((current) =>
          current && ch.items.some((i) => i.id === current) ? current : ch.items[0].id
        );
      }
    } catch (err) {
      console.error(err);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [courseId, chapterId]);

  useEffect(() => {
    if (!isAuthenticated || !courseId) return;
    loadCourse();
  }, [isAuthenticated, courseId, loadCourse]);

  const activeItem: ChapterItem | undefined = activeChapter?.items.find(
    (i) => i.id === activeItemId
  );
  const itemIndex = activeChapter?.items.findIndex((i) => i.id === activeItemId) ?? -1;
  const totalItems = activeChapter?.items_count ?? 0;
  const completedItems =
    activeChapter?.items.filter((i) => i.is_completed).length ?? 0;
  const progress = totalItems ? Math.round((completedItems / totalItems) * 100) : 0;

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
    // Last item of the current chapter: jump to the first item of the next chapter,
    // or trigger the course-completion screen if this was the last chapter too.
    if (!course) return;
    const currentChapterIdx = course.chapters.findIndex((c) => c.id === activeChapter.id);
    const nextChapter = course.chapters
      .slice(currentChapterIdx + 1)
      .find((c) => c.items.length > 0);
    if (nextChapter) {
      router.push(`/student/courses/${courseId}/chapters/${nextChapter.id}`);
    } else {
      setShowCompletion(true);
    }
  };

  const handleResourceCompleted = async (resourceId: string) => {
    try {
      await api.markResourceCompleted(resourceId);
      loadCourse(true);
    } catch (err) {
      console.error(err);
    }
  };

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
      <div className="-m-6 flex h-[calc(100vh-4rem)] items-center justify-center bg-gradient-to-br from-primary/5 via-background to-purple-500/5 px-6">
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
              Félicitations !
            </h1>
            <p className="text-lg text-foreground">
              Tu viens de terminer&nbsp;
              <span className="font-semibold">{course.title}</span>.
            </p>
            <p className="text-muted-foreground">
              Chaque chapitre maîtrisé est un pas de plus vers ta réussite.
              Continue sur ta lancée — l&apos;effort que tu fournis aujourd&apos;hui
              construit ton avenir. 🚀
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <Link href="/student/courses">
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
                    router.push(
                      `/student/courses/${courseId}/chapters/${firstChapterWithItems.id}`
                    );
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
    <div className="-m-6 flex h-[calc(100vh-4rem)] flex-col bg-background">
      <div className="flex items-center justify-between border-b bg-card px-4 py-2">
        <div className="flex items-center gap-2">
          <Link href={`/student/courses/${courseId}`}>
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
              <h2 className="font-semibold text-base leading-tight">
                {activeChapter.title}
              </h2>
              <div className="mt-3 flex items-center gap-2">
                <div className="flex-1 h-1.5 rounded-full bg-secondary overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <span className="text-xs font-semibold text-primary">{progress} %</span>
              </div>
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
                <div className="space-y-0.5">
                  {activeChapter.items.length === 0 && (
                    <div className="text-center text-sm text-muted-foreground py-8">
                      Aucun contenu dans ce chapitre.
                    </div>
                  )}
                  {activeChapter.items.map((item, idx) => {
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
                        className={`w-full text-left rounded-lg px-3 py-2.5 text-sm font-medium transition-colors flex items-center gap-2 ${
                          isActive
                            ? "bg-primary text-primary-foreground"
                            : "hover:bg-accent"
                        }`}
                      >
                        <span className="text-xs opacity-70 w-5">{idx + 1}.</span>
                        <Icon className="h-4 w-4 shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="line-clamp-1">{item.title}</div>
                          <div className={`text-[10px] ${isActive ? "opacity-80" : "opacity-60"}`}>
                            {label}
                          </div>
                        </div>
                        {item.is_completed && (
                          <CheckCircle2
                            className={`h-4 w-4 ${
                              isActive ? "text-primary-foreground" : "text-green-500"
                            }`}
                          />
                        )}
                      </button>
                    );
                  })}

                  {course.chapters.length > 1 && (
                    <div className="mt-3 pt-3 border-t space-y-0.5">
                      {course.chapters
                        .filter((c) => c.id !== activeChapter.id)
                        .map((c) => (
                          <Link
                            key={c.id}
                            href={`/student/courses/${courseId}/chapters/${c.id}`}
                            className="block rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
                          >
                            <span className="opacity-70">
                              {course.chapters.findIndex((x) => x.id === c.id) + 1}.
                            </span>{" "}
                            {c.title}
                          </Link>
                        ))}
                    </div>
                  )}
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

        <main className="flex-1 overflow-y-auto bg-muted/20 p-6">
          {!activeItem ? (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              {activeChapter.items.length === 0
                ? "Aucun contenu dans ce chapitre."
                : "Sélectionnez un élément pour commencer."}
            </div>
          ) : activeItem.item_type === "quiz" ? (
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
              <QuizRunner quizId={activeItem.id} onCompleted={() => loadCourse(true)} />
            </div>
          ) : (
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
                  <Button
                    size="sm"
                    onClick={() => {
                      const resourceId = activeItem.id;
                      goNext();
                      handleResourceCompleted(resourceId);
                    }}
                  >
                    {nextLabel}
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>

              <div className="rounded-xl border bg-card p-4 shadow-sm">
                {activeItem.kind === "video" ? (
                  <VideoPlayer url={activeItem.url} title={activeItem.title} />
                ) : (
                  <PdfViewer url={activeItem.url} title={activeItem.title} />
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
