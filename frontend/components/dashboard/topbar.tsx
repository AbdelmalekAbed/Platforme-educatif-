"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { usePlatformStore } from "@/store/platform";
import { api } from "@/services/api";
import type { Notification as NotifType } from "@/types";
import { Bell, Check, CheckCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";

const POLL_INTERVAL_MS = 60_000;
const TYPE_DOT: Record<NotifType["type"], string> = {
  info: "bg-blue-500",
  success: "bg-green-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
};

export function TopBar() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const platformSettings = usePlatformStore((s) => s.settings);
  const ensurePlatformLoaded = usePlatformStore((s) => s.ensureLoaded);
  const [notifications, setNotifications] = useState<NotifType[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    ensurePlatformLoaded();
  }, [ensurePlatformLoaded]);

  const load = useCallback(async () => {
    try {
      const res = await api.getNotifications(false);
      setNotifications(res);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [isAuthenticated, load]);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const handleClick = async (notif: NotifType) => {
    if (!notif.is_read) {
      setNotifications((prev) =>
        prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
      );
      try {
        await api.markNotificationRead(notif.id);
      } catch (err) {
        console.error(err);
      }
    }
    if (notif.link) {
      setOpen(false);
      router.push(notif.link);
    }
  };

  const handleMarkAllRead = async () => {
    if (unreadCount === 0) return;
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    try {
      await api.markAllNotificationsRead();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-wide text-muted-foreground truncate">
          {platformSettings?.name ?? "EdTech Platform"}
        </p>
        <h2 className="text-lg font-semibold truncate">
          Bienvenue, {user?.first_name} 👋
        </h2>
      </div>
      <div ref={containerRef} className="relative flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          onClick={() => setOpen((o) => !o)}
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-semibold text-destructive-foreground">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </Button>

        {open && (
          <div className="absolute right-0 top-12 z-50 w-80 rounded-lg border bg-popover shadow-lg">
            <div className="flex items-center justify-between border-b px-4 py-2.5">
              <h3 className="font-semibold text-sm">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors"
                  title="Tout marquer comme lu"
                >
                  <CheckCheck className="h-3.5 w-3.5" />
                  Tout lire
                </button>
              )}
            </div>

            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="px-4 py-10 text-center text-sm text-muted-foreground">
                  <Bell className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  Aucune notification
                </div>
              ) : (
                notifications.map((notif) => (
                  <button
                    key={notif.id}
                    onClick={() => handleClick(notif)}
                    className={`w-full text-left px-4 py-3 border-b last:border-0 hover:bg-accent transition-colors ${
                      !notif.is_read ? "bg-accent/40" : ""
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <span
                        className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                          TYPE_DOT[notif.type] ?? "bg-blue-500"
                        } ${notif.is_read ? "opacity-30" : ""}`}
                      />
                      <div className="flex-1 min-w-0">
                        <p
                          className={`text-sm leading-tight ${
                            notif.is_read ? "font-normal text-muted-foreground" : "font-medium"
                          }`}
                        >
                          {notif.title}
                        </p>
                        {notif.message && (
                          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                            {notif.message}
                          </p>
                        )}
                        <p className="text-[10px] text-muted-foreground mt-1">
                          {formatDistanceToNow(new Date(notif.created_at), {
                            addSuffix: true,
                            locale: fr,
                          })}
                        </p>
                      </div>
                      {notif.is_read && (
                        <Check className="h-3 w-3 text-muted-foreground shrink-0 mt-1" />
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
