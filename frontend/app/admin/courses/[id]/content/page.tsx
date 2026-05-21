"use client";

import { useParams } from "next/navigation";
import { CourseContentEditor } from "@/components/learning/course-content-editor";

export default function AdminCourseContentPage() {
  const params = useParams<{ id: string }>();
  return (
    <CourseContentEditor
      courseId={params.id}
      backHref={(course) =>
        course?.grade_level
          ? `/admin/courses/level/${course.grade_level}`
          : "/admin/courses"
      }
      backLabel="Retour au niveau"
    />
  );
}
