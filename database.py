import os
import sqlite3
import psycopg2
import psycopg2.extras

DB_PATH = "data.db"

IS_POSTGRES = "DATABASE_URL" in os.environ


# ───────── CONNEXION DB ─────────

def get_db():
    if IS_POSTGRES:
        conn = psycopg2.connect(
            os.environ["DATABASE_URL"],
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


# ───────── INIT DB ─────────

def init_db():
    db = get_db()
    cur = db.cursor()

    # Création des tables
    if IS_POSTGRES:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stands (
                id SERIAL PRIMARY KEY,
                nom TEXT NOT NULL,
                description TEXT,
                actif BOOLEAN DEFAULT TRUE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                stand_id INTEGER REFERENCES stands(id),
                nom TEXT NOT NULL,
                prix REAL NOT NULL,
                emoji TEXT,
                actif BOOLEAN DEFAULT TRUE
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                stand_id INTEGER REFERENCES stands(id),
                stand_nom TEXT,
                montant REAL NOT NULL,
                mode_paiement TEXT,
                statut TEXT DEFAULT 'ok',
                detail_articles TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                description TEXT,
                actif INTEGER DEFAULT 1
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stand_id INTEGER,
                nom TEXT NOT NULL,
                prix REAL NOT NULL,
                emoji TEXT,
                actif INTEGER DEFAULT 1
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stand_id INTEGER,
                stand_nom TEXT,
                montant REAL NOT NULL,
                mode_paiement TEXT,
                statut TEXT DEFAULT 'ok',
                detail_articles TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)

    # Vérifier si la table stands est vide
    cur.execute("SELECT COUNT(*) AS cnt FROM stands")
    row = cur.fetchone()

    if row is None:
        count = 0
    elif isinstance(row, dict):
        count = row["cnt"]
    else:
        count = row[0]

    # Si vide → insérer données par défaut
    if count == 0:
        print("→ Initialisation des stands et articles par défaut")

        # ───────── STANDS (10 stands) ─────────
        stands_defaut = [
            ("À manger", "nourritures"),
            ("Boissons", "Boissons basiques"),
            ("Cocktails", "avec ou sans alcool, consigne 2chf"),
        ]

        cur.executemany(
            "INSERT INTO stands (nom, description) VALUES (%s, %s)" if IS_POSTGRES else
            "INSERT INTO stands (nom, description) VALUES (?, ?)",
            stands_defaut
        )

        # Récupérer les IDs
        cur.execute("SELECT id FROM stands ORDER BY id")
        stands = cur.fetchall()
        ids = [s["id"] if isinstance(s, dict) else s[0] for s in stands]

        # ───────── ARTICLES (beaucoup plus variés) ─────────
        articles_defaut = [
            # a manger (1)
            (ids[0], "Grillades", 12.00, "🥩"),
            (ids[0], "Bifanas", 8.00, "🫓"),
            (ids[0], "Frites", 5.00, "🍟"),

            # Boissons (2)
            (ids[1], "Minérale 3DL (Coca,..)", 3.00, "🥤"),
            (ids[1], "Eau Minéral 1.5LT", 6.00, "💧"),
            (ids[1], "Bière", 4.00, "🍺"),
            (ids[1], "Bière sans alcool", 4.00, "🍺"),
            (ids[1], "Mateus Rosé", 15.00, "🍷"),
            (ids[1], "Vin au verre", 4.00, "🍷"),
            (ids[1], "Grogu", 5.00, "🥃"),
            (ids[1], "Red bull", 5.00, "🥤"),
            (ids[1], "Café", 3.00, "☕"),

            # Cocktails (3)
            (ids[2], "Virgin Mojito (+ 2chf)", 10.00, "🍸"),
            (ids[2], "Mojito (+ 2chf)", 12.00, "🍸"),
            (ids[2], "Caipirinha (+ 2chf)", 10.00, "🍹"),
            (ids[2], "Spritz (+ 2chf)", 10.00, "🍹"),
        ]

        cur.executemany(
            "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (%s, %s, %s, %s)" if IS_POSTGRES else
            "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (?, ?, ?, ?)",
            articles_defaut
        )

    db.commit()
    db.close()
