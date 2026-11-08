# Deployment

These instructions describe the tracked pull-based deployment tooling. They do not establish whether a particular server has completed setup. Commands below change the deployment or server configuration; adapt them to your instance.

## Deployment

The server pulls; nothing pushes to it. A systemd timer runs `deploy/deploy.sh` every minute. When the `production` branch on GitHub points at a new commit, the script checks it out, reinstalls dependencies if `pyproject.toml` or `uv.lock` changed, restarts `czdemos.service` and waits up to 90 s for `/settings` to answer. If it does not, the script goes back to the previous commit and skips the bad one until the next push. It refuses to deploy over files edited by hand on the server. `.env`, `data/` and other untracked files are left alone, including the server's instance config (`INSTANCE_CONFIG_PATH`, usually `data/instances/<server>.toml`), which is copied there by hand. Without a valid one the app does not start, so the health check fails and the deploy rolls back.

Deploy from any machine with push access:

```bash
git push origin main:production                         # what is on main
git push origin <sha>:production                        # an older commit, keeping production behind main
git push --force-with-lease origin <sha>:production     # roll back
```

Watch it on the server with `journalctl -u avatar-deploy -f`.

One-time setup on the server, in the checkout the app runs from (`/home/papacek/rag-avatar` on czdemos-avatar):

```bash
git remote set-url origin https://github.com/ampapacek/CZD-avatar.git
git pull                                # brings in deploy/
cp deploy/deploy.env.example deploy/deploy.env   # optional: only for settings that differ
sudo deploy/install.sh                  # units + sudoers rule for this checkout and your user
sudo -n systemctl restart czdemos.service   # must work without a password prompt
```

`deploy/install.sh` writes `avatar-deploy.service`, `avatar-deploy.timer` and `/etc/sudoers.d/avatar-deploy` with the checkout's path and the user who ran `sudo`, then enables the timer. `deploy/install.sh --dry-run` prints them without installing anything.

Per-server settings go in `deploy/deploy.env` (untracked; see `deploy/deploy.env.example`): the branch to follow, the app's systemd service, the health-check URL and the path to `uv`. The service loads that file; `deploy.sh` finds its checkout from its own location. Re-run `sudo deploy/install.sh` after changing `SERVICE` or moving the checkout.
