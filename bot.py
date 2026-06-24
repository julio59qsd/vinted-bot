import time
import json
import os
import threading
import requests
from vinted_scraper import VintedScraper
from flask import Flask, jsonify, request

TELEGRAM_TOKEN = "8728826832:AAHJNErIeLR7i6N0-f2QrQUu0wSF9_hZ9Eg"
TELEGRAM_CHAT_ID = "7794106017"
INTERVALLE_SECONDES = 60
FICHIER_VUS = "/tmp/annonces_vues.json"
FICHIER_FILTRES = "/tmp/filtres.json"

COULEURS = {
    "rouge": "5", "noir": "1", "blanc": "12", "bleu": "3",
    "vert": "6", "jaune": "7", "rose": "9", "gris": "4",
    "marron": "2", "orange": "8", "violet": "10", "beige": "11"
}

ETATS = {
    "neuf avec etiquette": "6", "neuf sans etiquette": "1",
    "tres bon etat": "2", "bon etat": "3", "satisfaisant": "4"
}

app = Flask(__name__)

HTML = open("/app/index.html").read() if os.path.exists("/app/index.html") else ""

def charger_filtres():
    if os.path.exists(FICHIER_FILTRES):
        with open(FICHIER_FILTRES, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_filtres(filtres):
    with open(FICHIER_FILTRES, "w", encoding="utf-8") as f:
        json.dump(filtres, f, ensure_ascii=False, indent=2)

def charger_vus():
    if os.path.exists(FICHIER_VUS):
        with open(FICHIER_VUS, "r") as f:
            return set(json.load(f))
    return set()

def sauvegarder_vus(vus):
    with open(FICHIER_VUS, "w") as f:
        json.dump(list(vus), f)

def envoyer_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"})
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def bot_loop():
    print("Bot demarre...")
    envoyer_telegram("Bot Vinted demarre ! Gere tes alertes sur l'interface web.")
    scraper = VintedScraper("https://www.vinted.fr")
    annonces_vues = charger_vus()
    while True:
        filtres = charger_filtres()
        for filtre in filtres:
            if not filtre.get("actif", True):
                continue
            try:
                params = {"search_text": filtre["recherche"], "order": "newest_first", "per_page": 20}
                if filtre.get("couleur"):
                    params["color_ids[]"] = COULEURS.get(filtre["couleur"].lower(), "")
                if filtre.get("etat"):
                    params["status_ids[]"] = ETATS.get(filtre["etat"].lower(), "")
                if filtre.get("prix_max"):
                    params["price_to"] = filtre["prix_max"]
                items = scraper.search(params)
                for item in items:
                    item_id = str(item.id)
                    cle = f"{filtre['id']}_{item_id}"
                    if cle not in annonces_vues:
                        annonces_vues.add(cle)
                        prix = f"{item.price} EUR" if item.price else "Prix inconnu"
                        taille = item.size_title if item.size_title else "-"
                        lien = f"https://www.vinted.fr/items/{item_id}"
                        message = (
                            f"Nouvelle annonce !\n"
                            f"Recherche : {filtre['nom']}\n\n"
                            f"{item.title}\n"
                            f"{prix}\n"
                            f"Taille : {taille}\n"
                            f"Voir l'annonce : {lien}"
                        )
                        envoyer_telegram(message)
                        print(f"Envoye : {item.title}")
                sauvegarder_vus(annonces_vues)
            except Exception as e:
                print(f"Erreur filtre {filtre.get('nom')} : {e}")
        time.sleep(INTERVALLE_SECONDES)

@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vinted Bot</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:#0f0f13;color:#e8e8f0;min-height:100vh;padding:20px}
.header{text-align:center;padding:32px 0 24px}
.header h1{font-size:28px;font-weight:700;background:linear-gradient(135deg,#09b3ef,#7b61ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:6px}
.header p{color:#6b6b80;font-size:14px}
.status-bar{display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:32px;font-size:13px;color:#6b6b80}
.dot{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.card{background:#1a1a24;border:1px solid #2a2a38;border-radius:16px;padding:24px;max-width:600px;margin:0 auto 20px}
.card h2{font-size:16px;font-weight:600;margin-bottom:20px;color:#c8c8e0}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.form-full{grid-column:1/-1}
label{display:block;font-size:12px;color:#6b6b80;margin-bottom:6px;font-weight:500;text-transform:uppercase;letter-spacing:.05em}
input,select{width:100%;background:#0f0f13;border:1px solid #2a2a38;border-radius:10px;padding:10px 14px;color:#e8e8f0;font-size:14px;font-family:'Inter',sans-serif;outline:none;transition:border-color .2s}
input:focus,select:focus{border-color:#09b3ef}
select option{background:#1a1a24}
.btn-add{width:100%;background:linear-gradient(135deg,#09b3ef,#7b61ff);border:none;border-radius:10px;padding:12px;color:white;font-size:15px;font-weight:600;cursor:pointer;margin-top:8px;transition:opacity .2s}
.btn-add:hover{opacity:.85}
.filtres-list{max-width:600px;margin:0 auto}
.filtre-card{background:#1a1a24;border:1px solid #2a2a38;border-radius:14px;padding:18px 20px;margin-bottom:12px;display:flex;align-items:center;gap:16px}
.filtre-card.inactif{opacity:.45}
.filtre-info{flex:1}
.filtre-nom{font-weight:600;font-size:15px;margin-bottom:6px}
.filtre-tags{display:flex;flex-wrap:wrap;gap:6px}
.tag{background:#0f0f13;border:1px solid #2a2a38;border-radius:20px;padding:3px 10px;font-size:12px;color:#8888a0}
.tag.couleur{border-color:#7b61ff44;color:#9b81ff}
.tag.etat{border-color:#09b3ef44;color:#09b3ef}
.tag.prix{border-color:#22c55e44;color:#22c55e}
.filtre-actions{display:flex;gap:8px;flex-shrink:0}
.btn-icon{width:36px;height:36px;border-radius:8px;border:1px solid #2a2a38;background:#0f0f13;color:#8888a0;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;transition:all .2s}
.btn-icon:hover{border-color:#09b3ef;color:#09b3ef}
.btn-icon.danger:hover{border-color:#ef4444;color:#ef4444}
.empty{text-align:center;color:#3a3a50;font-size:14px;padding:40px 0}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(80px);background:#22c55e;color:white;padding:12px 24px;border-radius:30px;font-size:14px;font-weight:500;transition:transform .3s;z-index:999}
.toast.show{transform:translateX(-50%) translateY(0)}
</style>
</head>
<body>
<div class="header"><h1>Vinted Bot</h1><p>Tes alertes automatiques Vinted</p></div>
<div class="status-bar"><div class="dot"></div>Bot actif - alertes Telegram activees</div>
<div class="card">
  <h2>Nouvelle alerte</h2>
  <div class="form-grid">
    <div class="form-full"><label>Nom de l'alerte</label><input type="text" id="nom" placeholder="ex: Ralph Lauren rouge"></div>
    <div class="form-full"><label>Recherche</label><input type="text" id="recherche" placeholder="ex: ralph lauren polo"></div>
    <div><label>Couleur</label><select id="couleur"><option value="">Toutes</option><option value="rouge">Rouge</option><option value="noir">Noir</option><option value="blanc">Blanc</option><option value="bleu">Bleu</option><option value="vert">Vert</option><option value="jaune">Jaune</option><option value="rose">Rose</option><option value="gris">Gris</option><option value="marron">Marron</option><option value="orange">Orange</option><option value="violet">Violet</option><option value="beige">Beige</option></select></div>
    <div><label>Etat</label><select id="etat"><option value="">Tous</option><option value="neuf avec etiquette">Neuf avec etiquette</option><option value="neuf sans etiquette">Neuf sans etiquette</option><option value="tres bon etat">Tres bon etat</option><option value="bon etat">Bon etat</option><option value="satisfaisant">Satisfaisant</option></select></div>
    <div><label>Taille</label><input type="text" id="taille" placeholder="ex: M, L, 42"></div>
    <div><label>Prix max (EUR)</label><input type="number" id="prix_max" placeholder="ex: 50"></div>
  </div>
  <button class="btn-add" onclick="ajouterFiltre()">Creer l'alerte</button>
</div>
<div class="filtres-list" id="filtres-list"></div>
<div class="toast" id="toast"></div>
<script>
async function chargerFiltres(){const res=await fetch('/api/filtres');const filtres=await res.json();const c=document.getElementById('filtres-list');if(!filtres.length){c.innerHTML='<div class="empty">Aucune alerte.<br>Cree ta premiere alerte ci-dessus !</div>';return}c.innerHTML=filtres.map(f=>`<div class="filtre-card ${f.actif?'':'inactif'}"><div class="filtre-info"><div class="filtre-nom">${f.nom}</div><div class="filtre-tags"><span class="tag">${f.recherche}</span>${f.couleur?`<span class="tag couleur">${f.couleur}</span>`:''} ${f.etat?`<span class="tag etat">${f.etat}</span>`:''} ${f.prix_max?`<span class="tag prix">max ${f.prix_max}EUR</span>`:''}</div></div><div class="filtre-actions"><button class="btn-icon" onclick="toggleFiltre('${f.id}')">${f.actif?'⏸':'▶'}</button><button class="btn-icon danger" onclick="supprimerFiltre('${f.id}')">🗑</button></div></div>`).join('')}
async function ajouterFiltre(){const r=document.getElementById('recherche').value.trim();if(!r){showToast('Saisis une recherche !','#ef4444');return}await fetch('/api/filtres',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nom:document.getElementById('nom').value.trim()||r,recherche:r,couleur:document.getElementById('couleur').value,etat:document.getElementById('etat').value,taille:document.getElementById('taille').value,prix_max:document.getElementById('prix_max').value})});['nom','recherche','taille','prix_max'].forEach(id=>document.getElementById(id).value='');document.getElementById('couleur').value='';document.getElementById('etat').value='';showToast('Alerte creee !');chargerFiltres()}
async function supprimerFiltre(id){if(!confirm('Supprimer ?'))return;await fetch('/api/filtres/'+id,{method:'DELETE'});showToast('Supprime');chargerFiltres()}
async function toggleFiltre(id){await fetch('/api/filtres/'+id+'/toggle',{method:'POST'});chargerFiltres()}
function showToast(m,c='#22c55e'){const t=document.getElementById('toast');t.textContent=m;t.style.background=c;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2500)}
chargerFiltres();setInterval(chargerFiltres,10000);
</script>
</body>
</html>"""

@app.route("/api/filtres", methods=["GET"])
def get_filtres():
    return jsonify(charger_filtres())

@app.route("/api/filtres", methods=["POST"])
def add_filtre():
    data = request.json
    filtres = charger_filtres()
    nouveau = {"id": str(int(time.time())), "nom": data.get("nom", data.get("recherche")), "recherche": data["recherche"], "couleur": data.get("couleur", ""), "etat": data.get("etat", ""), "taille": data.get("taille", ""), "prix_max": data.get("prix_max", ""), "actif": True}
    filtres.append(nouveau)
    sauvegarder_filtres(filtres)
    return jsonify({"ok": True, "filtre": nouveau})

@app.route("/api/filtres/<filtre_id>", methods=["DELETE"])
def delete_filtre(filtre_id):
    sauvegarder_filtres([f for f in charger_filtres() if f["id"] != filtre_id])
    return jsonify({"ok": True})

@app.route("/api/filtres/<filtre_id>/toggle", methods=["POST"])
def toggle_filtre(filtre_id):
    filtres = charger_filtres()
    for f in filtres:
        if f["id"] == filtre_id:
            f["actif"] = not f.get("actif", True)
    sauvegarder_filtres(filtres)
    return jsonify({"ok": True})

if __name__ == "__main__":
    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
