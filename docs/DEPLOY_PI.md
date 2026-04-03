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

5.  **Voir les logs** :
    ```bash
    journalctl -u scodoc-alert -f
    ```
    > **Note**: Ctrl+C arrête seulement l'affichage des logs, pas le service. Le service continue de tourner en arrière-plan.

## Lancement Automatique (SysVinit)

Pour les systèmes Devuan (par défaut) ou autres utilisant SysVinit au lieu de systemd :

1.  **Créer le script init** :
    Créez le fichier `/etc/init.d/scodoc-alert` :
    ```bash
    sudo nano /etc/init.d/scodoc-alert
    ```
    
    Et collez ce contenu (adaptez les chemins si nécessaire) :
    ```bash
    #!/bin/sh
    ### BEGIN INIT INFO
    # Provides:          scodoc-alert
    # Required-Start:    $remote_fs $syslog $network
    # Required-Stop:     $remote_fs $syslog $network
    # Default-Start:     2 3 4 5
    # Default-Stop:      0 1 6
    # Short-Description: ScodocAlert grade monitor
    # Description:       Monitor Scodoc grades and send Discord notifications
    ### END INIT INFO

    PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
    DAEMON=/usr/bin/python3
    DAEMON_ARGS="/home/pi/ScodocAlert/src/main.py --loop"
    PIDFILE=/var/run/scodoc-alert.pid
    LOGFILE=/var/log/scodoc-alert.log
    WORKDIR=/home/pi/ScodocAlert
    USER=pi

    # Load the VERBOSE setting and other rcS variables
    . /lib/init/vars.sh

    # Define LSB log_* functions
    . /lib/lsb/init-functions

    do_start() {
        log_daemon_msg "Starting ScodocAlert" "scodoc-alert"
        start-stop-daemon --start --quiet --pidfile $PIDFILE \
            --make-pidfile --background --chdir $WORKDIR \
            --chuid $USER --startas /bin/bash -- -c \
            "exec $DAEMON $DAEMON_ARGS >> $LOGFILE 2>&1"
        log_end_msg $?
    }

    do_stop() {
        log_daemon_msg "Stopping ScodocAlert" "scodoc-alert"
        start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 \
            --pidfile $PIDFILE
        log_end_msg $?
        rm -f $PIDFILE
    }

    do_status() {
        if [ -f $PIDFILE ]; then
            PID=$(cat $PIDFILE)
            if ps -p $PID > /dev/null 2>&1; then
                echo "ScodocAlert is running (PID: $PID)"
                return 0
            else
                echo "ScodocAlert is not running (stale PID file)"
                return 1
            fi
        else
            echo "ScodocAlert is not running"
            return 3
        fi
    }

    case "$1" in
        start)
            do_start
            ;;
        stop)
            do_stop
            ;;
        restart)
            do_stop
            sleep 2
            do_start
            ;;
        status)
            do_status
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status}"
            exit 1
            ;;
    esac

    exit 0
    ```

2.  **Rendre le script exécutable** :
    ```bash
    sudo chmod +x /etc/init.d/scodoc-alert
    ```

3.  **Activer le service au démarrage** :
    ```bash
    sudo update-rc.d scodoc-alert defaults
    ```

4.  **Démarrer le service** :
    ```bash
    sudo service scodoc-alert start
    ```

5.  **Vérifier le statut** :
    ```bash
    sudo service scodoc-alert status
    ```

6.  **Voir les logs** :
    ```bash
    tail -f /var/log/scodoc-alert.log
    ```
    > **Note**: Ctrl+C arrête seulement l'affichage des logs, pas le service. Le service continue de tourner en arrière-plan.

**Commandes utiles pour SysVinit** :
- Démarrer : `sudo service scodoc-alert start`
- Arrêter : `sudo service scodoc-alert stop`
- Redémarrer : `sudo service scodoc-alert restart`
- Désactiver au démarrage : `sudo update-rc.d scodoc-alert remove`

## Lancement Automatique (OpenRC)

Pour les systèmes Devuan avec OpenRC ou autres distributions utilisant OpenRC (Alpine, Gentoo, etc.) :

1.  **Créer le script OpenRC** :
    Créez le fichier `/etc/init.d/scodoc-alert` :
    ```bash
    sudo nano /etc/init.d/scodoc-alert
    ```
    
    Et collez ce contenu (adaptez les chemins si nécessaire) :
    ```bash
    #!/sbin/openrc-run
    
    name="ScodocAlert"
    description="Monitor Scodoc grades and send Discord notifications"
    
    command="/usr/bin/python3"
    command_args="/home/pi/ScodocAlert/src/main.py --loop"
    command_background="yes"
    pidfile="/run/${RC_SVCNAME}.pid"
    directory="/home/pi/ScodocAlert"
    command_user="pi:pi"
    
    output_log="/var/log/scodoc-alert.log"
    error_log="/var/log/scodoc-alert.log"
    
    depend() {
        need net
        use logger dns
        after firewall
    }
    
    start_pre() {
        checkpath --file --owner $command_user --mode 0644 \
            "$output_log" "$error_log"
    }
    ```

2.  **Rendre le script exécutable** :
    ```bash
    sudo chmod +x /etc/init.d/scodoc-alert
    ```

3.  **Activer le service au démarrage** :
    ```bash
    sudo rc-update add scodoc-alert default
    ```

4.  **Démarrer le service** :
    ```bash
    sudo rc-service scodoc-alert start
    ```

5.  **Vérifier le statut** :
    ```bash
    sudo rc-service scodoc-alert status
    ```

6.  **Voir les logs** :
    ```bash
    tail -f /var/log/scodoc-alert.log
    ```
    > **Note**: Ctrl+C arrête seulement l'affichage des logs, pas le service. Le service continue de tourner en arrière-plan.

**Commandes utiles pour OpenRC** :
- Démarrer : `sudo rc-service scodoc-alert start`
- Arrêter : `sudo rc-service scodoc-alert stop`
- Redémarrer : `sudo rc-service scodoc-alert restart`
- Vérifier statut : `sudo rc-service scodoc-alert status`
- Désactiver au démarrage : `sudo rc-update del scodoc-alert default`
- Lister les services actifs : `sudo rc-status`
