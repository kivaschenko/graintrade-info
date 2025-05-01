#!/bin/bash

# Update and upgrade system
echo "Updating and upgrading the system..."
sudo apt update -y && sudo apt upgrade -y && sudo apt dist-upgrade -y

# Install essential tools
echo "Installing essential tools..."
sudo apt install -y curl wget gnupg lsb-release ca-certificates ufw fail2ban unzip git

# Set up UFW firewall
echo "Setting up UFW firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Install Docker Compose
echo "Installing Docker Compose..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name)
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Fail2Ban
echo "Installing Fail2Ban..."
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Configure Fail2Ban (basic setup)
echo "Configuring Fail2Ban..."
sudo bash -c 'cat <<EOF > /etc/fail2ban/jail.local
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF'

# Reload Fail2Ban to apply changes
sudo systemctl restart fail2ban

# Install basic monitoring tools (htop, etc.)
echo "Installing basic monitoring tools..."
sudo apt install -y htop iotop iftop

# Clean up
echo "Cleaning up..."
sudo apt autoremove -y && sudo apt clean

# Reboot the server to apply all changes
echo "Rebooting the server..."
sudo reboot
# End of script
# Note: This script is intended for a fresh Ubuntu server setup.
# It is recommended to review and customize the script according to your needs.
# Ensure you have backups and understand the implications of each command before running.