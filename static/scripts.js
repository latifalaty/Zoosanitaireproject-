// scripts.js
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('addUserForm').addEventListener('submit', function(event) {
        event.preventDefault(); // Empêche le formulaire de se soumettre normalement
        
        // Récupère le message d'alerte à partir de la réponse JSON
        fetch('/add_user', {
            method: 'POST',
            body: new FormData(this)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Efface les champs du formulaire
                document.getElementById('addUserForm').reset();
                // Affiche l'alerte
                window.alert('Utilisateur ajouté avec succès!');
            }
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des données:', error);
        });
    });
});
