
# Caisse-ACVV
Gestion de paiement par twint ou par cash pour l'ACCVS
=======
# 🏆 Tournoi Paiement — Guide de démarrage

## Installation (une seule fois)

```bash
# 1. Ouvre un terminal dans VS Code (Ctrl+`)
cd tournoi-paiement

# 2. Installe les dépendances Python
pip install flask qrcode pillow

# 3. Lance le serveur
python app.py
```

## Accès depuis les tablettes

Trouve l'IP de ton PC (Windows) :
```
ipconfig       → cherche "Adresse IPv4" ex: 192.168.1.42
```

Sur chaque tablette (même réseau WiFi) :

| Appareil | URL |
|---|---|
| Tablettes stands | `http://192.168.1.42:5000/` |
| Dashboard organisateur | `http://192.168.1.42:5000/dashboard` |
| Administration | `http://192.168.1.42:5000/admin` |

---

## Configurer ton QR TWINT

Dans `app.py`, ligne ~130, remplace :
```python
TWINT_URL = "https://pay.twint.ch"
```
par le vrai lien TWINT de ton association.

> **Comment trouver ton lien TWINT ?**  
> Ouvre TWINT → Mon profil → Partager → Copier le lien

---

## Structure du projet

```
tournoi-paiement/
├── app.py          ← Serveur principal (Flask)
├── database.py     ← Base de données SQLite
├── tournoi.db      ← Fichier DB (créé au démarrage)
├── requirements.txt
└── templates/
    ├── index.html   ← Sélection du stand
    ├── caisse.html  ← Interface caisse (tablette)
    ├── dashboard.html ← Récapitulatif organisateur
    ├── admin.html   ← Gestion articles/stands
    └── qr.html      ← Affichage QR TWINT
```

---

## Workflow le jour du tournoi

1. **Matin** → Lance `python app.py` sur ton PC
2. **Stands** → Chaque tablette ouvre le navigateur sur `/`
3. **Pendant** → L'organisateur surveille `/dashboard` (refresh auto 15s)
4. **Fin de journée** → Export CSV depuis le dashboard
5. **Compte-rendu** → Ouvre le CSV dans Excel

---

## Personnaliser les articles

Via l'interface : `http://[IP]:5000/admin`  
Ou directement dans `database.py` → `articles_defaut`

---

## Arrêter le serveur

```
Ctrl + C  dans le terminal VS Code
```

Les données sont sauvegardées dans `tournoi.db` — elles survivent aux redémarrages.