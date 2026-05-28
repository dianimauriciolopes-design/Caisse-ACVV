from flask import Flask, render_template, request, jsonify, send_file
from database import get_db, init_db, IS_POSTGRES

import json
import os
import io
import qrcode
from datetime import datetime

app = Flask(__name__)

# ───────── HELPER SQL ─────────
def exec_query(cur, pg, sqlite, params=()):
    if IS_POSTGRES:
        cur.execute(pg, params)
    else:
        cur.execute(sqlite, params)

# ───────── PAGES ─────────

@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM stands WHERE actif = TRUE" if IS_POSTGRES else
            "SELECT * FROM stands WHERE actif = 1")

    stands = cur.fetchall()
    db.close()
    return render_template("index.html", stands=stands)

@app.route("/caisse/<int:stand_id>")
def caisse(stand_id):
    db = get_db()
    cur = db.cursor()

    exec_query(cur,
        "SELECT * FROM stands WHERE id = %s",
        "SELECT * FROM stands WHERE id = ?",
        (stand_id,)
    )
    stand = cur.fetchone()

    exec_query(cur,
        "SELECT * FROM articles WHERE stand_id = %s AND actif = TRUE",
        "SELECT * FROM articles WHERE stand_id = ? AND actif = 1",
        (stand_id,)
    )

    articles = cur.fetchall()

    db.close()

    if not stand:
        return "Stand introuvable", 404

    return render_template("caisse.html", stand=stand, articles=articles)

@app.route("/admin")
def admin():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM stands")
    stands = cur.fetchall()

    cur.execute("""
        SELECT a.*, s.nom AS stand_nom
        FROM articles a
        JOIN stands s ON a.stand_id = s.id
        ORDER BY s.id
    """)
    articles = cur.fetchall()

    db.close()
    return render_template("admin.html", stands=stands, articles=articles)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ───────── API TRANSACTIONS ─────────

@app.route("/api/transaction", methods=["POST"])
def transaction():
    data = request.json
    db = get_db()
    cur = db.cursor()

    # récupérer nom du stand
    exec_query(cur,
        "SELECT nom FROM stands WHERE id = %s",
        "SELECT nom FROM stands WHERE id = ?",
        (data["stand_id"],)
    )
    stand = cur.fetchone()

    if not stand:
        return jsonify({"erreur": "stand introuvable"}), 404

    if IS_POSTGRES:
        cur.execute("""
            INSERT INTO transactions 
            (stand_id, stand_nom, montant, mode_paiement, detail_articles)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data["stand_id"],
            stand["nom"],
            data["montant"],
            data["mode_paiement"],
            json.dumps(data.get("articles", []))
        ))
        tid = cur.fetchone()["id"]
    else:
        cur.execute("""
            INSERT INTO transactions 
            (stand_id, stand_nom, montant, mode_paiement, detail_articles)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["stand_id"],
            stand["nom"],
            data["montant"],
            data["mode_paiement"],
            json.dumps(data.get("articles", []))
        ))
        tid = cur.lastrowid

    db.commit()
    db.close()

    return jsonify({"success": True, "id": tid})

@app.route("/api/transactions")
def transactions():
    db = get_db()
    cur = db.cursor()

    if IS_POSTGRES:
        cur.execute("""
            SELECT * FROM transactions
            WHERE statut != 'annule'
            ORDER BY created_at DESC
        """)
    else:
        cur.execute("""
            SELECT * FROM transactions
            WHERE statut != 'annule'
            ORDER BY created_at DESC
        """)

    rows = cur.fetchall()
    db.close()

    # convertir JSON articles
    result = []
    for t in rows:
        result.append({
            "id": t["id"],
            "stand_nom": t["stand_nom"],
            "montant": float(t["montant"]),
            "mode_paiement": t["mode_paiement"],
            "statut": t["statut"],
            "created_at": t["created_at"],
            "detail_articles": json.loads(t["detail_articles"] or "[]")
        })

    return jsonify(result)

@app.route("/api/transaction/<int:t_id>/annuler", methods=["POST"])
def annuler(t_id):
    db = get_db()
    cur = db.cursor()

    exec_query(cur,
        "UPDATE transactions SET statut = 'annule' WHERE id = %s",
        "UPDATE transactions SET statut = 'annule' WHERE id = ?",
        (t_id,)
    )

    db.commit()
    db.close()

    return jsonify({"success": True})


# ───────── API ARTICLES ─────────

@app.route("/api/article", methods=["POST"])
def ajouter_article():
    data = request.json

    db = get_db()
    cur = db.cursor()

    exec_query(cur,
        "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (%s, %s, %s, %s)",
        "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (?, ?, ?, ?)",
        (data["stand_id"], data["nom"], data["prix"], data.get("emoji", "🍺"))
    )

    db.commit()
    db.close()

    return jsonify({"success": True})


@app.route("/api/article/<int:a_id>", methods=["DELETE"])
def supprimer_article(a_id):
    db = get_db()
    cur = db.cursor()

    exec_query(cur,
        "UPDATE articles SET actif = FALSE WHERE id = %s",
        "UPDATE articles SET actif = 0 WHERE id = ?",
        (a_id,)
    )

    db.commit()
    db.close()

    return jsonify({"success": True})


# ───────── API STANDS ─────────

@app.route("/api/stand", methods=["POST"])
def ajouter_stand():
    data = request.json

    db = get_db()
    cur = db.cursor()

    exec_query(cur,
        "INSERT INTO stands (nom, description) VALUES (%s, %s)",
        "INSERT INTO stands (nom, description) VALUES (?, ?)",
        (data["nom"], data.get("description", ""))
    )

    db.commit()
    db.close()

    return jsonify({"success": True})


# ───────── STATS ─────────

@app.route("/api/stats")
def stats():
    db = get_db()
    cur = db.cursor()

    # GLOBAL
    cur.execute("""
        SELECT 
            COUNT(*) as nb,
            COALESCE(SUM(montant), 0) as total,
            COALESCE(SUM(CASE WHEN mode_paiement='cash' THEN montant ELSE 0 END), 0) as cash,
            COALESCE(SUM(CASE WHEN mode_paiement='twint' THEN montant ELSE 0 END), 0) as twint
        FROM transactions
        WHERE statut != 'annule'
    """)
    global_data = cur.fetchone()

    # PAR STAND
    cur.execute("""
        SELECT stand_nom, stand_id,
            COUNT(*) as nb,
            SUM(montant) as total,
            SUM(CASE WHEN mode_paiement='cash' THEN montant ELSE 0 END) as cash,
            SUM(CASE WHEN mode_paiement='twint' THEN montant ELSE 0 END) as twint
        FROM transactions
        WHERE statut != 'annule'
        GROUP BY stand_id, stand_nom
        ORDER BY total DESC
    """)
    stands = cur.fetchall()

    # PAR HEURE
    if IS_POSTGRES:
        cur.execute("""
            SELECT EXTRACT(HOUR FROM created_at) as heure,
                   COUNT(*) as nb,
                   SUM(montant) as total
            FROM transactions
            WHERE statut != 'annule'
            GROUP BY heure
            ORDER BY heure
        """)
    else:
        cur.execute("""
            SELECT strftime('%H', created_at) as heure,
                   COUNT(*) as nb,
                   SUM(montant) as total
            FROM transactions
            WHERE statut != 'annule'
            GROUP BY heure
            ORDER BY heure
        """)

    heures = cur.fetchall()

    db.close()

    return jsonify({
        "global": {
            "nb_transactions": global_data["nb"],
            "total": float(global_data["total"]),
            "total_cash": float(global_data["cash"]),
            "total_twint": float(global_data["twint"])
        },
        "par_stand": [
            {
                "stand_id": s["stand_id"],
                "stand_nom": s["stand_nom"],
                "nb": s["nb"],
                "total": float(s["total"]),
                "cash": float(s["cash"]),
                "twint": float(s["twint"])
            } for s in stands
        ],
        "par_heure": [
            {
                "heure": int(h["heure"]),
                "nb": h["nb"],
                "total": float(h["total"])
            } for h in heures
        ]
    })

# ───────── QR ─────────

@app.route("/api/qr-image")
def qr():
    url = request.args.get("url", "https://pay.twint.ch")

    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf)
    buf.seek(0)

    return send_file(buf, mimetype="image/png")

# ───────── RUN ─────────

if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)