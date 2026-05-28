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

    # Compatible PostgreSQL + SQLite
    if row is None:
        count = 0
    elif isinstance(row, dict):
        count = row["cnt"]
    else:
        count = row[0]

    # Si vide → insérer données par défaut
    if count == 0:
        print("→ Initialisation des stands et articles par défaut")

        cur.execute("INSERT INTO stands (nom, description) VALUES (%s, %s)" if IS_POSTGRES else
                    "INSERT INTO stands (nom, description) VALUES (?, ?)",
                    ("Bar", "Boissons"))

        cur.execute("INSERT INTO stands (nom, description) VALUES (%s, %s)" if IS_POSTGRES else
                    "INSERT INTO stands (nom, description) VALUES (?, ?)",
                    ("Nourriture", "Snacks"))

        # Récupérer les IDs
        cur.execute("SELECT id FROM stands ORDER BY id")
        stands = cur.fetchall()

        ids = [s["id"] if isinstance(s, dict) else s[0] for s in stands]

        articles = [
            (ids[0], "Bière", 5, "🍺"),
            (ids[0], "Soda", 3, "🥤"),
            (ids[1], "Hot-dog", 6, "🌭"),
            (ids[1], "Chips", 2, "🍟"),
        ]

        for a in articles:
            cur.execute(
                "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (%s, %s, %s, %s)"
                if IS_POSTGRES else
                "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (?, ?, ?, ?)",
                a
            )

    db.commit()
    db.close()
