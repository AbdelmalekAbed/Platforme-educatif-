# ⚡ WSL - QUICK START

## 🚀 En 3 Étapes

### 1️⃣ Ouvrir WSL et Accéder au Projet

```bash
# Depuis le menu Démarrer ou PowerShell, tapez: wsl
# Puis naviguez au projet:
cd /mnt/c/Users/aabed/Desktop/Platform
```

### 2️⃣ Lancer le Setup (PREMIÈRE FOIS SEULEMENT)

```bash
chmod +x setup_wsl.sh
bash setup_wsl.sh
```

Cela installe et configure tout automatiquement (2-3 min).

### 3️⃣ Démarrer l'Application

**Terminal WSL 1 - Backend:**
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

**Terminal WSL 2 - Frontend:**
```bash
cd frontend && npm run dev
```

---

## 🌐 Accès

- **Frontend**: http://localhost:3000
- **Admin**: admin@edtech.com / Admin123456

---

## 🔄 Redémarrage (Après Première Fois)

**Backend:**
```bash
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend && npm run dev
```

---

## 📖 Besoin d'Aide?

→ Consultez [SETUP_WSL_GUIDE.md](SETUP_WSL_GUIDE.md)

---

## 🆘 Problèmes Rapides

| Problème | Solution |
|----------|----------|
| PostgreSQL ne démarre pas | `sudo service postgresql start` |
| "alembic not found" | `source venv/bin/activate` |
| Port déjà utilisé | Vérifier un autre processus |
| WSL très lent | Utiliser WSL 2 |

