"use client";

import { useParams } from "next/navigation";

import { LessonPlayer } from "@/components/learning/lesson-player";

export default function StudentChapterDetailPage() {
  const params = useParams<{ id: string; chapterId: string }>();
  const courseId = params.id;
  const chapterId = params.chapterId;

  return (
    <LessonPlayer
      courseId={courseId}
      chapterId={chapterId}
      backHref={`/student/courses/${courseId}`}
      chapterHref={(cId, chId) => `/student/courses/${cId}/chapters/${chId}`}
      coursesHomeHref="/student/courses"
      role="student"
    />
  );
}
