"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import type { User } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [roleFilter, setRoleFilter] = useState<string>("");

  useEffect(() => {
    api.getUsers(roleFilter || undefined).then(setUsers).catch(console.error);
  }, [roleFilter]);

  const handleToggle = async (userId: string) => {
    await api.toggleUserActive(userId);
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, is_active: !u.is_active } : u))
    );
  };

  const roleLabels: Record<string, string> = {
    admin: "Admin",
    teacher: "Professeur",
    student: "Élève",
    vendor: "Vendeur",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Gestion des Utilisateurs</h1>
        <div className="flex gap-2">
          {["", "student", "teacher", "vendor", "admin"].map((role) => (
            <Button
              key={role}
              variant={roleFilter === role ? "default" : "outline"}
              size="sm"
              onClick={() => setRoleFilter(role)}
            >
              {role === "" ? "Tous" : roleLabels[role]}
            </Button>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Utilisateurs ({users.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="pb-3 font-medium">Nom</th>
                  <th className="pb-3 font-medium">Email</th>
                  <th className="pb-3 font-medium">Rôle</th>
                  <th className="pb-3 font-medium">Statut</th>
                  <th className="pb-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b">
                    <td className="py-3">
                      {user.first_name} {user.last_name}
                    </td>
                    <td className="py-3">{user.email}</td>
                    <td className="py-3">
                      <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                        {roleLabels[user.role]}
                      </span>
                    </td>
                    <td className="py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${
                          user.is_active
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {user.is_active ? "Actif" : "Inactif"}
                      </span>
                    </td>
                    <td className="py-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleToggle(user.id)}
                      >
                        {user.is_active ? "Désactiver" : "Activer"}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
