#!/bin/bash

# Automated Commodity Price Parser Script
# Add to crontab: 0 9,12,15,18 * * 1-5 /path/to/run_commodity_parser.sh

# Set script directory
SCRIPT_DIR="/home/kostiantyn/projects/graintrade-info/parsers"
LOGFILE="$SCRIPT_DIR/commodity_parser.log"

# Change to script directory
cd "$SCRIPT_DIR"

# Log start time
echo "$(date): Starting commodity price parser..." >> "$LOGFILE"

# Activate virtual environment and run script
source venv/bin/activate
python yfinance_draft.py >> "$LOGFILE" 2>&1

# Log completion
if [ $? -eq 0 ]; then
    echo "$(date): Commodity price parser completed successfully" >> "$LOGFILE"
else
    echo "$(date): Commodity price parser failed with exit code $?" >> "$LOGFILE"
fi

# Keep only last 100 lines of log file to prevent it from growing too large
tail -n 100 "$LOGFILE" > "$LOGFILE.tmp" && mv "$LOGFILE.tmp" "$LOGFILE"