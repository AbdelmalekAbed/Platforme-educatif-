"use client";

import { useParams } from "next/navigation";
import { CourseProgram } from "@/components/learning/course-program";

export default function TeacherCourseContentPage() {
  const params = useParams<{ id: string }>();
  const courseId = params.id;

  return (
    <CourseProgram
      courseId={courseId}
      backHref={(course) =>
        course?.grade_level
          ? `/teacher/courses/level/${course.grade_level}`
          : "/teacher/courses"
      }
      chapterHref={(cId, chId) => `/teacher/courses/${cId}/chapters/${chId}`}
      hideProgress
    />
  );
}
