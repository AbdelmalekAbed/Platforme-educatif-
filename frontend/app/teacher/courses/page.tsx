"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { Subject } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LevelCatalog } from "@/components/learning/level-catalog";

export default function TeacherCoursesPage() {
  const { isAuthenticated } = useAuthStore();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", subject: "", grade_level: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!isAuthenticated) return;
    api.getSubjects().then(setSubjects).catch(console.error);
  }, [isAuthenticated]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await api.createCourse(form);
      setForm({ title: "", description: "", subject: "", grade_level: "" });
      setShowForm(false);
      // Force LevelCatalog to refetch counts after a new course is created.
      setReloadKey((k) => k + 1);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Créer un cours</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label>Titre du cours</Label>
                <Input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  required
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Matière</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={form.subject}
                    onChange={(e) => setForm({ ...form, subject: e.target.value })}
                  >
                    <option value="">-- Sélectionner une matière --</option>
                    {subjects.map((s) => (
                      <option key={s.id} value={s.name}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Niveau</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={form.grade_level ?? ""}
                    onChange={(e) => setForm({ ...form, grade_level: e.target.value })}
                    required
                  >
                    <option value="">-- Sélectionner un niveau --</option>
                    <option value="6eme">6ème</option>
                    <option value="5eme">5ème</option>
                    <option value="4eme">4ème</option>
                    <option value="3eme">3ème</option>
                  </select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <textarea
                  className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "Création..." : "Créer le cours"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <LevelCatalog
        key={reloadKey}
        title="Mes cours"
        subtitle="Choisissez un niveau pour voir vos cours"
        levelHrefBase="/teacher/courses/level"
        action={
          <Button onClick={() => setShowForm((s) => !s)}>
            {showForm ? "Annuler" : "+ Nouveau Cours"}
          </Button>
        }
      />
    </div>
  );
}
