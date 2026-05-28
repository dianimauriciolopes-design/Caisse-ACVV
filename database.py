import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Table des stands
    c.execute("""
        CREATE TABLE IF NOT EXISTS stands (
            id SERIAL PRIMARY KEY,
            nom TEXT NOT NULL,
            description TEXT,
            actif INTEGER DEFAULT 1
        )
    """)

    # Table des articles
    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            stand_id INTEGER NOT NULL,
            nom TEXT NOT NULL,
            prix REAL NOT NULL,
            emoji TEXT DEFAULT '🍺',
            actif INTEGER DEFAULT 1,
            FOREIGN KEY (stand_id) REFERENCES stands(id)
        )
    """)

    # Table des transactions
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            stand_id INTEGER NOT NULL,
            stand_nom TEXT NOT NULL,
            montant REAL NOT NULL,
            mode_paiement TEXT NOT NULL,
            statut TEXT DEFAULT 'confirme',
            detail_articles TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stand_id) REFERENCES stands(id)
        )
    """)

    # Vérifier si données déjà présentes
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
            (2, "Bière 50cl", 4.00, "🍺"),
            (2, "Soft 33cl", 2.50, "🥤"),
            (2, "Eau 50cl", 1.50, "💧"),
        ]

        c.executemany(
            "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (%s, %s, %s, %s)",
            articles_defaut
        )

    conn.commit()
    conn.close()

    print("✅ Base PostgreSQL initialisée")
