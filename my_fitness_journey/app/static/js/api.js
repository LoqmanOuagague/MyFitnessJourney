// Backend/app/static/js/api.js

// ⚠️ IMPORTANT : On laisse vide car le site et l'API sont sur le même port (5000)
// Le navigateur utilisera automatiquement l'hôte actuel.
const API_BASE_URL = "";

/**
 * Fonction universelle pour parler au Backend.
 * Gère l'URL, les Headers (Auth) et les Erreurs.
 * * @param {string} endpoint - Ex: "/api/listings"
 * @param {string} method - "GET", "POST", "PUT", "DELETE"
 * @param {object} data - Les données à envoyer (sera converti en JSON)
 */
async function callApi(endpoint, method = "GET", data = null) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Récupération du token (email) stocké dans le navigateur
    const userEmail = localStorage.getItem("user_email");

    // Headers de base
    const headers = {
        "Content-Type": "application/json"
    };

    // Si l'utilisateur est connecté, on ajoute son badge d'identité
    if (userEmail) {
        headers["X-User-Email"] = userEmail;
    }

    const options = {
        method,
        headers,
    };

    // Si on envoie des données (POST/PUT), on les transforme en texte JSON
    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);

        // Si le serveur répond une erreur (400, 401, 403, 500...)
        if (!response.ok) {
            // On essaie de lire le message d'erreur envoyé par Flask
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.error || `Erreur ${response.status}: ${response.statusText}`;
            throw new Error(errorMessage);
        }

        // Cas spécial : Si la réponse est vide (ex: DELETE réussi qui renvoie 204)
        if (response.status === 204) return null;

        // Sinon, on renvoie le résultat JSON
        return await response.json();

    } catch (error) {
        console.error("Erreur API:", error);
        // On relance l'erreur pour que le fichier qui a appelé callApi puisse l'afficher (alert, div rouge...)
        throw error; 
    }
}

/**
 * Spécial pour l'Upload de Photos (Multipart/Form-Data)
 * On ne peut pas utiliser callApi car il ne faut pas mettre 'Content-Type: application/json'
 */
async function uploadPhoto(fileInput) {
    const url = `${API_BASE_URL}/api/photos`;
    const userEmail = localStorage.getItem("user_email");
    
    if (!userEmail) throw new Error("Connexion requise pour uploader.");

    const formData = new FormData();
    formData.append("file", fileInput);

    const response = await fetch(url, {
        method: "POST",
        headers: { 
            "X-User-Email": userEmail 
            // Note: Pas de Content-Type ici, le navigateur le mettra automatiquement avec le "boundary" correct
        },
        body: formData
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Erreur upload");
    }
    
    return await response.json(); // Retourne { url: "..." }
}
