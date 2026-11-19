# Caisse-ACVV

Gestion de paiement par TWINT ou par cash pour l'ACVV (tournoi de football).

App statique (HTML/JS, pas de serveur) qui parle directement à **Supabase**
(base de données + API), déployée sur **Cloudflare Pages**.

## 🏗️ Architecture

- `public/` — tout le site : pages HTML + JS, c'est ça qui est déployé sur
  Cloudflare Pages.
- `supabase/schema.sql` — tables, règles de sécurité (RLS) et données par
  défaut à exécuter une fois dans le projet Supabase.
- `legacy-flask/` — ancienne version Flask/SQLite, gardée pour référence.
  Plus utilisée, peut être supprimée.

Le navigateur appelle directement l'API Supabase avec la clé `anon`
(protégée par des règles RLS plutôt que par un vrai serveur). Les pages
`/admin.html` et `/dashboard.html` sont protégées par un simple mot de passe
partagé — **ce n'est pas une vraie authentification**, juste un filtre pour
éviter qu'un visiteur lambda tombe dessus par erreur. Ne pas s'en servir pour
protéger des données sensibles.

## 🚀 Mise en place (une seule fois)

### 1. Créer le projet Supabase

1. Va sur [supabase.com](https://supabase.com) → crée un compte/projet (région Europe conseillée).
2. Dans le projet → **SQL Editor** → nouvelle requête → colle le contenu de
   [`supabase/schema.sql`](supabase/schema.sql) → **Run**.
   Ça crée les tables `stands`, `articles`, `transactions`, les règles RLS,
   et les stands/articles par défaut.
3. Dans **Project Settings → API**, récupère :
   - `Project URL`
   - `anon public` key

### 2. Configurer l'app

Édite [`public/js/config.js`](public/js/config.js) :

```js
const SUPABASE_URL = "https://xxxxx.supabase.co";
const SUPABASE_ANON_KEY = "eyJ...";
const ADMIN_PASSWORD = "mot-de-passe-du-jour";
```

### 3. Tester en local

```bash
npm install
npm run dev
```

Puis ouvre l'URL affichée par `wrangler` (en général `http://localhost:8788`).

### 4. Déployer sur Cloudflare Pages

**Option A — via le dashboard Cloudflare (recommandé) :**
1. [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Sélectionne ce dépôt.
3. Build settings : **Framework preset = None**, **Build command = (vide)**,
   **Build output directory = `public`**.
4. Déployer. Chaque `git push` redéploie automatiquement.

**Option B — en ligne de commande :**
```bash
npm run deploy
```

## 📱 Utilisation le jour du tournoi

| Page | URL |
|---|---|
| Choix du stand | `https://ton-site.pages.dev/` |
| Caisse d'un stand | lien généré automatiquement depuis la page d'accueil |
| Dashboard organisateur | `https://ton-site.pages.dev/dashboard.html` (mot de passe) |
| Administration (stands/articles) | `https://ton-site.pages.dev/admin.html` (mot de passe) |

Le dashboard se rafraîchit automatiquement toutes les 15 secondes.

## 🍹 Personnaliser les stands / articles

Via l'interface : `/admin.html`. Ou directement dans Supabase (**Table editor**).

## 📷 QR TWINT

Le QR code affiché sur `/caisse.html` et `/twint.html` est l'image statique
[`public/img/qrcode.jpg`](public/img/qrcode.jpg). Pour le changer :
remplace ce fichier par le QR de ton compte TWINT
(TWINT → Mon profil → Partager → Copier/exporter le QR).
