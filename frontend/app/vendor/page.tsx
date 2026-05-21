"use client";

import { StatsCard } from "@/components/dashboard/stats-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ShoppingBag, DollarSign, Package, TrendingUp } from "lucide-react";

export default function VendorDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Espace Vendeur</h1>
        <p className="text-muted-foreground">Gérez vos produits et ventes</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard title="Produits" value="0" icon={Package} />
        <StatsCard title="Ventes" value="0" icon={ShoppingBag} />
        <StatsCard title="Revenus" value="0 €" icon={DollarSign} />
        <StatsCard title="Croissance" value="—" icon={TrendingUp} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Fonctionnalité à venir</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            L&apos;espace vendeur est en cours de développement. Vous pourrez bientôt :
          </p>
          <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
            <li>• Publier des formations et supports pédagogiques</li>
            <li>• Gérer votre catalogue de produits</li>
            <li>• Suivre vos ventes et revenus</li>
            <li>• Accéder aux statistiques de performance</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
