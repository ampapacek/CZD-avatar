# Deployment

These instructions describe the tracked pull-based deployment tooling. They do not establish whether a particular server has completed setup. Commands below change the deployment or server configuration; adapt them to your instance.

## Deployment

The server pulls; nothing pushes to it. A systemd timer runs `deploy/deploy.sh` every minute. When the `production` branch on GitHub points at a new commit, the script checks it out, reinstalls dependencies if `pyproject.toml` or `uv.lock` changed, restarts `czdemos.service` and waits up to 90 s for `/settings` to answer. If it does not, the script goes back to the previous commit and skips the bad one until the next push. It refuses to deploy over files edited by hand on the server. `.env`, `data/` and other untracked files are left alone.

Deploy from any machine with push access:

```bash
git push origin main:production                         # what is on main
git push origin <sha>:production                        # an older commit, keeping production behind main
git push --force-with-lease origin <sha>:production     # roll back
```

Watch it on the server with `journalctl -u avatar-deploy -f`.

One-time setup on the server, in `/home/papacek/rag-avatar`:

```bash
git remote set-url origin https://github.com/ampapacek/CZD-avatar.git
git pull                                # brings in deploy/
echo 'papacek ALL=(root) NOPASSWD: /usr/bin/systemctl restart czdemos.service' | sudo tee /etc/sudoers.d/avatar-deploy
sudo chmod 440 /etc/sudoers.d/avatar-deploy && sudo visudo -cf /etc/sudoers.d/avatar-deploy
sudo -n systemctl restart czdemos.service   # must work without a password prompt
sudo cp deploy/avatar-deploy.service deploy/avatar-deploy.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now avatar-deploy.timer
```

Paths, user and service name are defaults at the top of `deploy/deploy.sh` and in the two unit files; change them there for another server.
