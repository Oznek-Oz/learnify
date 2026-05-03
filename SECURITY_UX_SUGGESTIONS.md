# Suggestions de sécurité et d'expérience utilisateur

## Sécurité

- Restreindre l'accès aux ressources uploadées aux utilisateurs autorisés et protéger les URL de téléchargement.
- Mettre en place des en-têtes de sécurité HTTP (CSP, HSTS, X-Frame-Options, X-Content-Type-Options).
- Ajouter une journalisation des actions sensibles (connexion, modification de mot de passe, suppression). 
- Limiter le taux de requêtes pour les endpoints d'authentification et de génération de contenu.
- Vérifier les permissions sur les objets `Quiz` / `FlashcardDeck` pour éviter l'accès à des ressources appartenant à d'autres utilisateurs.

## Expérience utilisateur

- Afficher des notifications claires pour chaque action (upload, génération, sauvegarde, erreurs).
- Ajouter des états de chargement et des retours visuels pour les tâches longues (barres de progression globales, spinners). 
- Permettre la reprise automatique de quiz/flashcards depuis la dernière session sauvegardée.
- Rendre l'interface responsive avec un menu mobile, des cartes adaptatives et des boutons larges sur mobile.
- Proposer un aperçu des documents uploadés et un bouton de téléchargement direct.
- Offrir un historique ou un statut détaillé des générations de quiz/flashcards (en cours, prêt, échec).
- Préserver les réponses de quiz non terminés même après rechargement ou navigation.
- Améliorer l'accessibilité : labels explicites, focus visibles, contrastes conformes, navigation clavier.
