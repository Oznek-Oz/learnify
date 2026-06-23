# Diagrammes UML de l'Application Learnify

Ce document contient les descriptions détaillées de tous les diagrammes UML créés pour l'application Learnify.

## 1. class_diagram.mmd - Diagramme de classes UML

Ce diagramme représente la structure des données de l'application Learnify. Il montre :
- **CustomUser** : Modèle utilisateur étendu avec authentification par email
- **Course** : Cours uploadés par les utilisateurs (PDF/images) avec statut de traitement
- **CourseChunk** : Morceaux de texte extraits des cours avec leurs embeddings
- **Quiz** : Quiz générés avec difficulté et statut de génération
- **Question** : Questions à choix multiples avec explications
- **FlashcardDeck** : Collections de flashcards organisées par sujet
- **Flashcard** : Cartes de révision avec système de répétition espacée

Les relations montrent la hiérarchie : User → Courses → Chunks/Quizzes/Decks → Questions/Flashcards.

## 2. use_case_diagram.mmd - Diagramme de cas d'usage

Ce diagramme illustre les interactions principales entre l'étudiant et le système :
- **Fonctionnalités utilisateur** : Upload de cours, génération de quiz/flashcards, étude, passage de quiz
- **Processus système** : Traitement automatique (OCR, embeddings, stockage vectoriel), génération IA
- **Flux de données** : De l'upload à la génération en passant par le traitement automatique

## 3. course_processing_activity.mmd - Diagramme d'activité du traitement de cours

Ce diagramme montre le pipeline RAG (Retrieval-Augmented Generation) pour traiter les cours :
- **États** : Uploadé → En traitement → OCR → Chunking → Embeddings → Stockage → Prêt
- **Gestion d'erreurs** : Chaque étape peut échouer et passer à l'état "Failed"
- **Technologies** : Tâches Celery asynchrones, SentenceTransformers pour les embeddings, ChromaDB pour le stockage vectoriel

## 4. quiz_generation_sequence.mmd - Diagramme de séquence de génération de quiz

Ce diagramme détaille le processus complet de génération d'un quiz :
- **Acteurs** : Utilisateur, API Django, PostgreSQL, Redis Queue, Worker Celery, Gemini API, ChromaDB
- **Flux** : Création du quiz → Mise en file → Traitement asynchrone → Recherche sémantique → Génération IA → Sauvegarde
- **Communication** : HTTP pour l'API, files de messages pour les tâches asynchrones

## 5. component_diagram.mmd - Diagramme de composants système

Ce diagramme montre l'architecture technique détaillée :
- **Frontend** : React/Vite SPA avec Axios, Zustand, React Router
- **Backend** : Django REST Framework avec authentification JWT, vues API, sérialiseurs
- **Services asynchrones** : Workers Celery avec files dédiées (courses et génération)
- **Stockage** : PostgreSQL, ChromaDB, Redis, fichiers médias
- **Services externes** : Gemini API, Tesseract OCR, SentenceTransformers

## 6. deployment_diagram.mmd - Diagramme de déploiement

Ce diagramme représente l'infrastructure de déploiement :
- **Client** : Navigateur web avec application React
- **Serveur web** : Nginx (reverse proxy) → Gunicorn → Django
- **Bases de données** : PostgreSQL (métier), Redis (cache/broker), ChromaDB (vecteurs)
- **Workers** : Nœuds Celery pour les tâches asynchrones
- **Stockage** : Fichiers médias locaux/NFS
- **APIs externes** : Gemini API pour la génération IA

## 7. generation_state.mmd - Diagramme d'états de génération

Ce diagramme montre les états possibles des processus de génération (quiz/flashcards) :
- **États** : Pending (en attente) → Generating (en cours) → Ready (terminé) ou Failed (échoué)
- **Transitions** : Démarrage par worker Celery, recherche sémantique dans ChromaDB
- **Gestion** : Sauvegarde en base ou logging d'erreurs

## 8. architecture.mmd - Diagramme d'architecture globale

Ce diagramme montre l'architecture générale de l'application Learnify :
- **Client** : Interface React/Vite
- **API** : Backend Django REST avec authentification JWT
- **Storage** : PostgreSQL, ChromaDB, Redis, fichiers médias
- **AI** : Intégration avec Gemini API
- **Celery** : Traitement asynchrone avec files dédiées

## 9. generation_flow.mmd - Diagramme de flux de génération

Ce diagramme illustre le processus de génération de contenu IA :
- **Acteurs** : Utilisateur, Frontend React, API Django, Celery, PostgreSQL, ChromaDB, Gemini API
- **Flux** : Demande utilisateur → API → File d'attente → Worker → Recherche sémantique → Génération IA → Sauvegarde
- **Polling** : Vérification périodique du statut par le frontend

---

Ces diagrammes couvrent tous les aspects importants de l'application Learnify :
- Structure des données et modèles
- Interactions utilisateur et cas d'usage
- Processus métier et workflows
- Architecture technique et composants
- Infrastructure de déploiement
- États et transitions système

Ils sont particulièrement utiles pour :
- La documentation technique
- La compréhension du système par de nouveaux développeurs
- La maintenance et l'évolution de l'application
- Les présentations et revues d'architecture