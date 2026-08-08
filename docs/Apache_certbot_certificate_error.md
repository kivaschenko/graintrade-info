Updated todo list

I can see what is happening: there is likely a stale manually started Apache process plus a failing restart path, so I’ll give you a clean recovery sequence that forces one owner (systemd) and bypasses the broken SSL vhost first.

You are very close. The behavior now is consistent with this sequence:

1. Apache was already running outside proper systemd tracking.
2. start says “already running” and exits success, so systemd shows inactive/dead.
3. restart actually stops it, then fresh start fails because one HTTPS vhost is still broken (most likely API SSL cert path/content).

The earlier SSL error for API is still the key blocker.

Use this exact recovery flow on server:

1. Stop all Apache processes and clear stale pid
    sudo apachectl -k stop || true
    sudo pkill -9 apache2 || true
    sudo rm -f /var/run/apache2/apache2.pid

2. Temporarily disable the known bad API vhost
    sudo a2dissite api.graintrade.info.conf

3. Validate and start cleanly through systemd
    sudo apache2ctl -t
    sudo systemctl start apache2
    sudo systemctl status apache2 --no-pager -l

4. If Apache is up, issue cert only for existing DNS name
    sudo certbot --apache -d home.graintrade.info

5. Verify site
    curl -I https://home.graintrade.info

6. Diagnose API cert before re-enabling API vhost
    sudo certbot certificates
    sudo ls -la /etc/letsencrypt/live/
    sudo openssl x509 -in /etc/letsencrypt/live/api.graintrade.info/fullchain.pem -noout -subject -issuer -dates
    sudo openssl pkey -in /etc/letsencrypt/live/api.graintrade.info/privkey.pem -noout -text >/dev/null

7. Re-enable API site only after cert files are valid
    sudo a2ensite api.graintrade.info.conf
    sudo apache2ctl -t
    sudo systemctl restart apache2

Why this works:
- It removes process-state confusion.
- It isolates the bad SSL vhost so Home certificate issuance can proceed.
- It then fixes API independently.

Related config locations in your repo:
- api.graintrade.info.conf
- api.graintrade.info.conf
- home.graintrade.info.conf

If restart still fails after step 3, send these two outputs and I will pinpoint the exact next command:
1. sudo journalctl -u apache2 -n 80 --no-pager
2. sudo tail -n 80 /var/log/apache2/error.log