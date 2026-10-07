#!/usr/bin/env bash
# Pull-based deploy, run every minute by avatar-deploy.timer.
#
# If the `production` branch on GitHub points at a commit other than the one
# checked out, check that commit out, reinstall dependencies when pyproject.toml
# or uv.lock changed, restart the app and wait for /settings to answer. When the
# new commit does not come up healthy, go back to the previous one and remember
# the bad commit so it is not retried every minute; a new push clears that.
#
# Every setting can be overridden from the environment (the tests do this).

set -uo pipefail

REPO_DIR=${REPO_DIR:-/home/papacek/rag-avatar}
DEPLOY_BRANCH=${DEPLOY_BRANCH:-production}
SERVICE=${SERVICE:-czdemos.service}
UV=${UV:-/home/papacek/.local/bin/uv}
RESTART_CMD=${RESTART_CMD:-sudo -n systemctl restart $SERVICE}
INSTALL_CMD=${INSTALL_CMD:-$UV pip install --quiet --python .venv/bin/python -e .}
HEALTH_URL=${HEALTH_URL:-http://127.0.0.1/settings}
HEALTH_CMD=${HEALTH_CMD:-curl -fsS -o /dev/null --max-time 5 $HEALTH_URL}
HEALTH_TIMEOUT=${HEALTH_TIMEOUT:-90}
HEALTH_INTERVAL=${HEALTH_INTERVAL:-3}
# Inside .git: never tracked, untouched by checkouts.
STATE_DIR=${STATE_DIR:-$REPO_DIR/.git/avatar-deploy}

log() { echo "$*"; }
short() { git rev-parse --short "$1"; }

deps_changed() {
    ! git diff --quiet "$1" "$2" -- pyproject.toml uv.lock
}

wait_healthy() {
    local deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
    while true; do
        if bash -c "$HEALTH_CMD" >/dev/null 2>&1; then
            return 0
        fi
        if [ "$(date +%s)" -ge "$deadline" ]; then
            return 1
        fi
        sleep "$HEALTH_INTERVAL"
    done
}

# Move the checkout from $2 to $1 and bring the app up on it. Every step is
# checked by hand: `set -e` is ignored inside a function called from `if`.
switch_to() {
    local to=$1 from=$2
    git checkout --quiet -B "$DEPLOY_BRANCH" "$to" || return 1
    if deps_changed "$from" "$to"; then
        log "dependencies changed, reinstalling"
        bash -c "$INSTALL_CMD" || return 1
    fi
    bash -c "$RESTART_CMD" || return 1
    wait_healthy
}

main() {
    cd "$REPO_DIR" || exit 1
    mkdir -p "$STATE_DIR"

    local remote target current
    remote=$(git ls-remote --exit-code origin "refs/heads/$DEPLOY_BRANCH") || {
        # Exit code 2 means the branch does not exist; anything else is a
        # network or git error worth a failed run.
        [ $? -eq 2 ] && exit 0
        log "cannot reach origin"
        exit 1
    }
    target=${remote%%[[:space:]]*}
    current=$(git rev-parse HEAD)

    [ "$target" = "$current" ] && exit 0
    [ "$(cat "$STATE_DIR/bad" 2>/dev/null)" = "$target" ] && exit 0

    # Never overwrite edits made by hand on the server. Say so once per target.
    if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
        if [ "$(cat "$STATE_DIR/blocked" 2>/dev/null)" != "$target" ]; then
            echo "$target" > "$STATE_DIR/blocked"
            log "not deploying: tracked files were changed on the server:"
            git status --short --untracked-files=no
            exit 1
        fi
        exit 0
    fi

    git fetch --quiet origin "+refs/heads/$DEPLOY_BRANCH:refs/remotes/origin/$DEPLOY_BRANCH" || {
        log "fetch failed"
        exit 1
    }
    # The branch may have moved again since ls-remote.
    target=$(git rev-parse "refs/remotes/origin/$DEPLOY_BRANCH")
    [ "$target" = "$current" ] && exit 0

    log "deploying $(short "$target") (was $(short "$current"))"
    if switch_to "$target" "$current"; then
        rm -f "$STATE_DIR/bad" "$STATE_DIR/blocked"
        log "deployed $(short "$target")"
        exit 0
    fi

    echo "$target" > "$STATE_DIR/bad"
    log "$(short "$target") did not come up healthy, rolling back to $(short "$current")"
    if switch_to "$current" "$target"; then
        log "rolled back to $(short "$current")"
    else
        log "ERROR: rollback to $(short "$current") is not healthy either"
    fi
    exit 1
}

# Kept on one line with the call: a deploy may rewrite this file while it runs,
# and bash has already read the whole of main() before executing it.
main "$@"; exit $?
