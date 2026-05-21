"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type {
  CourseFull,
  ChapterWithItems,
  ChapterItem,
  ResourceKind,
  QuizAdmin,
} from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ArrowLeft,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  Video,
  FileText,
  Layers,
  BookOpen,
  HelpCircle,
  X,
  Paperclip,
} from "lucide-react";

const RESOURCE_KINDS: { value: ResourceKind; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { value: "video", label: "Vidéo", icon: Video },
  { value: "fiche", label: "Fiche", icon: BookOpen },
  { value: "pdf", label: "PDF", icon: FileText },
  { value: "exercise", label: "Exercice", icon: FileText },
  { value: "correction", label: "Correction", icon: FileText },
];

const KIND_ICON: Record<string, React.ComponentType<{ className?: string }>> = {
  video: Video,
  fiche: BookOpen,
  pdf: FileText,
  exercise: FileText,
  correction: FileText,
};

interface ResourceForm {
  title: string;
  kind: ResourceKind;
  url: string;
}

interface CourseContentEditorProps {
  courseId: string;
  /** Either a static URL or a function called with the loaded course to compute the URL dynamically. */
  backHref: string | ((course: CourseFull | null) => string);
  backLabel?: string;
}

export function CourseContentEditor({
  courseId,
  backHref,
  backLabel = "Retour",
}: CourseContentEditorProps) {
  const { isAuthenticated } = useAuthStore();
  const [course, setCourse] = useState<CourseFull | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(new Set());
  const [expandedQuizzes, setExpandedQuizzes] = useState<Set<string>>(new Set());
  const [quizDetails, setQuizDetails] = useState<Record<string, QuizAdmin>>({});

  const [newChapterTitle, setNewChapterTitle] = useState("");
  const [resourceForm, setResourceForm] = useState<Record<string, ResourceForm>>({});
  const [uploadingChapter, setUploadingChapter] = useState<Record<string, boolean>>({});
  const [uploadError, setUploadError] = useState<Record<string, string>>({});
  const [quizQuestionForm, setQuizQuestionForm] = useState<Record<string, {
    text: string;
    choices: { id: string; text: string }[];
    correct: string;
  }>>({});

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getCourseFull(courseId);
      setCourse(data);
    } catch (err) {
      // Course may have been deleted (e.g. clicking a stale notification link).
      // The UI already renders a "Cours introuvable" fallback when course is null,
      // so swallow the expected 404 instead of polluting the console.
      const msg = err instanceof Error ? err.message : "";
      if (!msg.includes("introuvable") && !msg.includes("HTTP 404")) {
        console.error(err);
      }
      setCourse(null);
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    if (!isAuthenticated || !courseId) return;
    reload();
  }, [isAuthenticated, courseId, reload]);

  const toggleChapter = (id: string) => {
    setExpandedChapters((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleQuiz = async (quizId: string) => {
    setExpandedQuizzes((s) => {
      const next = new Set(s);
      if (next.has(quizId)) next.delete(quizId);
      else next.add(quizId);
      return next;
    });
    if (!quizDetails[quizId]) {
      try {
        const quiz = await api.getQuizAdmin(quizId);
        setQuizDetails((s) => ({ ...s, [quizId]: quiz }));
      } catch (err) {
        console.error(err);
      }
    }
  };

  const addChapter = async () => {
    if (!newChapterTitle.trim() || !course) return;
    await api.createChapter(courseId, {
      title: newChapterTitle.trim(),
      position: course.chapters.length,
    });
    setNewChapterTitle("");
    reload();
  };

  const removeChapter = async (id: string) => {
    if (!confirm("Supprimer ce chapitre et tout son contenu ?")) return;
    await api.deleteChapter(id);
    reload();
  };

  const addResource = async (chapter: ChapterWithItems) => {
    const form = resourceForm[chapter.id];
    if (!form?.title || !form?.url) return;
    await api.createChapterResource(chapter.id, {
      title: form.title,
      kind: form.kind,
      url: form.url,
      position: chapter.items_count,
    });
    setResourceForm((s) => ({ ...s, [chapter.id]: { title: "", kind: "pdf", url: "" } }));
    reload();
  };

  const removeResource = async (resourceId: string) => {
    await api.deleteResource(resourceId);
    reload();
  };

  const handleFileUpload = async (chapter: ChapterWithItems, file: File) => {
    setUploadError((s) => ({ ...s, [chapter.id]: "" }));
    setUploadingChapter((s) => ({ ...s, [chapter.id]: true }));
    try {
      const result = await api.uploadFile(file);
      const inferredKind: ResourceKind = result.kind === "video" ? "video" : "pdf";
      const current = resourceForm[chapter.id] ?? { title: "", kind: "pdf" as ResourceKind, url: "" };
      setResourceForm((s) => ({
        ...s,
        [chapter.id]: {
          title: current.title || result.filename.replace(/\.[^.]+$/, ""),
          kind: inferredKind,
          url: result.url,
        },
      }));
    } catch (err: unknown) {
      setUploadError((s) => ({
        ...s,
        [chapter.id]: err instanceof Error ? err.message : "Échec de l'envoi",
      }));
    } finally {
      setUploadingChapter((s) => ({ ...s, [chapter.id]: false }));
    }
  };

  const addQuiz = async (chapter: ChapterWithItems) => {
    const quiz = await api.createQuiz(chapter.id, { position: chapter.items_count });
    setQuizDetails((s) => ({ ...s, [quiz.id]: { ...quiz, questions: [] } }));
    setExpandedQuizzes((s) => new Set(s).add(quiz.id));
    reload();
  };

  const removeQuiz = async (quizId: string) => {
    if (!confirm("Supprimer le quiz et toutes ses questions ?")) return;
    await api.deleteQuiz(quizId);
    setQuizDetails((s) => {
      const next = { ...s };
      delete next[quizId];
      return next;
    });
    reload();
  };

  const addQuestion = async (quizId: string) => {
    const form = quizQuestionForm[quizId];
    if (!form?.text || form.choices.length < 2 || !form.correct) return;
    await api.addQuizQuestion(quizId, {
      text: form.text,
      choices: form.choices,
      correct_choice_id: form.correct,
    });
    setQuizQuestionForm((s) => ({
      ...s,
      [quizId]: { text: "", choices: [{ id: "a", text: "" }, { id: "b", text: "" }], correct: "a" },
    }));
    const refreshed = await api.getQuizAdmin(quizId);
    setQuizDetails((s) => ({ ...s, [quizId]: refreshed }));
  };

  const removeQuestion = async (quizId: string, questionId: string) => {
    await api.deleteQuizQuestion(questionId);
    const refreshed = await api.getQuizAdmin(quizId);
    setQuizDetails((s) => ({ ...s, [quizId]: refreshed }));
  };

  if (loading) {
    return <div className="animate-pulse text-muted-foreground">Chargement...</div>;
  }

  if (!course) {
    return <div className="text-center text-muted-foreground py-16">Cours introuvable.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link href={typeof backHref === "function" ? backHref(course) : backHref}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-1" /> {backLabel}
          </Button>
        </Link>
      </div>

      <div className="rounded-xl border bg-gradient-to-r from-primary/10 to-background p-6">
        <h1 className="text-2xl font-bold">{course.title}</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Gérez les chapitres et leurs fichiers (vidéo, PDF, quiz)
        </p>
        <div className="mt-3 flex gap-2 text-xs">
          {course.grade_level && (
            <span className="rounded-full bg-secondary px-3 py-1">{course.grade_level}</span>
          )}
          {course.subject && (
            <span className="rounded-full bg-secondary px-3 py-1">{course.subject}</span>
          )}
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Ajouter un chapitre</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Ex: Aire, Périmètre et Volume 3ème"
              value={newChapterTitle}
              onChange={(e) => setNewChapterTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addChapter()}
            />
            <Button onClick={addChapter} disabled={!newChapterTitle.trim()}>
              <Plus className="h-4 w-4 mr-1" /> Ajouter
            </Button>
          </div>
        </CardContent>
      </Card>

      {course.chapters.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Layers className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p>Aucun chapitre. Créez-en un ci-dessus.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {course.chapters.map((chapter, cIdx) => {
            const expanded = expandedChapters.has(chapter.id);
            const rForm = resourceForm[chapter.id] ?? { title: "", kind: "pdf" as ResourceKind, url: "" };
            return (
              <Card key={chapter.id}>
                <div
                  className="flex items-center gap-3 p-4 cursor-pointer hover:bg-accent/30"
                  onClick={() => toggleChapter(chapter.id)}
                >
                  {expanded ? (
                    <ChevronDown className="h-4 w-4 shrink-0" />
                  ) : (
                    <ChevronRight className="h-4 w-4 shrink-0" />
                  )}
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-bold">
                    {cIdx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold">{chapter.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {chapter.items_count} élément{chapter.items_count > 1 ? "s" : ""}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeChapter(chapter.id);
                    }}
                    className="p-2 text-muted-foreground hover:text-red-600"
                    title="Supprimer le chapitre"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                {expanded && (
                  <div className="border-t bg-muted/20 p-4 space-y-4">
                    {/* Items list (resources + quizzes) */}
                    <div className="space-y-1.5">
                      {chapter.items.length === 0 && (
                        <div className="text-xs text-muted-foreground italic px-1">
                          Aucun fichier ni quiz. Ajoutez-en ci-dessous.
                        </div>
                      )}
                      {chapter.items.map((item, iIdx) =>
                        item.item_type === "resource" ? (
                          <ResourceRow
                            key={item.id}
                            item={item}
                            index={iIdx}
                            onDelete={() => removeResource(item.id)}
                          />
                        ) : (
                          <QuizRow
                            key={item.id}
                            item={item}
                            index={iIdx}
                            expanded={expandedQuizzes.has(item.id)}
                            quiz={quizDetails[item.id]}
                            form={
                              quizQuestionForm[item.id] ?? {
                                text: "",
                                choices: [
                                  { id: "a", text: "" },
                                  { id: "b", text: "" },
                                ],
                                correct: "a",
                              }
                            }
                            onToggle={() => toggleQuiz(item.id)}
                            onDelete={() => removeQuiz(item.id)}
                            onFormChange={(form) =>
                              setQuizQuestionForm((s) => ({ ...s, [item.id]: form }))
                            }
                            onAddQuestion={() => addQuestion(item.id)}
                            onRemoveQuestion={(qid) => removeQuestion(item.id, qid)}
                          />
                        )
                      )}
                    </div>

                    {/* Add new resource */}
                    <div className="rounded-lg border bg-card p-3 space-y-2">
                      <div className="text-xs font-semibold uppercase text-muted-foreground">
                        Ajouter un fichier
                      </div>
                      <div className="grid grid-cols-12 gap-2">
                        <select
                          value={rForm.kind}
                          onChange={(e) =>
                            setResourceForm((s) => ({
                              ...s,
                              [chapter.id]: { ...rForm, kind: e.target.value as ResourceKind },
                            }))
                          }
                          className="col-span-3 h-9 rounded-md border bg-background px-2 text-sm"
                        >
                          {RESOURCE_KINDS.map((k) => (
                            <option key={k.value} value={k.value}>
                              {k.label}
                            </option>
                          ))}
                        </select>
                        <Input
                          className="col-span-4 h-9"
                          placeholder="Titre"
                          value={rForm.title}
                          onChange={(e) =>
                            setResourceForm((s) => ({
                              ...s,
                              [chapter.id]: { ...rForm, title: e.target.value },
                            }))
                          }
                        />
                        <Input
                          className="col-span-4 h-9"
                          placeholder="URL ou importer →"
                          value={rForm.url}
                          onChange={(e) =>
                            setResourceForm((s) => ({
                              ...s,
                              [chapter.id]: { ...rForm, url: e.target.value },
                            }))
                          }
                        />
                        <Button
                          size="sm"
                          onClick={() => addResource(chapter)}
                          disabled={!rForm.title || !rForm.url}
                          className="col-span-1 h-9 px-0"
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <label className="inline-flex items-center gap-1 cursor-pointer rounded-md border px-2 py-1 hover:bg-accent">
                          <Paperclip className="h-3 w-3" />
                          <input
                            type="file"
                            accept=".pdf,.mp4,.webm,.mov,.mkv,.avi,.png,.jpg,.jpeg,.gif,.webp"
                            className="hidden"
                            onChange={(e) => {
                              const f = e.target.files?.[0];
                              if (f) handleFileUpload(chapter, f);
                              e.target.value = "";
                            }}
                            disabled={uploadingChapter[chapter.id]}
                          />
                          {uploadingChapter[chapter.id]
                            ? "Envoi en cours..."
                            : "Importer un fichier (PDF / vidéo)"}
                        </label>
                        {uploadError[chapter.id] && (
                          <span className="text-red-600">{uploadError[chapter.id]}</span>
                        )}
                      </div>
                    </div>

                    {/* Add quiz button */}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => addQuiz(chapter)}
                      className="w-full"
                    >
                      <HelpCircle className="h-3.5 w-3.5 mr-2" /> Ajouter un quiz
                    </Button>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ResourceRow({
  item,
  index,
  onDelete,
}: {
  item: Extract<ChapterItem, { item_type: "resource" }>;
  index: number;
  onDelete: () => void;
}) {
  const Icon = KIND_ICON[item.kind] ?? FileText;
  return (
    <div className="flex items-center gap-2 rounded-md border bg-card px-3 py-2 text-sm">
      <span className="text-xs text-muted-foreground w-6 shrink-0">{index + 1}.</span>
      <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
      <span className="flex-1 line-clamp-1">{item.title}</span>
      <span className="text-xs text-muted-foreground capitalize">{item.kind}</span>
      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-primary hover:underline"
      >
        Voir
      </a>
      <button onClick={onDelete} className="text-muted-foreground hover:text-red-600">
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

interface QuizRowProps {
  item: Extract<ChapterItem, { item_type: "quiz" }>;
  index: number;
  expanded: boolean;
  quiz?: QuizAdmin;
  form: { text: string; choices: { id: string; text: string }[]; correct: string };
  onToggle: () => void;
  onDelete: () => void;
  onFormChange: (form: { text: string; choices: { id: string; text: string }[]; correct: string }) => void;
  onAddQuestion: () => void;
  onRemoveQuestion: (questionId: string) => void;
}

function QuizRow({
  item,
  index,
  expanded,
  quiz,
  form,
  onToggle,
  onDelete,
  onFormChange,
  onAddQuestion,
  onRemoveQuestion,
}: QuizRowProps) {
  return (
    <div className="rounded-md border bg-card">
      <div className="flex items-center gap-2 px-3 py-2 text-sm">
        <span className="text-xs text-muted-foreground w-6 shrink-0">{index + 1}.</span>
        <HelpCircle className="h-4 w-4 text-primary shrink-0" />
        <span className="flex-1 line-clamp-1">{item.title}</span>
        <span className="text-xs text-muted-foreground">
          {item.question_count} question{item.question_count > 1 ? "s" : ""}
        </span>
        <button onClick={onToggle} className="text-xs text-primary hover:underline">
          {expanded ? "Masquer" : "Éditer"}
        </button>
        <button onClick={onDelete} className="text-muted-foreground hover:text-red-600">
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
      {expanded && (
        <div className="border-t p-3">
          {quiz ? (
            <QuizEditor
              quiz={quiz}
              form={form}
              onFormChange={onFormChange}
              onAdd={onAddQuestion}
              onRemove={onRemoveQuestion}
            />
          ) : (
            <div className="text-xs text-muted-foreground italic">Chargement du quiz...</div>
          )}
        </div>
      )}
    </div>
  );
}

interface QuizEditorProps {
  quiz: QuizAdmin;
  form: { text: string; choices: { id: string; text: string }[]; correct: string };
  onFormChange: (form: { text: string; choices: { id: string; text: string }[]; correct: string }) => void;
  onAdd: () => void;
  onRemove: (questionId: string) => void;
}

function QuizEditor({ quiz, form, onFormChange, onAdd, onRemove }: QuizEditorProps) {
  const addChoice = () => {
    const nextId = String.fromCharCode(97 + form.choices.length);
    onFormChange({ ...form, choices: [...form.choices, { id: nextId, text: "" }] });
  };

  const removeChoice = (id: string) => {
    if (form.choices.length <= 2) return;
    const newChoices = form.choices.filter((c) => c.id !== id);
    onFormChange({
      ...form,
      choices: newChoices,
      correct: form.correct === id ? newChoices[0].id : form.correct,
    });
  };

  return (
    <div className="space-y-3 rounded-lg bg-muted/10 p-3">
      <div className="space-y-2">
        {quiz.questions.length === 0 && (
          <div className="text-xs text-muted-foreground italic">Aucune question.</div>
        )}
        {quiz.questions.map((q, idx) => (
          <div key={q.id} className="rounded-md border bg-card p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 space-y-1">
                <div className="text-sm font-medium">
                  <span className="text-primary mr-1">Q{idx + 1}.</span>
                  {q.text}
                </div>
                <ul className="text-xs text-muted-foreground space-y-0.5 ml-4">
                  {q.choices.map((c: { id: string; text: string }) => (
                    <li
                      key={c.id}
                      className={c.id === q.correct_choice_id ? "text-green-600 font-medium" : ""}
                    >
                      {c.id === q.correct_choice_id ? "✓ " : "• "}
                      {c.text}
                    </li>
                  ))}
                </ul>
              </div>
              <button
                onClick={() => onRemove(q.id)}
                className="text-muted-foreground hover:text-red-600"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-md border bg-background p-3 space-y-2">
        <Label className="text-xs">Nouvelle question</Label>
        <Input
          placeholder="Énoncé de la question"
          value={form.text}
          onChange={(e) => onFormChange({ ...form, text: e.target.value })}
        />
        <div className="space-y-1.5">
          {form.choices.map((c) => (
            <div key={c.id} className="flex items-center gap-2">
              <input
                type="radio"
                checked={form.correct === c.id}
                onChange={() => onFormChange({ ...form, correct: c.id })}
                className="h-4 w-4 accent-primary"
              />
              <span className="text-xs font-mono text-muted-foreground w-4">{c.id}</span>
              <Input
                placeholder={`Choix ${c.id.toUpperCase()}`}
                value={c.text}
                onChange={(e) =>
                  onFormChange({
                    ...form,
                    choices: form.choices.map((x) =>
                      x.id === c.id ? { ...x, text: e.target.value } : x
                    ),
                  })
                }
                className="h-8 text-sm"
              />
              {form.choices.length > 2 && (
                <button
                  onClick={() => removeChoice(c.id)}
                  className="text-muted-foreground hover:text-red-600"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between items-center">
          <Button variant="outline" size="sm" onClick={addChoice}>
            <Plus className="h-3 w-3 mr-1" /> Ajouter un choix
          </Button>
          <Button
            size="sm"
            onClick={onAdd}
            disabled={
              !form.text ||
              form.choices.some((c) => !c.text.trim()) ||
              !form.correct
            }
          >
            <Plus className="h-3 w-3 mr-1" /> Ajouter la question
          </Button>
        </div>
      </div>
    </div>
  );
}
