"use client";

import { useParams } from "next/navigation";
import { CourseContentEditor } from "@/components/learning/course-content-editor";

export default function TeacherCourseContentPage() {
  const params = useParams<{ id: string }>();
  return (
    <CourseContentEditor
      courseId={params.id}
      backHref={(course) =>
        course?.grade_level
          ? `/teacher/courses/level/${course.grade_level}`
          : "/teacher/courses"
      }
      backLabel="Retour au niveau"
    />
  );
}
