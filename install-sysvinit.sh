#!/bin/bash
set -e

echo "========================================="
echo "ScodocAlert SysVinit Installer"
echo "========================================="
echo ""

CURRENT_DIR=$(pwd)
SCRIPT_DIR="$CURRENT_DIR"

echo "Project directory: $SCRIPT_DIR"
read -p "Is this correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter full project path: " SCRIPT_DIR
fi

if [ ! -f "$SCRIPT_DIR/src/main.py" ]; then
    echo "Error: main.py not found in $SCRIPT_DIR/src/"
    exit 1
fi

read -p "Service user (default: pi): " SERVICE_USER
SERVICE_USER=${SERVICE_USER:-pi}

echo ""
echo "Configuration:"
echo "  - Directory: $SCRIPT_DIR"
echo "  - User: $SERVICE_USER"
echo "  - Logs: /var/log/scodoc-alert.log"
echo ""
read -p "Continue installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

echo "Creating init.d script..."
sudo tee /etc/init.d/scodoc-alert > /dev/null <<EOF
#!/bin/sh
### BEGIN INIT INFO
# Provides:          scodoc-alert
# Required-Start:    \$remote_fs \$syslog \$network
# Required-Stop:     \$remote_fs \$syslog \$network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: ScodocAlert grade monitor
# Description:       Monitor Scodoc grades and send Discord notifications
### END INIT INFO

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
DAEMON=/usr/bin/python3
DAEMON_ARGS="$SCRIPT_DIR/src/main.py --loop"
PIDFILE=/var/run/scodoc-alert.pid
LOGFILE=/var/log/scodoc-alert.log
WORKDIR=$SCRIPT_DIR
USER=$SERVICE_USER

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions
. /lib/lsb/init-functions

do_start() {
    log_daemon_msg "Starting ScodocAlert" "scodoc-alert"
    start-stop-daemon --start --quiet --pidfile \$PIDFILE \\
        --make-pidfile --background --chdir \$WORKDIR \\
        --chuid \$USER --startas /bin/bash -- -c \\
        "exec \$DAEMON \$DAEMON_ARGS >> \$LOGFILE 2>&1"
    log_end_msg \$?
}

do_stop() {
    log_daemon_msg "Stopping ScodocAlert" "scodoc-alert"
    start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 \\
        --pidfile \$PIDFILE
    log_end_msg \$?
    rm -f \$PIDFILE
}

do_status() {
    if [ -f \$PIDFILE ]; then
        PID=\$(cat \$PIDFILE)
        if ps -p \$PID > /dev/null 2>&1; then
            echo "ScodocAlert is running (PID: \$PID)"
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

case "\$1" in
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
        echo "Usage: \$0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
EOF

echo "Setting permissions..."
sudo chmod +x /etc/init.d/scodoc-alert

sudo touch /var/log/scodoc-alert.log
sudo chown $SERVICE_USER:$SERVICE_USER /var/log/scodoc-alert.log

echo "Enabling service at boot..."
sudo update-rc.d scodoc-alert defaults

echo ""
echo "========================================="
echo "Installation complete!"
echo "========================================="
echo ""
echo "Available commands:"
echo "  - Start   : sudo service scodoc-alert start"
echo "  - Stop    : sudo service scodoc-alert stop"
echo "  - Restart : sudo service scodoc-alert restart"
echo "  - Status  : sudo service scodoc-alert status"
echo "  - Logs    : tail -f /var/log/scodoc-alert.log"
echo ""
read -p "Start service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo service scodoc-alert start
    sleep 2
    sudo service scodoc-alert status
    echo ""
    echo "Live logs (Ctrl+C to quit):"
    tail -f /var/log/scodoc-alert.log
fi
