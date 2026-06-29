"use client";

import { useParams } from "next/navigation";
import { LessonPlayer } from "@/components/learning/lesson-player";

export default function TeacherChapterDetailPage() {
  const params = useParams<{ id: string; chapterId: string }>();
  const courseId = params.id;
  const chapterId = params.chapterId;

  return (
    <LessonPlayer
      courseId={courseId}
      chapterId={chapterId}
      backHref={`/teacher/courses/${courseId}/content`}
      chapterHref={(cId, chId) => `/teacher/courses/${cId}/chapters/${chId}`}
      coursesHomeHref="/teacher/courses"
      role="teacher"
    />
  );
}
