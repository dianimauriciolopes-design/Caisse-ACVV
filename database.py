import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tournoi.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Table des stands
    c.execute("""
        CREATE TABLE IF NOT EXISTS stands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            description TEXT,
            actif INTEGER DEFAULT 1
        )
    """)

    # Table des articles/produits
    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stand_id INTEGER NOT NULL,
            stand_nom TEXT NOT NULL,
            montant REAL NOT NULL,
            mode_paiement TEXT NOT NULL,  -- 'cash' ou 'twint'
            statut TEXT DEFAULT 'confirme',  -- 'confirme', 'en_attente', 'annule'
            detail_articles TEXT,  -- JSON string
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (stand_id) REFERENCES stands(id)
        )
    """)

    # Stands par défaut
    c.execute("SELECT COUNT(*) FROM stands")
    if c.fetchone()[0] == 0:
        stands_defaut = [
            ("Bar Principal", "Bières, softs, vins"),
            ("Buvette Terrain A", "Boissons terrain A"),
            ("Buvette Terrain B", "Boissons terrain B"),
            ("Restauration", "Grillades, sandwichs"),
            ("Confiserie", "Snacks, bonbons"),
        ]
        c.executemany("INSERT INTO stands (nom, description) VALUES (?, ?)", stands_defaut)

        # Articles par défaut pour le Bar Principal (stand 1)
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
            (3, "Bière 50cl", 4.00, "🍺"),
            (3, "Soft 33cl", 2.50, "🥤"),
            (3, "Eau 50cl", 1.50, "💧"),
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
    print("✅ Base de données initialisée.")
