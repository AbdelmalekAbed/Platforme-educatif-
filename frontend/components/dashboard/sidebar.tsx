"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { useUiStore } from "@/store/ui";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  BookOpen,
  Video,
  ClipboardList,
  Calendar,
  BarChart3,
  CreditCard,
  Users,
  Settings,
  LogOut,
  ShoppingBag,
  UserCheck,
  FileText,
  GraduationCap,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

const teacherLinks = [
  { href: "/teacher", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/teacher/courses", label: "Mes cours", icon: BookOpen },
  { href: "/teacher/sessions", label: "Sessions live", icon: Video },
  { href: "/teacher/homework", label: "Devoirs", icon: ClipboardList },
  { href: "/teacher/attendance", label: "Présences", icon: UserCheck },
  { href: "/teacher/calendar", label: "Calendrier", icon: Calendar },
  { href: "/teacher/analytics", label: "Statistiques", icon: BarChart3 },
];

const studentLinks = [
  { href: "/student", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/student/catalog", label: "Catalogue", icon: GraduationCap },
  { href: "/student/courses", label: "Mes cours", icon: BookOpen },
  { href: "/student/homework", label: "Devoirs", icon: ClipboardList },
  { href: "/student/recordings", label: "Rediffusions", icon: Video },
  { href: "/student/attendance", label: "Mes présences", icon: UserCheck },
  { href: "/student/payments", label: "Paiements", icon: CreditCard },
  { href: "/student/documents", label: "Documents", icon: FileText },
];

const adminLinks = [
  { href: "/admin", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/admin/users", label: "Utilisateurs", icon: Users },
  { href: "/admin/courses", label: "Cours", icon: BookOpen },
  { href: "/admin/subjects", label: "Matières", icon: ClipboardList },
  { href: "/admin/payments", label: "Paiements", icon: CreditCard },
  { href: "/admin/analytics", label: "Analytiques", icon: BarChart3 },
  { href: "/admin/settings", label: "Paramètres", icon: Settings },
];

const vendorLinks = [
  { href: "/vendor", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/vendor/products", label: "Produits", icon: ShoppingBag },
  { href: "/vendor/sales", label: "Ventes", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { sidebarCollapsed, toggleSidebar } = useUiStore();

  if (!user) return null;

  const links =
    user.role === "admin"
      ? adminLinks
      : user.role === "teacher"
      ? teacherLinks
      : user.role === "vendor"
      ? vendorLinks
      : studentLinks;

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r bg-card transition-[width] duration-200",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="flex h-16 items-center justify-between gap-2 border-b px-3">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2 overflow-hidden px-1">
            <BookOpen className="h-6 w-6 shrink-0 text-primary" />
            <span className="text-lg font-bold">EdTech</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className={cn(
            "rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-foreground",
            sidebarCollapsed && "mx-auto"
          )}
          aria-label={sidebarCollapsed ? "Ouvrir la barre latérale" : "Fermer la barre latérale"}
          title={sidebarCollapsed ? "Ouvrir la barre latérale" : "Fermer la barre latérale"}
        >
          {sidebarCollapsed ? (
            <PanelLeftOpen className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-2">
        {links.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              title={sidebarCollapsed ? link.label : undefined}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                sidebarCollapsed && "justify-center px-0",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <link.icon className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span className="truncate">{link.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="border-t p-2">
        {!sidebarCollapsed ? (
          <>
            <div className="mb-3 flex items-center gap-3 px-1">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                {user.first_name[0]}
                {user.last_name[0]}
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="truncate text-sm font-medium">
                  {user.first_name} {user.last_name}
                </p>
                <p className="truncate text-xs text-muted-foreground">{user.role}</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              <LogOut className="h-4 w-4" />
              Déconnexion
            </button>
          </>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div
              className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground"
              title={`${user.first_name} ${user.last_name} (${user.role})`}
            >
              {user.first_name[0]}
              {user.last_name[0]}
            </div>
            <button
              onClick={logout}
              className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              title="Déconnexion"
              aria-label="Déconnexion"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
