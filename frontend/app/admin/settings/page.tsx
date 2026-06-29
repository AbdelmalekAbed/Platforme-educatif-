"use client";

import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/services/api";
import { usePlatformStore } from "@/store/platform";
import type {
  PlatformSettings,
  SettingsSectionKey,
  PlatformSection,
  SignupsSection,
  SecuritySection,
  NotificationsSection,
  CoursesSection,
  AppearanceSection,
} from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Settings as SettingsIcon,
  Globe,
  UserPlus,
  ShieldCheck,
  Bell,
  GraduationCap,
  Palette,
  Wrench,
  Check,
  AlertTriangle,
  Loader2,
} from "lucide-react";

type SectionKey = SettingsSectionKey | "maintenance";

const SECTIONS: { key: SectionKey; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { key: "platform", label: "Plateforme", icon: Globe },
  { key: "signups", label: "Inscriptions", icon: UserPlus },
  { key: "security", label: "Sécurité", icon: ShieldCheck },
  { key: "notifications", label: "Notifications", icon: Bell },
  { key: "courses", label: "Cours par défaut", icon: GraduationCap },
  { key: "appearance", label: "Apparence", icon: Palette },
  { key: "maintenance", label: "Maintenance", icon: Wrench },
];

export default function AdminSettingsPage() {
  const refreshPlatform = usePlatformStore((s) => s.refresh);
  const [section, setSection] = useState<SectionKey>("platform");
  const [settings, setSettings] = useState<PlatformSettings | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [savingSection, setSavingSection] = useState<SettingsSectionKey | null>(null);
  const [savedSection, setSavedSection] = useState<SettingsSectionKey | null>(null);
  const [sectionError, setSectionError] = useState<{ key: SettingsSectionKey; message: string } | null>(
    null
  );

  useEffect(() => {
    let cancelled = false;
    api
      .getSettings()
      .then((s) => !cancelled && setSettings(s))
      .catch((err) =>
        !cancelled && setLoadError(err instanceof Error ? err.message : "Erreur de chargement")
      );
    return () => {
      cancelled = true;
    };
  }, []);

  const updateLocal = <K extends SettingsSectionKey>(key: K, patch: Partial<PlatformSettings[K]>) => {
    setSettings((prev) => (prev ? { ...prev, [key]: { ...prev[key], ...patch } } : prev));
  };

  const save = async <K extends SettingsSectionKey>(key: K) => {
    if (!settings) return;
    setSavingSection(key);
    setSectionError(null);
    try {
      const result = await api.updateSettings(key, settings[key]);
      setSettings((prev) => (prev ? { ...prev, [key]: result } : prev));
      // Platform identity is also exposed via /public/settings — refresh the
      // cached store so the TopBar and tab title update immediately.
      if (key === "platform" || key === "signups") {
        refreshPlatform();
      }
      setSavedSection(key);
      setTimeout(() => setSavedSection((s) => (s === key ? null : s)), 2500);
    } catch (err) {
      setSectionError({
        key,
        message: err instanceof Error ? err.message : "Échec de l'enregistrement",
      });
    } finally {
      setSavingSection(null);
    }
  };

  if (loadError) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-red-600">{loadError}</CardContent>
      </Card>
    );
  }

  if (!settings) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <SettingsIcon className="h-8 w-8" /> Paramètres
        </h1>
        <div className="animate-pulse text-muted-foreground">Chargement de la configuration...</div>
      </div>
    );
  }

  const { platform, signups, security, notifications, courses, appearance } = settings;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <SettingsIcon className="h-8 w-8" /> Paramètres
        </h1>
        <p className="text-muted-foreground">Configuration globale de la plateforme</p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <aside className="col-span-12 md:col-span-3">
          <Card>
            <nav className="p-2">
              {SECTIONS.map(({ key, label, icon: Icon }) => {
                const active = section === key;
                return (
                  <button
                    key={key}
                    onClick={() => setSection(key)}
                    className={`w-full flex items-center gap-3 rounded-md px-3 py-2 text-sm text-left transition-colors ${
                      active
                        ? "bg-primary/10 text-primary font-medium"
                        : "hover:bg-accent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{label}</span>
                  </button>
                );
              })}
            </nav>
          </Card>
        </aside>

        <div className="col-span-12 md:col-span-9 space-y-6">
          {section === "platform" && (
            <SectionWrapper
              title="Identité de la plateforme"
              description="Le nom apparaît dans l'en-tête et le titre des onglets. L'email de support sert pour les liens d'aide."
              sectionKey="platform"
              saved={savedSection === "platform"}
              saving={savingSection === "platform"}
              error={sectionError?.key === "platform" ? sectionError.message : null}
              onSave={() => save("platform")}
            >
              <Field label="Nom de la plateforme">
                <Input
                  value={platform.name}
                  onChange={(e) => updateLocal("platform", { name: e.target.value })}
                />
              </Field>
              <Field label="Description / tagline" hint="Affichée sur la page d'accueil publique.">
                <Input
                  value={platform.description}
                  onChange={(e) => updateLocal("platform", { description: e.target.value })}
                />
              </Field>
              <Field label="Email de support">
                <Input
                  type="email"
                  value={platform.support_email ?? ""}
                  onChange={(e) =>
                    updateLocal("platform", { support_email: e.target.value || null })
                  }
                />
              </Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Langue par défaut">
                  <Select
                    value={platform.default_language}
                    onChange={(v) =>
                      updateLocal("platform", {
                        default_language: v as PlatformSection["default_language"],
                      })
                    }
                    options={[
                      { value: "fr", label: "Français" },
                      { value: "en", label: "English" },
                      { value: "ar", label: "العربية" },
                    ]}
                  />
                </Field>
                <Field label="Fuseau horaire">
                  <Select
                    value={platform.timezone}
                    onChange={(v) => updateLocal("platform", { timezone: v })}
                    options={[
                      { value: "Europe/Paris", label: "Europe / Paris" },
                      { value: "Africa/Tunis", label: "Africa / Tunis" },
                      { value: "UTC", label: "UTC" },
                    ]}
                  />
                </Field>
              </div>
            </SectionWrapper>
          )}

          {section === "signups" && (
            <SectionWrapper
              title="Inscriptions et accès"
              description="Comment les nouveaux utilisateurs rejoignent la plateforme. Ces réglages sont appliqués en temps réel au formulaire d'inscription."
              sectionKey="signups"
              saved={savedSection === "signups"}
              saving={savingSection === "signups"}
              error={sectionError?.key === "signups" ? sectionError.message : null}
              onSave={() => save("signups")}
            >
              <Toggle
                label="Inscriptions publiques ouvertes"
                description="Si désactivé, l'endpoint /auth/register renvoie 403 — seuls les admins peuvent créer des comptes."
                checked={signups.public_signup_open}
                onChange={(v) => updateLocal("signups", { public_signup_open: v })}
              />
              <Toggle
                label="Vérification email obligatoire"
                description="L'utilisateur doit cliquer sur un lien envoyé par email avant de pouvoir se connecter."
                checked={signups.require_email_verification}
                onChange={(v) => updateLocal("signups", { require_email_verification: v })}
              />
              <Field label="Rôle par défaut à l'inscription">
                <Select
                  value={signups.default_role}
                  onChange={(v) =>
                    updateLocal("signups", { default_role: v as SignupsSection["default_role"] })
                  }
                  options={[
                    { value: "student", label: "Élève" },
                    { value: "teacher", label: "Professeur (demande validation)" },
                  ]}
                />
              </Field>
              <Toggle
                label="Approuver automatiquement les professeurs"
                description="Sinon, chaque compte professeur doit être validé par un admin."
                checked={signups.auto_approve_teachers}
                onChange={(v) => updateLocal("signups", { auto_approve_teachers: v })}
              />
              <Toggle
                label="Invitation requise pour les professeurs"
                description="Les professeurs ne peuvent s'inscrire qu'avec un lien d'invitation envoyé par un admin."
                checked={signups.require_invite_for_teachers}
                onChange={(v) => updateLocal("signups", { require_invite_for_teachers: v })}
              />
            </SectionWrapper>
          )}

          {section === "security" && (
            <SectionWrapper
              title="Sécurité"
              description="Politiques de connexion, sessions et mots de passe."
              sectionKey="security"
              saved={savedSection === "security"}
              saving={savingSection === "security"}
              error={sectionError?.key === "security" ? sectionError.message : null}
              onSave={() => save("security")}
            >
              <div className="grid grid-cols-2 gap-4">
                <Field label="Délai d'expiration de session (minutes)">
                  <Input
                    type="number"
                    min={5}
                    max={1440}
                    value={security.session_timeout_minutes}
                    onChange={(e) =>
                      updateLocal("security", {
                        session_timeout_minutes: Number(e.target.value) || 0,
                      })
                    }
                  />
                </Field>
                <Field label="Longueur minimale du mot de passe">
                  <Input
                    type="number"
                    min={6}
                    max={64}
                    value={security.password_min_length}
                    onChange={(e) =>
                      updateLocal("security", {
                        password_min_length: Number(e.target.value) || 0,
                      })
                    }
                  />
                </Field>
              </div>
              <Field
                label="Tentatives de connexion avant verrouillage"
                hint="Verrouille temporairement le compte après cette limite."
              >
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={security.max_login_attempts}
                  onChange={(e) =>
                    updateLocal("security", { max_login_attempts: Number(e.target.value) || 0 })
                  }
                />
              </Field>
              <Toggle
                label="Authentification à deux facteurs obligatoire pour les admins"
                description="Force tous les comptes admin à configurer la 2FA à la prochaine connexion."
                checked={security.require_mfa_for_admins}
                onChange={(v) => updateLocal("security", { require_mfa_for_admins: v })}
              />
            </SectionWrapper>
          )}

          {section === "notifications" && (
            <SectionWrapper
              title="Notifications par email"
              description="Quels événements déclenchent un email automatique."
              sectionKey="notifications"
              saved={savedSection === "notifications"}
              saving={savingSection === "notifications"}
              error={sectionError?.key === "notifications" ? sectionError.message : null}
              onSave={() => save("notifications")}
            >
              <Toggle
                label="Activer les notifications email"
                description="Désactivez pour suspendre tous les emails transactionnels (utile en maintenance)."
                checked={notifications.email_notifications_global}
                onChange={(v) =>
                  updateLocal("notifications", { email_notifications_global: v })
                }
              />
              <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
                <p className="text-sm font-medium">Notifier les admins lorsque :</p>
                <Toggle
                  label="Un nouveau compte est créé"
                  checked={notifications.notify_on_new_signup}
                  onChange={(v) =>
                    updateLocal("notifications", { notify_on_new_signup: v })
                  }
                  compact
                />
                <Toggle
                  label="Un paiement est reçu ou échoue"
                  checked={notifications.notify_on_payment}
                  onChange={(v) => updateLocal("notifications", { notify_on_payment: v })}
                  compact
                />
                <Toggle
                  label="Un devoir arrive à échéance dans les 24 h"
                  checked={notifications.notify_on_assignment_due}
                  onChange={(v) =>
                    updateLocal("notifications", { notify_on_assignment_due: v })
                  }
                  compact
                />
              </div>
              <Toggle
                label="Envoyer un résumé hebdomadaire"
                description="Email récapitulatif chaque lundi matin (activité, revenus, inscriptions)."
                checked={notifications.weekly_digest}
                onChange={(v) => updateLocal("notifications", { weekly_digest: v })}
              />
            </SectionWrapper>
          )}

          {section === "courses" && (
            <SectionWrapper
              title="Cours et contenus"
              description="Valeurs par défaut appliquées en temps réel : pass score utilisé à la création d'un quiz, taille max à l'upload vidéo."
              sectionKey="courses"
              saved={savedSection === "courses"}
              saving={savingSection === "courses"}
              error={sectionError?.key === "courses" ? sectionError.message : null}
              onSave={() => save("courses")}
            >
              <div className="grid grid-cols-2 gap-4">
                <Field
                  label="Score de réussite par défaut (%)"
                  hint="Appliqué aux nouveaux quiz quand non précisé."
                >
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    value={courses.default_pass_score}
                    onChange={(e) =>
                      updateLocal("courses", {
                        default_pass_score: Number(e.target.value) || 0,
                      })
                    }
                  />
                </Field>
                <Field
                  label="Taille max vidéo (Mo)"
                  hint="Limite imposée par l'API d'upload pour les fichiers vidéo."
                >
                  <Input
                    type="number"
                    min={1}
                    max={2000}
                    value={courses.video_max_size_mb}
                    onChange={(e) =>
                      updateLocal("courses", {
                        video_max_size_mb: Number(e.target.value) || 0,
                      })
                    }
                  />
                </Field>
              </div>
              <Field
                label="Archiver automatiquement après (jours d'inactivité)"
                hint="Les cours sans consultation depuis ce délai passent en archives."
              >
                <Input
                  type="number"
                  min={30}
                  max={3650}
                  value={courses.auto_archive_after_days}
                  onChange={(e) =>
                    updateLocal("courses", {
                      auto_archive_after_days: Number(e.target.value) || 0,
                    })
                  }
                />
              </Field>
              <Toggle
                label="Autoriser les élèves à noter les cours"
                description="Affiche une étoile de notation 1-5 sur la page d'un cours terminé."
                checked={courses.allow_student_course_rating}
                onChange={(v) =>
                  updateLocal("courses", { allow_student_course_rating: v })
                }
              />
            </SectionWrapper>
          )}

          {section === "appearance" && (
            <SectionWrapper
              title="Apparence"
              description="Personnalisation visuelle de l'interface."
              sectionKey="appearance"
              saved={savedSection === "appearance"}
              saving={savingSection === "appearance"}
              error={sectionError?.key === "appearance" ? sectionError.message : null}
              onSave={() => save("appearance")}
            >
              <Field label="Couleur d'accent">
                <div className="flex flex-wrap gap-2">
                  {["#7c3aed", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#ec4899"].map(
                    (color) => (
                      <button
                        key={color}
                        type="button"
                        onClick={() => updateLocal("appearance", { accent_color: color })}
                        className={`h-10 w-10 rounded-full border-2 transition-transform hover:scale-110 ${
                          appearance.accent_color === color
                            ? "border-foreground scale-110"
                            : "border-transparent"
                        }`}
                        style={{ background: color }}
                        aria-label={`Couleur ${color}`}
                      />
                    )
                  )}
                </div>
              </Field>
              <Field label="Thème par défaut">
                <div className="flex gap-2">
                  {(["light", "dark", "system"] as const).map((theme) => (
                    <button
                      key={theme}
                      type="button"
                      onClick={() =>
                        updateLocal("appearance", {
                          default_theme: theme as AppearanceSection["default_theme"],
                        })
                      }
                      className={`flex-1 rounded-lg border-2 px-4 py-3 text-sm capitalize transition-colors ${
                        appearance.default_theme === theme
                          ? "border-primary bg-primary/10 font-medium"
                          : "border-border hover:bg-accent"
                      }`}
                    >
                      {theme === "light" ? "Clair" : theme === "dark" ? "Sombre" : "Système"}
                    </button>
                  ))}
                </div>
              </Field>
            </SectionWrapper>
          )}

          {section === "maintenance" && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">État du système</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <Row label="Version" value="v1.0.0" />
                  <Row label="Base de données" value="PostgreSQL — connectée" />
                  <Row label="Langue de référence" value={platform.default_language.toUpperCase()} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Opérations</CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Actions ponctuelles — non branchées au backend pour l&apos;instant.
                  </p>
                </CardHeader>
                <CardContent className="grid gap-2 sm:grid-cols-2">
                  <Button variant="outline" disabled>Lancer une sauvegarde</Button>
                  <Button variant="outline" disabled>Vider le cache</Button>
                  <Button variant="outline" disabled>Exporter les données (CSV)</Button>
                  <Button variant="outline" disabled>Vérifier les liens cassés</Button>
                </CardContent>
              </Card>

              <Card className="border-red-500/40">
                <CardHeader>
                  <CardTitle className="text-base text-red-600 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" /> Zone dangereuse
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium">Réinitialiser les statistiques</p>
                      <p className="text-xs text-muted-foreground">
                        Remet à zéro les compteurs sans toucher aux comptes ni au contenu.
                      </p>
                    </div>
                    <Button variant="outline" disabled className="border-red-500/40 text-red-600">
                      Réinitialiser
                    </Button>
                  </div>
                  <div className="flex items-center justify-between gap-4 pt-3 border-t">
                    <div>
                      <p className="text-sm font-medium">Mode maintenance</p>
                      <p className="text-xs text-muted-foreground">
                        Bloque l&apos;accès non-admin et affiche un message d&apos;attente.
                      </p>
                    </div>
                    <Button variant="outline" disabled className="border-red-500/40 text-red-600">
                      Activer
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------- Local UI helpers ----------

function SectionWrapper({
  title,
  description,
  sectionKey: _sectionKey,
  saved,
  saving,
  error,
  onSave,
  children,
}: {
  title: string;
  description?: string;
  sectionKey: SettingsSectionKey;
  saved: boolean;
  saving: boolean;
  error: string | null;
  onSave: () => void;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && (
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-5">
        {children}
        <div className="flex items-center justify-end gap-3 pt-3 border-t">
          {error && <span className="text-sm text-red-600">{error}</span>}
          {saved && (
            <span className="flex items-center gap-1 text-sm text-green-600">
              <Check className="h-4 w-4" /> Modifications enregistrées
            </span>
          )}
          <Button onClick={onSave} disabled={saving}>
            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {saving ? "Enregistrement..." : "Enregistrer"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-sm font-medium">{label}</Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function Toggle({
  label,
  description,
  checked,
  onChange,
  compact = false,
}: {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  compact?: boolean;
}) {
  return (
    <div className={`flex items-start justify-between gap-4 ${compact ? "" : "py-1"}`}>
      <div className="flex-1">
        <div className="text-sm font-medium">{label}</div>
        {description && (
          <div className="text-xs text-muted-foreground mt-0.5">{description}</div>
        )}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors mt-0.5 ${
          checked ? "bg-primary" : "bg-input"
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition-transform ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b last:border-0 pb-2 last:pb-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
