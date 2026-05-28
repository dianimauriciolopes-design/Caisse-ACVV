import os

IS_POSTGRES = bool(os.getenv("DATABASE_URL"))

# ───────── POSTGRESQL ─────────
if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras

    def get_db():
        return psycopg2.connect(
            os.getenv("DATABASE_URL"),
            cursor_factory=psycopg2.extras.RealDictCursor
        )

    def init_db():
        conn = get_db()
        c = conn.cursor()

        # Tables
        c.execute("""
            CREATE TABLE IF NOT EXISTS stands (
                id SERIAL PRIMARY KEY,
                nom TEXT NOT NULL,
                description TEXT,
                actif INTEGER DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                stand_id INTEGER,
                nom TEXT,
                prix REAL,
                emoji TEXT,
                actif INTEGER DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                stand_id INTEGER,
                stand_nom TEXT,
                montant REAL,
                mode_paiement TEXT,
                statut TEXT DEFAULT 'confirme',
                detail_articles TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ✅ SAFE COUNT
        c.execute("SELECT COUNT(*) FROM stands")
        count = c.fetchone()[0]

        if count == 0:
            stands_defaut = [
                ("Bar Principal", "Bières, softs, vins"),
                ("Buvette Terrain A", "Boissons terrain A"),
                ("Buvette Terrain B", "Boissons terrain B"),
                ("Restauration", "Grillades, sandwichs"),
                ("Confiserie", "Snacks, bonbons"),
            ]

            c.executemany(
                "INSERT INTO stands (nom, description) VALUES (%s, %s)",
                stands_defaut
            )

            articles_defaut = [
                (1, "Bière 50cl", 4.00, "🍺"),
                (1, "Bière 33cl", 3.00, "🍺"),
                (1, "Soft 33cl", 2.50, "🥤"),
                (1, "Eau 50cl", 1.50, "💧"),
                (1, "Vin rouge", 4.00, "🍷"),
                (1, "Vin blanc", 4.00, "🥂"),
                (4, "Saucisse-pain", 5.00, "🌭"),
                (4, "Sandwich", 6.00, "🥪"),
                (4, "Frites", 4.00, "🍟"),
                (5, "Barre chocolat", 1.50, "🍫"),
                (5, "Chips", 2.00, "🍿"),
            ]

            c.executemany(
                "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (%s, %s, %s, %s)",
                articles_defaut
            )

        conn.commit()
        conn.close()

        print("✅ PostgreSQL initialisé")

# ───────── SQLITE ─────────
else:
    import sqlite3

    DB_PATH = os.path.join(os.path.dirname(__file__), "tournoi.db")

    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        conn = get_db()
        c = conn.cursor()

        # Tables
        c.execute("""
            CREATE TABLE IF NOT EXISTS stands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                description TEXT,
                actif INTEGER DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stand_id INTEGER,
                nom TEXT,
                prix REAL,
                emoji TEXT,
                actif INTEGER DEFAULT 1
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stand_id INTEGER,
                stand_nom TEXT,
                montant REAL,
                mode_paiement TEXT,
                statut TEXT DEFAULT 'confirme',
                detail_articles TEXT,
                note TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("SELECT COUNT(*) FROM stands")
        count = c.fetchone()[0]

        if count == 0:
            stands_defaut = [
                ("Bar Principal", "Bières, softs, vins"),
                ("Buvette Terrain A", "Boissons terrain A"),
                ("Buvette Terrain B", "Boissons terrain B"),
                ("Restauration", "Grillades, sandwichs"),
                ("Confiserie", "Snacks, bonbons"),
            ]

            c.executemany(
                "INSERT INTO stands (nom, description) VALUES (?, ?)",
                stands_defaut
            )

            articles_defaut = [
                (1, "Bière 50cl", 4.00, "🍺"),
                (1, "Bière 33cl", 3.00, "🍺"),
                (1, "Soft 33cl", 2.50, "🥤"),
                (1, "Eau 50cl", 1.50, "💧"),
                (1, "Vin rouge", 4.00, "🍷"),
                (1, "Vin blanc", 4.00, "🥂"),
                (4, "Saucisse-pain", 5.00, "🌭"),
                (4, "Sandwich", 6.00, "🥪"),
                (4, "Frites", 4.00, "🍟"),
                (5, "Barre chocolat", 1.50, "🍫"),
                (5, "Chips", 2.00, "🍿"),
            ]

            c.executemany(
                "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (?, ?, ?, ?)",
                articles_defaut
            )

        conn.commit()
        conn.close()

        print("✅ SQLite initialisé")