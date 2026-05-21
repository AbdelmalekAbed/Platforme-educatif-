"use client";

import { useEffect, useState } from "react";
import { api } from "@/services/api";
import type { Course, Notification } from "@/types";
import { StatsCard } from "@/components/dashboard/stats-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, Video, ClipboardList, CreditCard, Bell } from "lucide-react";

export default function StudentDashboard() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    api.getCourses().then(setCourses).catch(console.error);
    api.getNotifications(true).then(setNotifications).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Mon Espace Élève</h1>
        <p className="text-muted-foreground">Suivez vos cours et votre progression</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Mes Cours" value={courses.length} icon={BookOpen} />
        <StatsCard title="Rediffusions" value="—" icon={Video} />
        <StatsCard title="Devoirs" value="—" icon={ClipboardList} />
        <StatsCard title="Notifications" value={notifications.length} icon={Bell} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Mes Cours</CardTitle>
          </CardHeader>
          <CardContent>
            {courses.length === 0 ? (
              <p className="text-muted-foreground">Aucun cours inscrit</p>
            ) : (
              <div className="space-y-3">
                {courses.map((course) => (
                  <div
                    key={course.id}
                    className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent"
                  >
                    <div>
                      <p className="font-medium">{course.title}</p>
                      <p className="text-sm text-muted-foreground">{course.subject}</p>
                    </div>
                    <span className="text-xs rounded-full bg-primary/10 px-2 py-1 text-primary">
                      {course.is_active ? "Actif" : "Terminé"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notifications récentes</CardTitle>
          </CardHeader>
          <CardContent>
            {notifications.length === 0 ? (
              <p className="text-muted-foreground">Aucune notification</p>
            ) : (
              <div className="space-y-3">
                {notifications.slice(0, 5).map((notif) => (
                  <div key={notif.id} className="flex items-start gap-3 rounded-lg border p-3">
                    <Bell className="mt-0.5 h-4 w-4 text-primary" />
                    <div>
                      <p className="font-medium text-sm">{notif.title}</p>
                      <p className="text-xs text-muted-foreground">{notif.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
