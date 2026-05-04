#!/bin/bash

echo "Russell 1000 Stock Screener - Telegram Bot Setup"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}$1${NC}"
}

print_error() {
    echo -e "${RED}Error: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

print_info() {
    echo -e "${BLUE}$1${NC}"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check SAM CLI
if ! command -v sam &> /dev/null; then
    print_error "SAM CLI not found. Please install SAM CLI first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "template.yaml" ]; then
    print_error "template.yaml not found. Please run this script from your project root."
    exit 1
fi

print_status "Prerequisites check passed"

# Step 1: Build and Deploy
echo ""
echo "Step 1: Building and deploying Lambda functions..."

sam build --use-container
if [ $? -ne 0 ]; then
    print_error "SAM build failed"
    exit 1
fi

print_status "Build completed"

sam deploy
if [ $? -ne 0 ]; then
    print_error "SAM deploy failed"
    exit 1
fi

print_status "Deployment completed"

# Step 2: Get the webhook URL
echo ""
echo "Step 2: Getting webhook URL..."

WEBHOOK_URL=$(aws cloudformation describe-stacks \
    --stack-name stock-screener-test \
    --query 'Stacks[0].Outputs[?OutputKey==`TelegramWebhookUrl`].OutputValue' \
    --output text 2>/dev/null)

if [ -z "$WEBHOOK_URL" ]; then
    print_error "Could not retrieve webhook URL from CloudFormation"
    print_info "Please check your stack name and try manually:"
    print_info "aws cloudformation describe-stacks --stack-name YOUR_STACK_NAME"
    exit 1
fi

print_status "Webhook URL: $WEBHOOK_URL"

# Step 3: Get Bot Token
echo ""
echo "Step 3: Retrieving bot token..."

BOT_TOKEN=$(aws ssm get-parameter \
    --name "/screener/telegram/bot_token" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text 2>/dev/null)

if [ -z "$BOT_TOKEN" ]; then
    print_error "Bot token not found in Parameter Store"
    print_info "Please run: ./setup_telegram_params.sh first"
    exit 1
fi

print_status "Bot token retrieved"

# Step 4: Set Telegram Webhook
echo ""
echo "Step 4: Setting up Telegram webhook..."

WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
    -d "url=${WEBHOOK_URL}" \
    -d "drop_pending_updates=true")

# Check if webhook was set successfully
if echo "$WEBHOOK_RESPONSE" | grep -q '"ok":true'; then
    print_status "Telegram webhook set successfully"
else
    print_error "Failed to set Telegram webhook"
    print_info "Response: $WEBHOOK_RESPONSE"
    exit 1
fi

# Step 5: Test webhook
echo ""
echo "Step 5: Testing webhook..."

WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo")
print_info "Webhook info: $WEBHOOK_INFO"

# Step 6: Get bot info
BOT_INFO=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe")
BOT_USERNAME=$(echo "$BOT_INFO" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)

echo ""
print_status "Telegram Bot Setup Complete"
echo ""
echo "Bot details:"
echo "   • Bot Username: @$BOT_USERNAME"
echo "   • Webhook URL: $WEBHOOK_URL"
echo "   • Status: Active"
echo ""
echo "Testing your bot:"
echo "   1. Open Telegram and search for: @$BOT_USERNAME"
echo "   2. Start a chat and send: /start"
echo "   3. Try these commands:"
echo "      • /screen - View top drawdown candidates"
echo "      • /portfolio - Your current positions"
echo "      • /monitor - Check profit targets"
echo "      • /account - Alpaca account summary"
echo "      • /help - Full command list"
echo ""
print_warning "Note: If this is a new bot, make sure to message it first before it can send you messages!"