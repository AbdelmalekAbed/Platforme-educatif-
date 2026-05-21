"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import type { Quiz, QuizAttempt } from "@/types";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Award, RotateCcw } from "lucide-react";

interface QuizRunnerProps {
  quizId: string;
  onCompleted?: (attempt: QuizAttempt) => void;
}

type ViewState = "intro" | "running" | "result";

export function QuizRunner({ quizId, onCompleted }: QuizRunnerProps) {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [view, setView] = useState<ViewState>("intro");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<QuizAttempt | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .getQuizForStudent(quizId)
      .then(setQuiz)
      .catch((e) => setError(e instanceof Error ? e.message : "Erreur"))
      .finally(() => setLoading(false));
  }, [quizId]);

  const start = () => {
    setAnswers({});
    setResult(null);
    setView("running");
  };

  const submit = async () => {
    if (!quiz) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload = quiz.questions.map((q) => ({
        question_id: q.id,
        choice_id: answers[q.id] ?? "",
      }));
      const attempt = await api.submitQuiz(quizId, payload);
      setResult(attempt);
      setView("result");
      onCompleted?.(attempt);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors de l'envoi");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl border bg-muted/20 py-16 text-center">
        <div className="animate-pulse text-muted-foreground">Chargement du quiz...</div>
      </div>
    );
  }

  if (error && !quiz) {
    return (
      <div className="rounded-xl border bg-red-50 border-red-200 py-8 text-center text-red-700">
        {error}
      </div>
    );
  }

  if (!quiz) return null;

  if (view === "intro") {
    return (
      <div className="rounded-xl border bg-gradient-to-br from-primary/5 to-background py-16 text-center">
        <h3 className="text-3xl font-bold">{quiz.title}</h3>
        {quiz.instructions && (
          <p className="mt-3 text-muted-foreground">{quiz.instructions}</p>
        )}
        <div className="mt-2 text-sm text-muted-foreground">
          {quiz.questions.length} questions • Note de passage: {quiz.pass_score}%
        </div>
        <Button size="lg" className="mt-6" onClick={start} disabled={!quiz.questions.length}>
          {quiz.questions.length ? "Prêt pour commencer" : "Aucune question disponible"}
        </Button>
      </div>
    );
  }

  if (view === "result" && result) {
    const passed = result.score >= quiz.pass_score;
    return (
      <div className="rounded-xl border bg-gradient-to-br from-primary/5 to-background py-12 px-6 text-center">
        <div
          className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full ${
            passed ? "bg-green-100 text-green-600" : "bg-orange-100 text-orange-600"
          }`}
        >
          <Award className="h-8 w-8" />
        </div>
        <h3 className="mt-4 text-2xl font-bold">
          {passed ? "Félicitations !" : "Encore un effort !"}
        </h3>
        <div className="mt-2 text-5xl font-bold text-primary">
          {Math.round(result.score)}%
        </div>
        <p className="mt-1 text-muted-foreground">
          {result.correct_count} / {result.total_count} réponses correctes
        </p>

        <div className="mt-6 max-w-xl mx-auto space-y-2 text-left">
          {quiz.questions.map((q, i) => {
            const ans = result.answers.find((a) => a.question_id === q.id);
            const correct = ans?.is_correct ?? false;
            return (
              <div
                key={q.id}
                className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${
                  correct
                    ? "bg-green-50 border-green-200"
                    : "bg-red-50 border-red-200"
                }`}
              >
                {correct ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />
                )}
                <div>
                  <div className="font-medium">
                    Q{i + 1}. {q.text}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <Button variant="outline" className="mt-6" onClick={start}>
          <RotateCcw className="h-4 w-4 mr-2" />
          Recommencer
        </Button>
      </div>
    );
  }

  // running
  const allAnswered = quiz.questions.every((q) => answers[q.id]);
  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-muted/30 p-3 text-sm flex items-center justify-between">
        <span className="font-medium">{quiz.title}</span>
        <span className="text-muted-foreground">
          {Object.keys(answers).length} / {quiz.questions.length} répondues
        </span>
      </div>
      {quiz.questions.map((q, i) => (
        <div key={q.id} className="rounded-xl border bg-card p-5">
          <div className="font-medium">
            <span className="text-primary mr-2">Q{i + 1}.</span> {q.text}
          </div>
          <div className="mt-3 space-y-2">
            {q.choices.map((c) => {
              const selected = answers[q.id] === c.id;
              return (
                <label
                  key={c.id}
                  className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 text-sm transition-colors ${
                    selected
                      ? "border-primary bg-primary/5"
                      : "hover:bg-accent"
                  }`}
                >
                  <input
                    type="radio"
                    name={q.id}
                    checked={selected}
                    onChange={() => setAnswers((a) => ({ ...a, [q.id]: c.id }))}
                    className="h-4 w-4 accent-primary"
                  />
                  <span>{c.text}</span>
                </label>
              );
            })}
          </div>
        </div>
      ))}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      <div className="flex justify-end">
        <Button size="lg" onClick={submit} disabled={!allAnswered || submitting}>
          {submitting ? "Envoi..." : "Terminer le quiz"}
        </Button>
      </div>
    </div>
  );
}
