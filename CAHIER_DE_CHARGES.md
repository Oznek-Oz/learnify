# Cahier des charges — Learnify

## 1. Contexte

Learnify est une application d’apprentissage en ligne qui permet à un utilisateur de charger des documents pédagogiques, de générer automatiquement des quiz et des flashcards à partir de ces documents, puis de réviser et d’évaluer ses connaissances. L’application se compose de:
- un backend Django REST Framework avec authentification JWT,
- un frontend React/Vite moderne avec navigation et interface utilisateur responsive.

## 2. Objectifs

- Permettre aux utilisateurs de créer un compte, se connecter et gérer leur profil.
- Autoriser l’upload de fichiers d’apprentissage (PDF / images) et le traitement automatique des contenus.
- Générer des quiz et des flashcards depuis les documents uploadés.
- Proposer une expérience fluide et responsive sur desktop et mobile.
- Offrir des fonctionnalités de reprise de session et de suivi de progression.

## 3. Périmètre fonctionnel

### 3.1 Authentification

- Inscription utilisateur via frontend.
- Connexion utilisateur avec gestion JWT.
- Stockage des tokens `access` et `refresh` dans le navigateur.
- Déconnexion et nettoyage de session.

### 3.2 Profil utilisateur

- Affichage des informations utilisateur (username, email, prénom, nom).
- Mise à jour du profil directement depuis un modal accessible en cliquant sur l’avatar.
- Modification du mot de passe depuis le modal profil.
- Les champs sont pré-remplis avec les valeurs actuelles.

### 3.3 Upload de documents

- Upload de cours au format PDF ou image.
- Chaque cours doit être enregistré côté backend.
- Affichage d’une barre de progression pendant l’upload.
- Possibilité de retélécharger le document uploadé depuis la liste des cours.
- Gestion de l’état de traitement du document : uploadé, traitement en cours, prêt, échec.

### 3.4 Génération de quiz et flashcards

- Génération asymétrique via API backend en tâche de fond.
- Suivi du statut de génération et rafraîchissement périodique si nécessaire.
- Possibilité de télécharger les contenus générés (quiz/flashcards) au format JSON.

### 3.5 Jouer au quiz

- Lecture du quiz dans une interface tutorielle.
- Navigation entre questions.
- Bouton de saut de question pour revenir plus tard.
- Reprise de quiz en cours via stockage local (`localStorage`).
- Résultat final et possibilité de recommencer.
- Limitation du nombre de questions forcée à la saisie.

### 3.6 Révision de flashcards

- Affichage d’un deck de flashcards généré.
- Reprise d’une session de flashcards statuée.
- Interface de navigation et de validation du statut.
- Export des flashcards générées.

### 3.7 Notifications utilisateur

- Retour visuel pour les actions réussies et les erreurs.
- Notification pour upload, inscription, connexion, mise à jour de profil, génération, suppression.

## 4. Exigences techniques

### 4.1 Backend

- Django REST Framework.
- JWT via `rest_framework_simplejwt`.
- Modèle utilisateur personnalisé.
- Endpoints principaux:
  - `POST /api/auth/register/`
  - `POST /api/auth/login/`
  - `POST /api/auth/logout/`
  - `GET/PATCH /api/auth/profile/`
  - `GET /api/courses/`
  - `POST /api/courses/`
  - `DELETE /api/courses/{id}/`
  - `GET /api/quizzes/`, `GET /api/quiz/{id}/`, `PATCH /api/quiz/{id}/`
  - `GET /api/flashcards/`, `GET /api/flashcards/{id}/`, `PATCH /api/flashcards/{id}/`
- Validation des données et gestion des erreurs.
- Mise à jour des statuts `pending`, `in_progress`, `ready`, `failed`.
- Protection `IsAuthenticated` pour les endpoints privés.

### 4.2 Frontend

- React avec Vite.
- React Router pour la navigation.
- TanStack React Query pour le fetch et le cache API.
- Zustand pour le store d’authentification.
- `react-hot-toast` pour les notifications.
- Responsive design pour desktop et mobile.
- Modal de paramètres plutôt qu’une page dédiée.
- Bouton de visibilité de mot de passe dans les formulaires login/register.

### 4.3 UX/Accessibilité

- UI claire et moderne.
- Affichage d’une barre/cercle de progression pour les traitements longs.
- Pré-remplissage des champs de profil.
- Validation inline dans les formulaires.
- Contrôle de la saisie pour éviter les dépassements de limites.
- Navigation simple entre dashboard, cours, quiz et flashcards.

## 5. Sécurité

- Validation stricte des mots de passe côté backend.
- Chiffrement sécurisé des mots de passe via Django.
- contrôle des permissions d’accès aux ressources utilisateur.
- Bon usage des tokens JWT.
- Protection contre l’upload de fichiers non autorisés.

## 6. Déploiement et exploitation

- Backend déployé sur un serveur compatible Django.
- Frontend buildé via Vite.
- Base de données compatible avec Django ORM.
- Configuration des environnements pour API URL, clés et tokens.

## 7. Évolutions possibles

- Export PDF des quiz et flashcards.
- Authentification via OAuth.
- Dashboard d’analyse de progression.
- Recherche full-text dans les contenus uploadés.
- Historique des sessions et statistiques d’apprentissage.
