"use client";

import { LevelCatalog } from "@/components/learning/level-catalog";

export default function TeacherCoursesPage() {
  return (
    <div className="space-y-6">
      <LevelCatalog
        title="Mes cours"
        subtitle="Choisissez un niveau pour voir les cours qui vous sont assignés"
        levelHrefBase="/teacher/courses/level"
      />
    </div>
  );
}
