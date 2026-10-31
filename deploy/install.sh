#!/usr/bin/env bash
# Install the auto-deploy timer for the checkout this script lives in.
#
#   sudo deploy/install.sh            install the units and the sudoers rule
#   deploy/install.sh --dry-run       print what would be installed
#
# The deploy runs as the user who called sudo, from this checkout. SERVICE is
# read from deploy/deploy.env when it is set there.

set -euo pipefail

REPO_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEPLOY_USER=${SUDO_USER:-$(id -un)}
DEPLOY_GROUP=$(id -gn "$DEPLOY_USER")
SERVICE=czdemos.service
if [ -f "$REPO_DIR/deploy/deploy.env" ]; then
    SERVICE=$(set +u; . "$REPO_DIR/deploy/deploy.env"; echo "${SERVICE:-czdemos.service}")
fi
UNIT_DIR=/etc/systemd/system
SUDOERS_FILE=/etc/sudoers.d/avatar-deploy

render() {
    sed -e "s|@USER@|$DEPLOY_USER|g" -e "s|@GROUP@|$DEPLOY_GROUP|g" -e "s|@REPO_DIR@|$REPO_DIR|g" "$1"
}

sudoers_rule="$DEPLOY_USER ALL=(root) NOPASSWD: /usr/bin/systemctl restart $SERVICE"

if [ "${1:-}" = "--dry-run" ]; then
    for unit in avatar-deploy.service avatar-deploy.timer; do
        echo "# $UNIT_DIR/$unit"
        render "$REPO_DIR/deploy/$unit"
        echo
    done
    echo "# $SUDOERS_FILE"
    echo "$sudoers_rule"
    exit 0
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "run with sudo, or pass --dry-run" >&2
    exit 1
fi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
echo "$sudoers_rule" > "$tmp"
visudo -cf "$tmp" >/dev/null
install -m 440 "$tmp" "$SUDOERS_FILE"

for unit in avatar-deploy.service avatar-deploy.timer; do
    render "$REPO_DIR/deploy/$unit" > "$UNIT_DIR/$unit"
done
systemctl daemon-reload
systemctl enable --now avatar-deploy.timer
echo "installed for $DEPLOY_USER in $REPO_DIR, restarting $SERVICE"
