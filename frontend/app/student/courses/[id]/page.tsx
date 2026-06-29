"use client";

import { useParams } from "next/navigation";
import { CourseProgram } from "@/components/learning/course-program";

export default function StudentCoursePage() {
  const params = useParams<{ id: string }>();
  const courseId = params.id;

  return (
    <CourseProgram
      courseId={courseId}
      backHref={(course) => `/student/catalog/${course?.grade_level ?? ""}`}
      chapterHref={(cId, chId) => `/student/courses/${cId}/chapters/${chId}`}
      showKnownActions
    />
  );
}
