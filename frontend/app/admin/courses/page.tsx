"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { AdminCourse, Subject, User } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus } from "lucide-react";
import { LevelCatalog } from "@/components/learning/level-catalog";

export default function AdminCoursesPage() {
  const { isAuthenticated } = useAuthStore();
  const [courses, setCourses] = useState<AdminCourse[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [teachers, setTeachers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [form, setForm] = useState({
    teacher_id: "",
    title: "",
    description: "",
    subject: "",
    grade_level: "",
    max_students: "",
    price: "",
  });

  useEffect(() => {
    if (!isAuthenticated) return;
    loadSummary();
    api.getAdminSubjects().then(setSubjects).catch(console.error);
    api.getUsers("teacher").then(setTeachers).catch(console.error);
  }, [isAuthenticated]);

  const loadSummary = () => {
    api.getAdminCourses().then(setCourses).catch(console.error);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.teacher_id) {
      setError("Veuillez sélectionner un professeur.");
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      await api.adminCreateCourse({
        teacher_id: form.teacher_id,
        title: form.title,
        description: form.description || undefined,
        subject: form.subject || undefined,
        grade_level: form.grade_level || undefined,
        max_students: form.max_students ? parseInt(form.max_students) : undefined,
        price: form.price ? parseFloat(form.price) : 0,
      });
      setForm({
        teacher_id: "",
        title: "",
        description: "",
        subject: "",
        grade_level: "",
        max_students: "",
        price: "",
      });
      setShowForm(false);
      loadSummary();
      // Force LevelCatalog to refetch counts after a new course is created.
      setReloadKey((k) => k + 1);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur lors de la création");
    } finally {
      setIsLoading(false);
    }
  };

  const activeCourses = courses.filter((c) => c.is_active);
  const inactiveCourses = courses.filter((c) => !c.is_active);

  return (
    <div className="space-y-6">
      {/* Create Course Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Créer un cours</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Professeur *</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={form.teacher_id}
                    onChange={(e) => setForm({ ...form, teacher_id: e.target.value })}
                    required
                  >
                    <option value="">-- Sélectionner un professeur --</option>
                    {teachers.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.first_name} {t.last_name} ({t.email})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Titre du cours *</Label>
                  <Input
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    placeholder="Ex: Mathématiques Terminale"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Matière</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={form.subject}
                    onChange={(e) => setForm({ ...form, subject: e.target.value })}
                  >
                    <option value="">-- Sélectionner une matière --</option>
                    {subjects
                      .filter((s) => s.is_active)
                      .map((s) => (
                        <option key={s.id} value={s.name}>
                          {s.name}
                        </option>
                      ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Niveau *</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    value={form.grade_level}
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
                <div className="space-y-2">
                  <Label>Nombre max d&apos;élèves</Label>
                  <Input
                    type="number"
                    min={1}
                    value={form.max_students}
                    onChange={(e) => setForm({ ...form, max_students: e.target.value })}
                    placeholder="Ex: 30"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Prix (€)</Label>
                  <Input
                    type="number"
                    min={0}
                    step={0.01}
                    value={form.price}
                    onChange={(e) => setForm({ ...form, price: e.target.value })}
                    placeholder="0"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <textarea
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Description du cours..."
                />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "Création..." : "Créer le cours"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <LevelCatalog
        key={reloadKey}
        title="Gestion des cours"
        subtitle={`${courses.length} cours au total — ${activeCourses.length} actifs`}
        levelHrefBase="/admin/courses/level"
        action={
          <Button onClick={() => setShowForm((s) => !s)}>
            {showForm ? "Annuler" : (
              <span className="flex items-center gap-2">
                <Plus className="h-4 w-4" /> Nouveau Cours
              </span>
            )}
          </Button>
        }
        footer={
          <div className="grid gap-4 md:grid-cols-3 mt-8">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{courses.length}</div>
                <p className="text-sm text-muted-foreground">Total des cours</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-green-600">
                  {activeCourses.length}
                </div>
                <p className="text-sm text-muted-foreground">Cours actifs</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-red-500">
                  {inactiveCourses.length}
                </div>
                <p className="text-sm text-muted-foreground">Cours inactifs</p>
              </CardContent>
            </Card>
          </div>
        }
      />
    </div>
  );
}
