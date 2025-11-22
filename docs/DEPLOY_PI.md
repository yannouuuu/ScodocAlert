# Déploiement sur Raspberry Pi

Ce guide explique comment installer et lancer ScodocAlert sur un Raspberry Pi pour qu'il tourne en continu.

## Prérequis

*   Un Raspberry Pi avec Debian (ou autre Linux) installé.
*   Accès internet sur le Pi.
*   Python 3 installé.

## Installation

1.  **Copier les fichiers** : Transférez tout le dossier `ScodocAlert` sur votre Raspberry Pi (par exemple dans `/home/pi/ScodocAlert`).

2.  **Installer les dépendances** :
    ```bash
    cd /home/pi/ScodocAlert
    pip3 install -r requirements.txt
    ```
    *(Si vous utilisez un environnement virtuel, activez-le avant ou installez les paquets globalement avec `--break-system-packages` si nécessaire sur les OS récents).*

3.  **Configurer l'environnement** :
    *   Renommez `.env.example` en `.env` :
        ```bash
        mv .env.example .env
        ```
    *   Éditez le fichier `.env` avec vos identifiants et l'URL du Webhook Discord :
        ```bash
        vim .env
        ```

4.  **Tester le script** :
    Lancez le script une fois pour vérifier que tout fonctionne :
    ```bash
    python3 src/main.py
    ```

## Lancement Automatique (Systemd)

Pour que le script se lance au démarrage et redémarre en cas de crash :

1.  **Éditer le fichier service** :
    Ouvrez `scodoc-alert.service` et vérifiez les chemins (`WorkingDirectory` et `ExecStart`) et l'utilisateur (`User`). Si vous avez installé le projet ailleurs que dans `/home/pi/ScodocAlert`, modifiez ces lignes.

2.  **Installer le service** :
    ```bash
    sudo cp scodoc-alert.service /etc/systemd/system/
    sudo systemctl daemon-reload
    ```

3.  **Activer et démarrer** :
    ```bash
    sudo systemctl enable scodoc-alert
    sudo systemctl start scodoc-alert
    ```

4.  **Vérifier le statut** :
    ```bash
    sudo systemctl status scodoc-alert
    ```

## Logs

Pour voir les logs du script (et vérifier qu'il tourne bien) :
```bash
journalctl -u scodoc-alert -f
```
