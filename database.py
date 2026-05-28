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
            ("Bar Principal", "Bières, softs, vins"),
            ("Buvette Terrain A", "Boissons terrain A"),
            ("Buvette Terrain B", "Boissons terrain B"),
            ("Restauration", "Grillades, sandwichs"),
            ("Confiserie", "Snacks, bonbons"),
            ("Café & Desserts", "Café, thé, pâtisseries"),
            ("Cocktails", "Cocktails alcoolisés et sans alcool"),
            ("Vins & Spiritueux", "Sélection de vins et alcools"),
            ("Glaces", "Glaces et desserts froids"),
            ("Produits Locaux", "Produits artisanaux de la région"),
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
            # Bar Principal (1)
            (ids[0], "Bière 50cl", 4.00, "🍺"),
            (ids[0], "Bière 33cl", 3.00, "🍺"),
            (ids[0], "Soft 33cl", 2.50, "🥤"),
            (ids[0], "Eau 50cl", 1.50, "💧"),
            (ids[0], "Vin rouge", 4.00, "🍷"),
            (ids[0], "Vin blanc", 4.00, "🥂"),

            # Buvette Terrain A (2)
            (ids[1], "Soda", 3.00, "🥤"),
            (ids[1], "Eau", 2.00, "💧"),
            (ids[1], "Ice Tea", 3.00, "🧋"),

            # Buvette Terrain B (3)
            (ids[2], "Soda", 3.00, "🥤"),
            (ids[2], "Eau", 2.00, "💧"),
            (ids[2], "Barre énergétique", 2.50, "🍫"),

            # Restauration (4)
            (ids[3], "Saucisse-pain", 5.00, "🌭"),
            (ids[3], "Sandwich", 6.00, "🥪"),
            (ids[3], "Frites", 4.00, "🍟"),
            (ids[3], "Hamburger", 8.00, "🍔"),
            (ids[3], "Hot-dog", 5.00, "🌭"),

            # Confiserie (5)
            (ids[4], "Chips", 2.00, "🍿"),
            (ids[4], "Bonbons", 1.50, "🍬"),
            (ids[4], "Chocolat", 2.00, "🍫"),

            # Café & Desserts (6)
            (ids[5], "Café", 2.50, "☕"),
            (ids[5], "Cappuccino", 3.50, "☕"),
            (ids[5], "Thé", 2.50, "🍵"),
            (ids[5], "Croissant", 2.00, "🥐"),
            (ids[5], "Muffin", 3.00, "🧁"),

            # Cocktails (7)
            (ids[6], "Mojito", 8.00, "🍹"),
            (ids[6], "Virgin Mojito", 6.00, "🍸"),
            (ids[6], "Spritz", 7.00, "🥂"),

            # Vins & Spiritueux (8)
            (ids[7], "Whisky", 7.00, "🥃"),
            (ids[7], "Vodka Shot", 4.00, "🍸"),
            (ids[7], "Vin rosé", 4.00, "🍷"),

            # Glaces (9)
            (ids[8], "Cornet Vanille", 3.00, "🍦"),
            (ids[8], "Cornet Chocolat", 3.00, "🍦"),
            (ids[8], "Glace Magnum", 4.00, "🍫"),

            # Produits Locaux (10)
            (ids[9], "Saucisson artisanal", 6.00, "🥓"),
            (ids[9], "Fromage local", 5.00, "🧀"),
            (ids[9], "Pain maison", 3.00, "🍞"),
        ]

        cur.executemany(
            "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (%s, %s, %s, %s)" if IS_POSTGRES else
            "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (?, ?, ?, ?)",
            articles_defaut
        )

    db.commit()
    db.close()
