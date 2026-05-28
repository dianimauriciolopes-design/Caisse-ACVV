from flask import Flask, render_template, request, jsonify, send_file
from database import get_db, init_db
import json
import qrcode
import io
import os
import socket
from datetime import datetime

app = Flask(__name__)

# ─── PAGES ─────────────────────────────────────────

@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM stands WHERE actif = 1")
    stands = cur.fetchall()
    db.close()
    return render_template("index.html", stands=stands)

@app.route("/caisse/<int:stand_id>")
def caisse(stand_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM stands WHERE id = %s", (stand_id,))
    stand = cur.fetchone()

    cur.execute(
        "SELECT * FROM articles WHERE stand_id = %s AND actif = 1 ORDER BY prix",
        (stand_id,)
    )
    articles = cur.fetchall()

    db.close()

    if not stand:
        return "Stand introuvable", 404

    return render_template("caisse.html", stand=stand, articles=articles)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/admin")
def admin():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM stands")
    stands = cur.fetchall()

    cur.execute("""
        SELECT a.*, s.nom as stand_nom 
        FROM articles a JOIN stands s ON a.stand_id = s.id
        ORDER BY s.id, a.prix
    """)
    articles = cur.fetchall()

    db.close()
    return render_template("admin.html", stands=stands, articles=articles)

# ─── TRANSACTIONS ─────────────────────────────────

@app.route("/api/transaction", methods=["POST"])
def creer_transaction():
    data = request.json

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT nom FROM stands WHERE id = %s", (data["stand_id"],))
    stand = cur.fetchone()

    if not stand:
        db.close()
        return jsonify({"erreur": "Stand introuvable"}), 404

    cur.execute("""
        INSERT INTO transactions 
        (stand_id, stand_nom, montant, mode_paiement, detail_articles, note)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        data["stand_id"],
        stand[0],
        data["montant"],
        data["mode_paiement"],
        json.dumps(data.get("articles", [])),
        data.get("note", "")
    ))

    transaction_id = cur.fetchone()[0]

    db.commit()
    db.close()

    return jsonify({"success": True, "transaction_id": transaction_id})

@app.route("/api/transactions")
def liste_transactions():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT * FROM transactions 
        WHERE statut != 'annule' AND DATE(created_at) = CURRENT_DATE
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    db.close()

    result = []
    for t in rows:
        result.append({
            "id": t[0],
            "stand_id": t[1],
            "stand_nom": t[2],
            "montant": float(t[3]),
            "mode_paiement": t[4],
            "statut": t[5],
            "detail_articles": json.loads(t[6]) if t[6] else [],
            "note": t[7],
            "created_at": str(t[8])
        })

    return jsonify(result)

@app.route("/api/transaction/<int:t_id>/annuler", methods=["POST"])
def annuler_transaction(t_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("UPDATE transactions SET statut = 'annule' WHERE id = %s", (t_id,))

    db.commit()
    db.close()
    return jsonify({"success": True})

# ─── STATS ─────────────────────────────────────────

@app.route("/api/stats")
def stats():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT 
            COUNT(*),
            COALESCE(SUM(montant), 0),
            COALESCE(SUM(CASE WHEN mode_paiement='cash' THEN montant ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN mode_paiement='twint' THEN montant ELSE 0 END), 0)
        FROM transactions 
        WHERE statut != 'annule' AND DATE(created_at) = CURRENT_DATE
    """)
    row = cur.fetchone()

    cur.execute("""
        SELECT stand_nom, stand_id,
            COUNT(*),
            SUM(montant),
            SUM(CASE WHEN mode_paiement='cash' THEN montant ELSE 0 END),
            SUM(CASE WHEN mode_paiement='twint' THEN montant ELSE 0 END)
        FROM transactions 
        WHERE statut != 'annule' AND DATE(created_at) = CURRENT_DATE
        GROUP BY stand_id, stand_nom
        ORDER BY SUM(montant) DESC
    """)
    par_stand = cur.fetchall()

    cur.execute("""
        SELECT EXTRACT(HOUR FROM created_at),
               COUNT(*),
               SUM(montant)
        FROM transactions
        WHERE statut != 'annule' AND DATE(created_at) = CURRENT_DATE
        GROUP BY 1
        ORDER BY 1
    """)
    par_heure = cur.fetchall()

    db.close()

    return jsonify({
        "global": {
            "nb_transactions": row[0],
            "total": float(row[1]),
            "total_cash": float(row[2]),
            "total_twint": float(row[3])
        },
        "par_stand": [
            {
                "stand_id": s[1],
                "stand_nom": s[0],
                "nb": s[2],
                "total": float(s[3]),
                "cash": float(s[4]),
                "twint": float(s[5])
            } for s in par_stand
        ],
        "par_heure": [
            {"heure": int(h[0]), "nb": h[1], "total": float(h[2])}
            for h in par_heure
        ]
    })

# ─── LANCEMENT ─────────────────────────────────────

if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 8080))

    print("🚀 App démarrée")
    app.run(host="0.0.0.0", port=port)