**Outlining user setup steps**

I need to provide general steps for setting up SSH access on Fedora for a new user using `authorized_keys`. I'll consider commands like `install -d -m 700` to create directories securely, along with `chown` to adjust ownership. It’s important to mention how to append the public keys into the `authorized_keys` file, and I should also include how to use `sudo -u` to switch user contexts when necessary. These steps should ensure a proper setup for SSH access.To add an SSH public key for a new user on Fedora (so it goes into `authorized_keys`), do this:

1) Create the user (if you haven’t already)
```bash
sudo useradd -m -G wheel <username>
sudo passwd <username>
```

2) Make sure the `.ssh` directory exists with correct permissions
```bash
sudo -u <username> mkdir -p /home/<username>/.ssh
sudo chmod 700 /home/<username>/.ssh
```

3) Add the public key into `authorized_keys`
- Option A (recommended): append the key from a file:
```bash
sudo tee -a /home/<username>/.ssh/authorized_keys < /path/to/id_ed25519.pub > /dev/null
```

- Option B: add the key directly (paste the full `ssh-ed25519 AAAA...` line):
```bash
sudo tee -a /home/<username>/.ssh/authorized_keys > /dev/null <<'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... your_comment
EOF
```

4) Fix ownership and permissions (important)
```bash
sudo chown -R <username>:<username> /home/<username>/.ssh
sudo chmod 600 /home/<username>/.ssh/authorized_keys
```

5) (Optional) Verify
```bash
sudo -u <username> cat /home/<username>/.ssh/authorized_keys
```

If you tell me where your new user’s key is coming from (e.g., `~/.ssh/id_ed25519.pub` on your current machine, or a key in a file on the server), I can tailor the exact command.