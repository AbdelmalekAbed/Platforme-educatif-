import "@/styles/globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "EdTech Platform",
  description: "Plateforme éducative complète",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
