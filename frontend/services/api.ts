const API_BASE = "/api/v1";

class ApiClient {
  private accessToken: string | null =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  private refreshPromise: Promise<string | null> | null = null;
  private onAuthFailure: (() => void) | null = null;

  private getToken(): string | null {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("access_token");
      if (stored !== this.accessToken) this.accessToken = stored;
    }
    return this.accessToken;
  }

  setToken(token: string | null) {
    this.accessToken = token;
  }

  setOnAuthFailure(handler: (() => void) | null) {
    this.onAuthFailure = handler;
  }

  private async refreshAccessToken(): Promise<string | null> {
    if (typeof window === "undefined") return null;
    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) return null;
    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!response.ok) return null;
      const tokens: { access_token: string; refresh_token: string } = await response.json();
      this.accessToken = tokens.access_token;
      localStorage.setItem("access_token", tokens.access_token);
      localStorage.setItem("refresh_token", tokens.refresh_token);
      return tokens.access_token;
    } catch {
      return null;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    isRetry = false
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    // Auto-refresh on expired/missing access token, then retry the original request once.
    // FastAPI's HTTPBearer returns 403 when the header is missing, 401 when it's invalid.
    if (
      (response.status === 401 || response.status === 403) &&
      !isRetry &&
      !endpoint.startsWith("/auth/login") &&
      !endpoint.startsWith("/auth/refresh")
    ) {
      if (!this.refreshPromise) {
        this.refreshPromise = this.refreshAccessToken().finally(() => {
          this.refreshPromise = null;
        });
      }
      const newToken = await this.refreshPromise;
      if (newToken) {
        return this.request<T>(endpoint, options, true);
      }
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
      this.accessToken = null;
      this.onAuthFailure?.();
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return undefined as T;
    }
    return response.json();
  }

  // Auth
  login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    );
  }

  register(data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: string;
  }) {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  refreshToken(refresh_token: string) {
    return this.request<{ access_token: string; refresh_token: string }>(
      "/auth/refresh",
      { method: "POST", body: JSON.stringify({ refresh_token }) }
    );
  }

  getMe() {
    return this.request<import("@/types").User>("/auth/me");
  }

  // Courses
  getCourses() {
    return this.request<import("@/types").Course[]>("/courses/");
  }

  getTeacherDashboard() {
    return this.request<import("@/types").TeacherDashboard>("/courses/teacher-dashboard");
  }

  createCourse(data: { title: string; description?: string; subject?: string; grade_level?: string }) {
    return this.request<import("@/types").Course>("/courses/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  getCourse(id: string) {
    return this.request<import("@/types").Course>(`/courses/${id}`);
  }

  getCourseSessions(courseId: string) {
    return this.request<import("@/types").CourseSession[]>(
      `/courses/${courseId}/sessions`
    );
  }

  createSession(
    courseId: string,
    data: { title: string; scheduled_at: string; duration_minutes: number }
  ) {
    return this.request<import("@/types").CourseSession>(
      `/courses/${courseId}/sessions`,
      { method: "POST", body: JSON.stringify(data) }
    );
  }

  // Homework
  getHomework(courseId: string) {
    return this.request<import("@/types").Homework[]>(
      `/homework/course/${courseId}`
    );
  }

  createHomework(data: {
    course_id: string;
    title: string;
    description?: string;
    due_date?: string;
  }) {
    return this.request<import("@/types").Homework>("/homework/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  submitHomework(data: {
    homework_id: string;
    content?: string;
  }) {
    return this.request<import("@/types").HomeworkSubmission>("/homework/submit", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Attendance
  getSessionAttendance(sessionId: string) {
    return this.request<import("@/types").Attendance[]>(
      `/attendance/session/${sessionId}`
    );
  }

  // Notifications
  getNotifications(unreadOnly = false) {
    return this.request<import("@/types").Notification[]>(
      `/notifications/?unread_only=${unreadOnly}`
    );
  }

  markNotificationRead(id: string) {
    return this.request(`/notifications/${id}/read`, { method: "PUT" });
  }

  markAllNotificationsRead() {
    return this.request("/notifications/read-all", { method: "PUT" });
  }

  // Payments
  getStudentPayments(studentId: string) {
    return this.request<import("@/types").Payment[]>(
      `/payments/student/${studentId}`
    );
  }

  // Admin
  getStats() {
    return this.request<import("@/types").PlatformStats>("/admin/stats");
  }

  getUsers(role?: string, limit?: number) {
    const params = new URLSearchParams();
    if (role) params.set("role", role);
    if (limit !== undefined) params.set("limit", String(limit));
    const query = params.toString() ? `?${params.toString()}` : "";
    return this.request<import("@/types").User[]>(`/admin/users${query}`);
  }

  toggleUserActive(userId: string) {
    return this.request(`/admin/users/${userId}/toggle-active`, {
      method: "PUT",
    });
  }

  // Platform settings
  getSettings() {
    return this.request<import("@/types").PlatformSettings>("/admin/settings");
  }

  updateSettings<K extends import("@/types").SettingsSectionKey>(
    section: K,
    data: import("@/types").PlatformSettings[K]
  ) {
    return this.request<import("@/types").PlatformSettings[K]>(
      `/admin/settings/${section}`,
      { method: "PUT", body: JSON.stringify(data) }
    );
  }

  getPublicSettings() {
    return this.request<import("@/types").PublicSettings>("/public/settings");
  }

  // Subjects
  getSubjects() {
    return this.request<import("@/types").Subject[]>("/courses/subjects");
  }

  getAdminSubjects() {
    return this.request<import("@/types").Subject[]>("/admin/subjects");
  }

  createSubject(name: string) {
    return this.request<import("@/types").Subject>("/admin/subjects", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  }

  deleteSubject(id: string) {
    return this.request(`/admin/subjects/${id}`, { method: "DELETE" });
  }

  toggleSubjectActive(id: string) {
    return this.request<import("@/types").Subject>(
      `/admin/subjects/${id}/toggle`,
      { method: "PUT" }
    );
  }

  // Admin Courses
  getAdminCourses() {
    return this.request<import("@/types").AdminCourse[]>("/admin/courses");
  }

  adminCreateCourse(data: {
    teacher_id: string;
    title: string;
    description?: string;
    subject?: string;
    grade_level?: string;
    max_students?: number;
    price?: number;
  }) {
    return this.request<import("@/types").AdminCourse>("/admin/courses", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  adminToggleCourse(id: string) {
    return this.request<{ id: string; is_active: boolean }>(
      `/admin/courses/${id}/toggle`,
      { method: "PUT" }
    );
  }

  adminDeleteCourse(id: string) {
    return this.request(`/admin/courses/${id}`, { method: "DELETE" });
  }

  // ===== Course content =====

  // Levels & catalog
  getLevels() {
    return this.request<import("@/types").LevelInfo[]>("/content/levels");
  }

  getCoursesByLevel(level: string, skip = 0, limit = 4) {
    return this.request<import("@/types").CoursesByLevelResponse>(
      `/content/levels/${level}/courses?skip=${skip}&limit=${limit}`
    );
  }

  getCourseFull(courseId: string) {
    return this.request<import("@/types").CourseFull>(
      `/content/courses/${courseId}/full`
    );
  }

  // Chapters
  listChapters(courseId: string) {
    return this.request<import("@/types").Chapter[]>(
      `/content/courses/${courseId}/chapters`
    );
  }

  createChapter(courseId: string, data: { title: string; description?: string; position?: number }) {
    return this.request<import("@/types").Chapter>(
      `/content/courses/${courseId}/chapters`,
      { method: "POST", body: JSON.stringify({ position: 0, ...data }) }
    );
  }

  updateChapter(chapterId: string, data: Partial<{ title: string; description: string; position: number }>) {
    return this.request<import("@/types").Chapter>(`/content/chapters/${chapterId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  deleteChapter(chapterId: string) {
    return this.request(`/content/chapters/${chapterId}`, { method: "DELETE" });
  }

  reorderChapters(courseId: string, chapterIds: string[]) {
    return this.request(`/content/courses/${courseId}/chapters/reorder`, {
      method: "PATCH",
      body: JSON.stringify({ chapter_ids: chapterIds }),
    });
  }

  reorderChapterItems(chapterId: string, items: { type: "resource" | "quiz"; id: string }[]) {
    return this.request(`/content/chapters/${chapterId}/items/reorder`, {
      method: "PATCH",
      body: JSON.stringify({ items }),
    });
  }

  reorderQuizQuestions(quizId: string, questionIds: string[]) {
    return this.request(`/content/quizzes/${quizId}/questions/reorder`, {
      method: "PATCH",
      body: JSON.stringify({ question_ids: questionIds }),
    });
  }

  // Chapter detail (flat item list)
  getChapterWithItems(chapterId: string) {
    return this.request<import("@/types").ChapterWithItems>(
      `/content/chapters/${chapterId}`
    );
  }

  // Chapter resources (PDF / video / fiche / exercise / correction)
  listChapterResources(chapterId: string) {
    return this.request<import("@/types").ChapterResource[]>(
      `/content/chapters/${chapterId}/resources`
    );
  }

  createChapterResource(
    chapterId: string,
    data: {
      title: string;
      kind: import("@/types").ResourceKind;
      url: string;
      duration_seconds?: number;
      position?: number;
    }
  ) {
    return this.request<import("@/types").ChapterResource>(
      `/content/chapters/${chapterId}/resources`,
      { method: "POST", body: JSON.stringify({ position: 0, ...data }) }
    );
  }

  deleteResource(resourceId: string) {
    return this.request(`/content/resources/${resourceId}`, { method: "DELETE" });
  }

  markResourceCompleted(resourceId: string) {
    return this.request(`/content/resources/${resourceId}/complete`, { method: "POST" });
  }

  markCourseKnown(courseId: string) {
    return this.request(`/content/courses/${courseId}/known`, { method: "POST" });
  }

  unmarkCourseKnown(courseId: string) {
    return this.request(`/content/courses/${courseId}/known`, { method: "DELETE" });
  }

  markChapterKnown(chapterId: string) {
    return this.request(`/content/chapters/${chapterId}/known`, { method: "POST" });
  }

  unmarkChapterKnown(chapterId: string) {
    return this.request(`/content/chapters/${chapterId}/known`, { method: "DELETE" });
  }

  async uploadFile(file: File): Promise<{ url: string; kind: string; filename: string; size: number }> {
    const doUpload = async (token: string | null) => {
      const form = new FormData();
      form.append("file", file);
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;
      return fetch(`${API_BASE}/content/uploads`, { method: "POST", headers, body: form });
    };
    let response = await doUpload(this.getToken());
    if (response.status === 401 || response.status === 403) {
      if (!this.refreshPromise) {
        this.refreshPromise = this.refreshAccessToken().finally(() => {
          this.refreshPromise = null;
        });
      }
      const newToken = await this.refreshPromise;
      if (newToken) response = await doUpload(newToken);
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  // Quiz - admin/teacher
  createQuiz(chapterId: string, data: { title?: string; instructions?: string; pass_score?: number; position?: number }) {
    return this.request<import("@/types").QuizAdmin>(
      `/content/chapters/${chapterId}/quizzes`,
      { method: "POST", body: JSON.stringify({ position: 0, ...data }) }
    );
  }

  getQuizAdmin(quizId: string) {
    return this.request<import("@/types").QuizAdmin>(`/content/quizzes/${quizId}`);
  }

  addQuizQuestion(
    quizId: string,
    data: {
      text: string;
      choices: { id: string; text: string }[];
      correct_choice_id: string;
      explanation?: string;
      points?: number;
      position?: number;
    }
  ) {
    return this.request<import("@/types").QuizQuestionAdmin>(
      `/content/quizzes/${quizId}/questions`,
      { method: "POST", body: JSON.stringify({ points: 1, position: 0, ...data }) }
    );
  }

  deleteQuizQuestion(questionId: string) {
    return this.request(`/content/questions/${questionId}`, { method: "DELETE" });
  }

  deleteQuiz(quizId: string) {
    return this.request(`/content/quizzes/${quizId}`, { method: "DELETE" });
  }

  // Quiz - student
  getQuizForStudent(quizId: string) {
    return this.request<import("@/types").Quiz>(`/content/quizzes/${quizId}/take`);
  }

  submitQuiz(quizId: string, answers: { question_id: string; choice_id: string }[]) {
    return this.request<import("@/types").QuizAttempt>(
      `/content/quizzes/${quizId}/submit`,
      { method: "POST", body: JSON.stringify({ answers }) }
    );
  }

  getMyQuizAttempts(quizId: string) {
    return this.request<import("@/types").QuizAttempt[]>(
      `/content/quizzes/${quizId}/my-attempts`
    );
  }
}

export const api = new ApiClient();
