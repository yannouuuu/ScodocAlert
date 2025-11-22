# ScodocAlert

ScodocAlert est un script Python qui surveille les notes d'un étudiant (pour l'instant uniquement avec le CAS de l'Université de Lille) et envoie des alertes Discord lorsqu'une note est modifiée.

## Fonctionnalités

- Authentification via CAS
- Surveillance des notes
- Envoi d'alertes Discord
- Sauvegarde des états

## Prérequis

- Python 3.7+
- Un compte Discord avec un webhook
- Un compte étudiant sur l'Université de Lille

## Installation

1.  Cloner le dépôt.
2.  Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
3.  Configurer les variables d'environnement :
    *   Copier `.env.example` vers `.env`.
    *   Remplir `.env` avec vos identifiants et l'URL du Webhook Discord.

## Utilisation

Lancer le script depuis la racine du projet :

```bash
python3 src/main.py
```

Pour lancer en boucle (toutes les 10 minutes) :

```bash
python3 src/main.py --loop
```

## Structure du projet

*   `src/` : Code source de l'application.
*   `docs/` : Documentation (guide de déploiement Raspberry Pi).
*   `deploy/` : Fichiers de déploiement (service systemd).
*   `scodoc_state.json` : Fichier stockant l'état des notes (créé automatiquement).

## Déploiement sur Raspberry Pi

Voir le fichier `DEPLOY_PI.md` pour les instructions de déploiement.