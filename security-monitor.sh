#!/bin/bash

# Security Monitoring Script for Graintrade API
# This script helps monitor blocked requests and security events

echo "🔍 Security Monitoring Dashboard for Graintrade API"
echo "=================================================="

# Function to display recent blocked requests
show_blocked_requests() {
    echo ""
    echo "🚫 Recent Blocked Requests (Last 100 lines):"
    echo "--------------------------------------------"
    
    if [ -f /var/log/apache2/error.log ]; then
        tail -100 /var/log/apache2/error.log | grep -E "(403|Forbidden|blocked|denied)" | tail -20
    else
        echo "❌ Apache error log not found"
    fi
}

# Function to show top attacking IPs
show_top_attackers() {
    echo ""
    echo "🎯 Top Attacking IPs (Last 1000 requests):"
    echo "-------------------------------------------"
    
    if [ -f /var/log/apache2/access.log ]; then
        tail -1000 /var/log/apache2/access.log | \
        awk '{print $1}' | \
        sort | uniq -c | sort -nr | head -10 | \
        awk '{printf "%-15s %s requests\n", $2, $1}'
    else
        echo "❌ Apache access log not found"
    fi
}

# Function to show common attack patterns
show_attack_patterns() {
    echo ""
    echo "🔍 Common Attack Patterns (Last 1000 requests):"
    echo "-----------------------------------------------"
    
    if [ -f /var/log/apache2/access.log ]; then
        tail -1000 /var/log/apache2/access.log | \
        grep -E "(\.env|wp-|\.git|cgi-bin|xmlrpc|owa)" | \
        awk '{print $7}' | sort | uniq -c | sort -nr | head -10
    else
        echo "❌ Apache access log not found"
    fi
}

# Function to show mod_evasive blocks
show_evasive_blocks() {
    echo ""
    echo "⚡ mod_evasive Blocks:"
    echo "--------------------"
    
    if [ -d /var/log/apache2/evasive ]; then
        if [ "$(ls -A /var/log/apache2/evasive)" ]; then
            ls -la /var/log/apache2/evasive/
        else
            echo "✅ No mod_evasive blocks found"
        fi
    else
        echo "❌ mod_evasive log directory not found"
    fi
}

# Function to show real-time monitoring
monitor_realtime() {
    echo ""
    echo "📡 Real-time Monitoring (Press Ctrl+C to stop):"
    echo "----------------------------------------------"
    
    if [ -f /var/log/apache2/access.log ]; then
        tail -f /var/log/apache2/access.log | grep --line-buffered -E "(403|404|\.env|wp-|\.git|cgi-bin)"
    else
        echo "❌ Apache access log not found"
    fi
}

# Parse command line arguments
case "${1:-summary}" in
    "blocked")
        show_blocked_requests
        ;;
    "attackers")
        show_top_attackers
        ;;
    "patterns")
        show_attack_patterns
        ;;
    "evasive")
        show_evasive_blocks
        ;;
    "realtime")
        monitor_realtime
        ;;
    "summary"|*)
        show_blocked_requests
        show_top_attackers
        show_attack_patterns
        show_evasive_blocks
        echo ""
        echo "💡 Usage:"
        echo "  $0 [summary|blocked|attackers|patterns|evasive|realtime]"
        ;;
esac