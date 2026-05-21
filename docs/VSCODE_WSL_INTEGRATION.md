# 🎯 Intégration VS Code + WSL

Pour une meilleure expérience, utilisez **VS Code avec l'extension Remote - WSL**.

---

## 🔧 Installation et Configuration

### 1. Installer l'Extension VS Code

Dans VS Code:
- Ouvrez l'onglet **Extensions** (Ctrl+Shift+X)
- Recherchez "**Remote - WSL**"
- Installez l'extension officielle Microsoft

### 2. Ouvrir le Projet depuis WSL

```bash
cd /mnt/c/Users/aabed/Desktop/Platform
code .
```

VS Code s'ouvrira et affichera "WSL: Ubuntu" en bas à gauche.

---

## 💻 Workflow Recommandé

### Option 1: Terminal Intégré VS Code + WSL

1. Ouvrez VS Code
2. Connectez-vous à WSL (voir ci-dessus)
3. Ouvrez le terminal intégré (Ctrl+`)
4. Il sera automatiquement dans WSL

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### Option 2: Terminal Externe + VS Code

**Terminal WSL 1:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal WSL 2:**
```bash
cd frontend
npm run dev
```

**VS Code:**
- Ouvrez le projet avec `code .` depuis WSL

---

## ⚙️ Configuration VS Code pour WSL

### Extensions Recommandées

Dans VS Code (connecté à WSL), installez:

- **Python** (Microsoft)
- **Pylance** (Microsoft)
- **ESLint** (Microsoft)
- **Prettier** (Prettier)
- **REST Client** (Huachao Mao)
- **Thunder Client** (Ranga Vadhineni)

### Settings VS Code

Créez/modifiez `.vscode/settings.json` dans la racine du projet:

```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true
  }
}
```

### Launch Configuration

Créez `.vscode/launch.json` pour déboguer:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

---

## 🐛 Débogage

### Backend (Python)

1. Mettez un point d'arrêt (F9) dans le code Python
2. Exécutez la configuration "Python: FastAPI" (F5)
3. L'application s'arrêtera au point d'arrêt

### Frontend (Node.js/TypeScript)

Ouvrez les DevTools:
- Appuyez sur **F12** ou **Ctrl+Shift+I**

---

## 📂 Structure VS Code Recommandée

```
.vscode/
├── settings.json
├── launch.json
└── extensions.json

backend/
├── venv/
├── app/
└── ...

frontend/
├── node_modules/
├── app/
└── ...
```

---

## 🚀 Raccourcis VS Code Utiles

| Raccourci | Action |
|-----------|--------|
| Ctrl+` | Ouvrir/Fermer le terminal |
| Ctrl+Shift+` | Nouveau terminal |
| F5 | Démarrer le débogage |
| Ctrl+Shift+D | Vue Débogage |
| Ctrl+Shift+X | Extensions |
| Ctrl+Shift+E | Explorateur |
| Ctrl+, | Paramètres |

---

## 📝 Fichiers à Éditer en WSL via VS Code

```
backend/
├── app/
│   ├── main.py              ← Point d'entrée
│   ├── api/
│   │   └── router.py        ← Routes API
│   ├── modules/             ← Logique métier
│   ├── core/                ← Configuration
│   └── ...

frontend/
├── app/
│   ├── page.tsx             ← Home page
│   ├── layout.tsx           ← Layout
│   ├── (auth)/              ← Auth pages
│   ├── admin/               ← Admin pages
│   └── ...
├── components/              ← Composants réutilisables
└── ...
```

---

## ✅ Avantages VS Code + WSL

✅ Édition Windows native (VS Code)  
✅ Exécution Linux native (WSL)  
✅ Pas de performance perdue  
✅ Intégration Git  
✅ Débogage intégré  
✅ Terminal WSL intégré  
✅ Extensions disponibles  

---

## 🎯 Workflow Optimal

```
1. cd /mnt/c/Users/aabed/Desktop/Platform
2. code .                        ← VS Code s'ouvre connecté à WSL
3. Terminal 1: cd backend && source venv/bin/activate && uvicorn app.main:app --reload
4. Terminal 2: cd frontend && npm run dev
5. Éditer le code dans VS Code
6. Les changements sont automatiquement rechargés (--reload)
```

---

## 📚 Ressources

- [VS Code Remote WSL Docs](https://code.visualstudio.com/docs/remote/wsl)
- [VS Code Python](https://code.visualstudio.com/docs/languages/python)
- [VS Code JavaScript](https://code.visualstudio.com/docs/languages/javascript)

---

Vous êtes maintenant prêt pour une meilleure expérience de développement! 🎉

