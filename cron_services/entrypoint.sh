#!/bin/bash
# Start cron service
service cron start

# Tail the log file to keep container running and see the output
tail -f /var/log/cron.log