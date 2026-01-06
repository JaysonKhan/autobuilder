#!/bin/bash
# Config file checker

echo "🔍 Checking AutoBuilder Config"
echo "=============================="
echo ""

# Check if config file exists
if [ -f "/etc/autobuilder/config.toml" ]; then
    echo "✅ Config file exists: /etc/autobuilder/config.toml"
    echo ""
    
    # Check telegram section
    if grep -q "\[telegram\]" /etc/autobuilder/config.toml; then
        echo "✅ [telegram] section found"
        echo ""
        echo "Telegram section content:"
        sed -n '/\[telegram\]/,/\[/p' /etc/autobuilder/config.toml | head -n 10
        echo ""
        
        # Check bot_token
        if grep -q "bot_token" /etc/autobuilder/config.toml; then
            BOT_TOKEN=$(grep "bot_token" /etc/autobuilder/config.toml | cut -d'"' -f2)
            if [ -z "$BOT_TOKEN" ] || [ "$BOT_TOKEN" = "YOUR_BOT_TOKEN_HERE" ]; then
                echo "❌ bot_token is not set or still has default value"
            else
                echo "✅ bot_token is set (length: ${#BOT_TOKEN} characters)"
            fi
        else
            echo "❌ bot_token not found in config"
        fi
        
        # Check chat_id
        if grep -q "chat_id" /etc/autobuilder/config.toml; then
            CHAT_ID=$(grep "chat_id" /etc/autobuilder/config.toml | cut -d'"' -f2)
            if [ -z "$CHAT_ID" ] || [ "$CHAT_ID" = "YOUR_CHAT_ID_HERE" ]; then
                echo "❌ chat_id is not set or still has default value"
            else
                echo "✅ chat_id is set: $CHAT_ID"
            fi
        else
            echo "❌ chat_id not found in config"
        fi
    else
        echo "❌ [telegram] section not found in config file"
    fi
else
    echo "❌ Config file not found: /etc/autobuilder/config.toml"
    echo ""
    echo "Creating from example..."
    sudo cp /opt/autobuilder/config/config.example.toml /etc/autobuilder/config.toml
    sudo chmod 600 /etc/autobuilder/config.toml
    sudo chown root:root /etc/autobuilder/config.toml
    echo "✅ Config file created. Please edit it: sudo nano /etc/autobuilder/config.toml"
fi

echo ""
echo "📝 To fix:"
echo "  sudo nano /etc/autobuilder/config.toml"
echo ""
echo "Make sure you have:"
echo "  [telegram]"
echo "  bot_token = \"your_actual_token_here\""
echo "  chat_id = \"your_chat_id_here\""
echo ""

