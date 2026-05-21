"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/auth";
import type { Subject } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminSubjectsPage() {
  const { isAuthenticated } = useAuthStore();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [newName, setNewName] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) return;
    loadSubjects();
  }, [isAuthenticated]);

  const loadSubjects = () => {
    api.getAdminSubjects().then(setSubjects).catch(console.error);
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    setIsAdding(true);
    setError("");
    try {
      await api.createSubject(name);
      setNewName("");
      loadSubjects();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'ajout");
    } finally {
      setIsAdding(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Supprimer cette matière ?")) return;
    setError("");
    try {
      await api.deleteSubject(id);
      loadSubjects();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erreur lors de la suppression");
    }
  };

  const handleToggle = async (id: string) => {
    try {
      await api.toggleSubjectActive(id);
      loadSubjects();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Gestion des Matières</h1>
        <p className="text-muted-foreground">
          Ajoutez ou gérez les matières disponibles pour les cours.
        </p>
      </div>

      {/* Add Subject Form */}
      <Card>
        <CardHeader>
          <CardTitle>Ajouter une matière</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="flex gap-3 items-end">
            <div className="flex-1 space-y-2">
              <Label>Nom de la matière</Label>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Ex: Mathématiques, Physique..."
                required
              />
            </div>
            <Button type="submit" disabled={isAdding}>
              {isAdding ? "Ajout..." : "Ajouter"}
            </Button>
          </form>
          {error && (
            <p className="mt-2 text-sm text-red-500">{error}</p>
          )}
        </CardContent>
      </Card>

      {/* Subjects List */}
      <Card>
        <CardHeader>
          <CardTitle>Matières ({subjects.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {subjects.length === 0 ? (
            <p className="text-muted-foreground text-sm">Aucune matière enregistrée.</p>
          ) : (
            <div className="divide-y">
              {subjects.map((subject) => (
                <div
                  key={subject.id}
                  className="flex items-center justify-between py-3"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`inline-block w-2 h-2 rounded-full ${
                        subject.is_active ? "bg-green-500" : "bg-gray-300"
                      }`}
                    />
                    <span
                      className={
                        subject.is_active ? "font-medium" : "text-muted-foreground line-through"
                      }
                    >
                      {subject.name}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggle(subject.id)}
                    >
                      {subject.is_active ? "Désactiver" : "Activer"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-500 hover:text-red-600"
                      onClick={() => handleDelete(subject.id)}
                    >
                      Supprimer
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
