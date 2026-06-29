// ---- Roles ----
export type Role = "admin" | "teacher" | "student" | "vendor";

// ---- Subject ----
export interface Subject {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

// ---- User ----
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: Role;
  is_active: boolean;
  is_verified: boolean;
  avatar_url?: string;
  created_at: string;
}

// ---- Auth ----
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: Role;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ---- Course ----
export interface Course {
  id: string;
  teacher_id: string;
  title: string;
  description?: string;
  subject?: string;
  grade_level?: string;
  max_students?: number;
  price?: number;
  is_active: boolean;
  thumbnail_url?: string;
  created_at: string;
}

export interface AdminCourse extends Course {
  teacher_name: string;
  teacher_email: string;
}

export interface CourseSession {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  scheduled_at: string;
  duration_minutes: number;
  status: "scheduled" | "live" | "completed" | "cancelled";
  room_id?: string;
  started_at?: string;
  ended_at?: string;
  created_at: string;
}

// ---- Homework ----
export interface Homework {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  due_date?: string;
  max_grade: number;
  attachment_url?: string;
  is_published: boolean;
  created_at: string;
}

export interface HomeworkSubmission {
  id: string;
  homework_id: string;
  student_id: string;
  content?: string;
  attachment_url?: string;
  grade?: number;
  feedback?: string;
  submitted_at: string;
  graded_at?: string;
  status: "submitted" | "graded" | "returned";
}

// ---- Attendance ----
export interface Attendance {
  id: string;
  session_id: string;
  student_id: string;
  status: "present" | "absent" | "late" | "excused";
  joined_at?: string;
  left_at?: string;
  auto_marked: boolean;
  created_at: string;
}

// ---- Payment ----
export interface Payment {
  id: string;
  student_id: string;
  amount: number;
  currency: string;
  status: "pending" | "completed" | "failed" | "refunded";
  payment_method?: string;
  transaction_id?: string;
  description?: string;
  created_at: string;
  paid_at?: string;
}

// ---- Notification ----
export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message?: string;
  type: "info" | "warning" | "success" | "error";
  is_read: boolean;
  link?: string;
  created_at: string;
}

// ---- Admin Stats ----
export interface PlatformStats {
  total_users: number;
  total_students: number;
  total_teachers: number;
  total_courses: number;
  total_enrollments: number;
  total_revenue: number;
}

// ---- Platform settings ----
export interface PlatformSection {
  name: string;
  description: string;
  support_email?: string | null;
  default_language: "fr" | "en" | "ar";
  timezone: string;
}

export interface SignupsSection {
  public_signup_open: boolean;
  require_email_verification: boolean;
  default_role: "student" | "teacher";
  auto_approve_teachers: boolean;
  require_invite_for_teachers: boolean;
}

export interface SecuritySection {
  session_timeout_minutes: number;
  password_min_length: number;
  require_mfa_for_admins: boolean;
  max_login_attempts: number;
}

export interface NotificationsSection {
  email_notifications_global: boolean;
  notify_on_new_signup: boolean;
  notify_on_payment: boolean;
  notify_on_assignment_due: boolean;
  weekly_digest: boolean;
}

export interface CoursesSection {
  default_pass_score: number;
  video_max_size_mb: number;
  auto_archive_after_days: number;
  allow_student_course_rating: boolean;
}

export interface AppearanceSection {
  accent_color: string;
  default_theme: "light" | "dark" | "system";
}

export interface PlatformSettings {
  platform: PlatformSection;
  signups: SignupsSection;
  security: SecuritySection;
  notifications: NotificationsSection;
  courses: CoursesSection;
  appearance: AppearanceSection;
}

export type SettingsSectionKey = keyof PlatformSettings;

export interface PublicSettings {
  name: string;
  description: string;
  support_email?: string | null;
  default_language: string;
  public_signup_open: boolean;
}

// ---- Course content ----

export type ResourceKind = "video" | "pdf" | "exercise" | "correction" | "fiche";

export interface Chapter {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  position: number;
  created_at: string;
}

export interface ChapterResource {
  id: string;
  chapter_id: string;
  title: string;
  kind: ResourceKind;
  url: string;
  duration_seconds?: number;
  position: number;
  created_at: string;
}

export interface ChapterItemResource {
  item_type: "resource";
  id: string;
  title: string;
  kind: ResourceKind;
  url: string;
  duration_seconds?: number;
  position: number;
  is_completed: boolean;
}

export interface ChapterItemQuiz {
  item_type: "quiz";
  id: string;
  title: string;
  pass_score: number;
  position: number;
  question_count: number;
  is_completed: boolean;
}

export type ChapterItem = ChapterItemResource | ChapterItemQuiz;

export interface ChapterWithItems {
  id: string;
  course_id?: string;
  title: string;
  description?: string;
  position: number;
  items_count: number;
  items: ChapterItem[];
  is_known?: boolean;
}

export interface CourseFull {
  id: string;
  title: string;
  description?: string;
  subject?: string;
  grade_level?: string;
  thumbnail_url?: string;
  teacher_id: string;
  teacher_name: string;
  progress_percent: number;
  is_known?: boolean;
  chapters: ChapterWithItems[];
}

export interface LevelInfo {
  code: string;
  label: string;
  course_count: number;
}

export interface CourseListItem {
  id: string;
  title: string;
  description?: string;
  subject?: string;
  grade_level?: string;
  thumbnail_url?: string;
  teacher_id?: string;
  teacher_name: string;
  created_at: string;
  progress_percent: number;
  is_known?: boolean;
  is_active?: boolean;
}

export interface CoursesByLevelResponse {
  items: CourseListItem[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
  level_progress_percent: number;
}

export interface TeacherDashboardCourse {
  id: string;
  title: string;
  description?: string | null;
  subject?: string | null;
  grade_level?: string | null;
  is_active: boolean;
  chapter_count: number;
  student_count: number;
  avg_progress: number | null;
}

export interface TeacherDashboard {
  total_courses: number;
  total_students: number;
  upcoming_sessions: number;
  active_homework: number;
  courses: TeacherDashboardCourse[];
}

// ---- Quiz ----

export interface QuizChoice {
  id: string;
  text: string;
}

export interface QuizQuestionStudent {
  id: string;
  text: string;
  choices: QuizChoice[];
  points: number;
  position: number;
}

export interface QuizQuestionAdmin extends QuizQuestionStudent {
  quiz_id: string;
  correct_choice_id: string;
  explanation?: string;
}

export interface Quiz {
  id: string;
  chapter_id: string;
  title: string;
  instructions?: string;
  pass_score: number;
  position: number;
  questions: QuizQuestionStudent[];
}

export interface QuizAdmin extends Omit<Quiz, "questions"> {
  questions: QuizQuestionAdmin[];
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  student_id: string;
  score: number;
  correct_count: number;
  total_count: number;
  answers: Array<{
    question_id: string;
    choice_id: string;
    is_correct: boolean;
  }>;
  completed_at: string;
}
