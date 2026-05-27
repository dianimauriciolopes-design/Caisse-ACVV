from flask import Flask, render_template, request, jsonify, send_file
from database import get_db, init_db
import json
import qrcode
import io
import os
import socket
from datetime import datetime

app = Flask(__name__)

# ─── PAGES PRINCIPALES ────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Page d'accueil : sélection du stand"""
    db = get_db()
    stands = db.execute("SELECT * FROM stands WHERE actif = 1").fetchall()
    db.close()
    return render_template("index.html", stands=stands)

@app.route("/caisse/<int:stand_id>")
def caisse(stand_id):
    """Interface caisse pour un stand"""
    db = get_db()
    stand = db.execute("SELECT * FROM stands WHERE id = ?", (stand_id,)).fetchone()
    articles = db.execute(
        "SELECT * FROM articles WHERE stand_id = ? AND actif = 1 ORDER BY prix",
        (stand_id,)
    ).fetchall()
    db.close()
    if not stand:
        return "Stand introuvable", 404
    return render_template("caisse.html", stand=stand, articles=articles)

@app.route("/dashboard")
def dashboard():
    """Dashboard récapitulatif pour l'organisateur"""
    return render_template("dashboard.html")

@app.route("/admin")
def admin():
    """Page d'administration (stands, articles)"""
    db = get_db()
    stands = db.execute("SELECT * FROM stands").fetchall()
    articles = db.execute("""
        SELECT a.*, s.nom as stand_nom 
        FROM articles a JOIN stands s ON a.stand_id = s.id
        ORDER BY s.id, a.prix
    """).fetchall()
    db.close()
    return render_template("admin.html", stands=stands, articles=articles)

# ─── API TRANSACTIONS ─────────────────────────────────────────────────────────

@app.route("/api/transaction", methods=["POST"])
def creer_transaction():
    """Enregistre un paiement"""
    data = request.json
    stand_id = data.get("stand_id")
    montant = data.get("montant")
    mode = data.get("mode_paiement")  # 'cash' ou 'twint'
    articles = data.get("articles", [])
    note = data.get("note", "")

    if not all([stand_id, montant, mode]):
        return jsonify({"erreur": "Données manquantes"}), 400

    db = get_db()
    stand = db.execute("SELECT nom FROM stands WHERE id = ?", (stand_id,)).fetchone()
    if not stand:
        db.close()
        return jsonify({"erreur": "Stand introuvable"}), 404

    db.execute("""
        INSERT INTO transactions (stand_id, stand_nom, montant, mode_paiement, detail_articles, note)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (stand_id, stand["nom"], montant, mode, json.dumps(articles, ensure_ascii=False), note))
    transaction_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.commit()
    db.close()

    return jsonify({"success": True, "transaction_id": transaction_id})

@app.route("/api/transactions")
def liste_transactions():
    """Retourne toutes les transactions du jour (ou toutes)"""
    filtre = request.args.get("filtre", "aujourd_hui")
    stand_id = request.args.get("stand_id")

    db = get_db()
    query = "SELECT * FROM transactions WHERE statut != 'annule'"
    params = []

    if filtre == "aujourd_hui":
        query += " AND DATE(created_at) = DATE('now', 'localtime')"
    
    if stand_id:
        query += " AND stand_id = ?"
        params.append(stand_id)

    query += " ORDER BY created_at DESC"
    transactions = db.execute(query, params).fetchall()
    db.close()

    result = []
    for t in transactions:
        result.append({
            "id": t["id"],
            "stand_id": t["stand_id"],
            "stand_nom": t["stand_nom"],
            "montant": t["montant"],
            "mode_paiement": t["mode_paiement"],
            "statut": t["statut"],
            "detail_articles": json.loads(t["detail_articles"]) if t["detail_articles"] else [],
            "note": t["note"],
            "created_at": t["created_at"]
        })
    return jsonify(result)

@app.route("/api/transaction/<int:t_id>/annuler", methods=["POST"])
def annuler_transaction(t_id):
    """Annule une transaction"""
    db = get_db()
    db.execute("UPDATE transactions SET statut = 'annule' WHERE id = ?", (t_id,))
    db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/api/stats")
def stats():
    """Statistiques du jour pour le dashboard"""
    db = get_db()
    
    # Totaux globaux
    row = db.execute("""
        SELECT 
            COUNT(*) as nb_transactions,
            COALESCE(SUM(montant), 0) as total,
            COALESCE(SUM(CASE WHEN mode_paiement='cash' THEN montant ELSE 0 END), 0) as total_cash,
            COALESCE(SUM(CASE WHEN mode_paiement='twint' THEN montant ELSE 0 END), 0) as total_twint
        FROM transactions 
        WHERE statut != 'annule' AND DATE(created_at) = DATE('now', 'localtime')
    """).fetchone()

    # Par stand
    par_stand = db.execute("""
        SELECT stand_nom, stand_id,
            COUNT(*) as nb,
            SUM(montant) as total,
            SUM(CASE WHEN mode_paiement='cash' THEN montant ELSE 0 END) as cash,
            SUM(CASE WHEN mode_paiement='twint' THEN montant ELSE 0 END) as twint
        FROM transactions 
        WHERE statut != 'annule' AND DATE(created_at) = DATE('now', 'localtime')
        GROUP BY stand_id, stand_nom
        ORDER BY total DESC
    """).fetchall()

    # Par heure (graphique)
    par_heure = db.execute("""
        SELECT strftime('%H', created_at, 'localtime') as heure,
               COUNT(*) as nb,
               SUM(montant) as total
        FROM transactions
        WHERE statut != 'annule' AND DATE(created_at) = DATE('now', 'localtime')
        GROUP BY heure
        ORDER BY heure
    """).fetchall()

    db.close()

    return jsonify({
        "global": {
            "nb_transactions": row["nb_transactions"],
            "total": round(row["total"], 2),
            "total_cash": round(row["total_cash"], 2),
            "total_twint": round(row["total_twint"], 2)
        },
        "par_stand": [
            {
                "stand_id": s["stand_id"],
                "stand_nom": s["stand_nom"],
                "nb": s["nb"],
                "total": round(s["total"], 2),
                "cash": round(s["cash"], 2),
                "twint": round(s["twint"], 2)
            } for s in par_stand
        ],
        "par_heure": [
            {"heure": h["heure"], "nb": h["nb"], "total": round(h["total"], 2)}
            for h in par_heure
        ]
    })

# ─── API ARTICLES & STANDS ───────────────────────────────────────────────────

@app.route("/api/articles/<int:stand_id>")
def articles_stand(stand_id):
    db = get_db()
    articles = db.execute(
        "SELECT * FROM articles WHERE stand_id = ? AND actif = 1 ORDER BY prix",
        (stand_id,)
    ).fetchall()
    db.close()
    return jsonify([dict(a) for a in articles])

@app.route("/api/article", methods=["POST"])
def ajouter_article():
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO articles (stand_id, nom, prix, emoji) VALUES (?, ?, ?, ?)",
        (data["stand_id"], data["nom"], data["prix"], data.get("emoji", "🍺"))
    )
    db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/api/article/<int:a_id>", methods=["DELETE"])
def supprimer_article(a_id):
    db = get_db()
    db.execute("UPDATE articles SET actif = 0 WHERE id = ?", (a_id,))
    db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/api/stand", methods=["POST"])
def ajouter_stand():
    data = request.json
    db = get_db()
    db.execute(
        "INSERT INTO stands (nom, description) VALUES (?, ?)",
        (data["nom"], data.get("description", ""))
    )
    db.commit()
    db.close()
    return jsonify({"success": True})

# ─── QR CODE TWINT ───────────────────────────────────────────────────────────

@app.route("/qr")
def afficher_qr():
    """Page avec le QR TWINT à afficher au client"""
    montant = request.args.get("montant", "")
    stand = request.args.get("stand", "Paiement TWINT")
    return render_template("qr.html", montant=montant, stand=stand)

@app.route("/api/qr-image")
def generer_qr():
    """Génère un QR code pour une URL ou un texte"""
    contenu = request.args.get("url", "https://pay.twint.ch")  # remplace par ton lien TWINT asso
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(contenu)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

# ─── EXPORT ──────────────────────────────────────────────────────────────────

@app.route("/api/export/csv")
def export_csv():
    """Export CSV des transactions du jour"""
    db = get_db()
    transactions = db.execute("""
        SELECT id, stand_nom, montant, mode_paiement, statut, note, created_at
        FROM transactions
        WHERE DATE(created_at) = DATE('now', 'localtime')
        ORDER BY created_at
    """).fetchall()
    db.close()

    lines = ["ID,Stand,Montant (CHF),Mode,Statut,Note,Heure"]
    for t in transactions:
        lines.append(f'{t["id"]},{t["stand_nom"]},{t["montant"]:.2f},{t["mode_paiement"]},{t["statut"]},"{t["note"] or ""}",{t["created_at"]}')

    csv_content = "\n".join(lines)
    buf = io.BytesIO(csv_content.encode("utf-8-sig"))
    date_str = datetime.now().strftime("%Y-%m-%d")
    return send_file(buf, mimetype="text/csv", as_attachment=True,
                     download_name=f"tournoi_{date_str}.csv")


# ─── Récupération de l'IP locale ─────────────────────────────────────────────
def get_local_ip():
    """
    Récupère l'adresse IP locale de l'appareil.
    Retourne '127.0.0.1' si l'adresse ne peut pas être déterminée.
    """
    try:
        # Crée un socket UDP temporaire pour déterminer l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # On se connecte à une adresse externe (Google DNS) sans envoyer de données
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"Erreur lors de la récupération de l'IP : {e}")
        return "127.0.0.1"  # Valeur par défaut

# Stocker l'IP dans une variable
DEVICE_IP = get_local_ip()

# Afficher l'IP
print(f"L'adresse IP locale de l'appareil est : {DEVICE_IP}")

# ─── LANCEMENT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("\n🏆 Tournoi Paiement démarré !")
    print(f"📱 Caisse    →  http://{DEVICE_IP}:5000/")
    print(f"📊 Dashboard →  http://{DEVICE_IP}:5000/dashboard")
    print(f"⚙️  Admin     →  http://{DEVICE_IP}:5000/admin\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
