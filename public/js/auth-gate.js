// Filtre simple par mot de passe pour les pages admin / dashboard.
// Voir l'avertissement dans config.js : ce n'est pas une vraie sécurité.
//
// Affiche un formulaire intégré à la page plutôt qu'un prompt() natif :
// ce dernier est bloqué (ou renvoie null silencieusement) dans pas mal
// d'environnements embarqués (webview d'IDE, navigateurs kiosque sur
// tablette, etc.), ce qui figeait toute la page sans erreur visible.
function requireAdminPassword() {
  return new Promise((resolve) => {
    if (sessionStorage.getItem("acvv_admin_ok") === "1") {
      resolve();
      return;
    }

    const overlay = document.createElement("div");
    overlay.style.cssText =
      "position:fixed;inset:0;background:rgba(5,8,20,0.95);" +
      "display:flex;align-items:center;justify-content:center;z-index:1000;" +
      "font-family:'DM Sans',sans-serif;";
    overlay.innerHTML = `
      <div style="background:#111827;border:2px solid #2d3447;border-radius:16px;padding:2rem;max-width:320px;width:90%;text-align:center">
        <div style="font-size:1.1rem;margin-bottom:1rem;color:#fff">🔒 Accès administrateur</div>
        <input type="password" id="acvv-admin-pwd" placeholder="Mot de passe" autocomplete="off"
          style="width:100%;box-sizing:border-box;background:#1e2433;border:2px solid #2d3447;border-radius:8px;color:#fff;font-size:1rem;padding:0.6rem;text-align:center;margin-bottom:0.6rem">
        <div id="acvv-admin-err" style="color:#cf2027;font-size:0.78rem;min-height:1.1rem;margin-bottom:0.6rem"></div>
        <button id="acvv-admin-submit" style="width:100%;background:#0047b8;color:#fff;border:none;border-radius:8px;padding:0.65rem;font-weight:700;font-family:'DM Sans',sans-serif;cursor:pointer">Valider</button>
      </div>
    `;
    document.body.appendChild(overlay);

    const input = overlay.querySelector("#acvv-admin-pwd");
    const err = overlay.querySelector("#acvv-admin-err");

    function submit() {
      if (input.value === ADMIN_PASSWORD) {
        sessionStorage.setItem("acvv_admin_ok", "1");
        overlay.remove();
        resolve();
      } else {
        err.textContent = "Mot de passe incorrect";
        input.value = "";
        input.focus();
      }
    }

    overlay.querySelector("#acvv-admin-submit").addEventListener("click", submit);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") submit();
    });
    setTimeout(() => input.focus(), 50);
  });
}
