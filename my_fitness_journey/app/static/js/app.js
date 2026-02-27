// Backend/app/static/js/app.js

// Au chargement de n'importe quelle page qui inclut ce script
document.addEventListener("DOMContentLoaded", () => {
    updateNavbar();
});

function updateNavbar() {
    const authLinks = document.getElementById("auth-links");
    if (!authLinks) return; 

    const userEmail = localStorage.getItem("user_email");

    if (userEmail) {
        // --- MODE CONNECTÉ ---
        
        // 1. Vérification Admin : On prépare le bouton seulement si c'est le bon email
        let adminBtnHtml = "";
        if (userEmail === "admin@imt.test") {
            adminBtnHtml = `
                <li class="nav-item">
                    <a class="btn btn-danger me-2" href="admin.html">⚙️ Admin</a>
                </li>
            `;
        }

        // 2. On injecte la variable ${adminBtnHtml} au début de la liste
        authLinks.innerHTML = `
            ${adminBtnHtml} 
            <li class="nav-item">
                <a class="btn btn-outline-primary me-2" href="sell.html">
                    + Vendre
                </a>
            </li>
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                    👤 ${userEmail}
                </a>
                <ul class="dropdown-menu dropdown-menu-end">
                    <li><a class="dropdown-item" href="profile.html">Mon Tableau de Bord</a></li>
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item text-danger" href="#" onclick="logout()">Déconnexion</a></li>
                </ul>
            </li>
        `;
    } else {
        // --- MODE VISITEUR (Inchangé) ---
        authLinks.innerHTML = `
            <li class="nav-item">
                <a class="nav-link fw-bold" href="login.html">Se connecter</a>
            </li>
        `;
    }
}

function logout() {
    localStorage.removeItem("user_email");
    window.location.href = "/"; // Retour accueil
}

function formatMoney(cents) {
    if (cents === undefined || cents === null) return "0.00 €";
    return (cents / 100).toFixed(2) + " €";
}