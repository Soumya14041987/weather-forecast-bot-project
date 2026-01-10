#!/bin/bash

# EC2 Setup Script for AWS Strands Agent SDK
# This script installs and configures the AWS Strands agent SDK on Ubuntu EC2 instance
# For Medium blog publication

set -e

echo "=========================================="
echo "AWS Strands Agent SDK Setup - Starting"
echo "=========================================="

# Update system packages
echo "Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# Install Python 3.11 and pip
echo "Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install Node.js and npm (required for AWS Strands SDK)
echo "Installing Node.js and npm..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install git
echo "Installing git..."
sudo apt install -y git

# Install build essentials (required for some Python packages)
echo "Installing build essentials..."
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# Create application directory
echo "Creating application directory..."
sudo mkdir -p /opt/aws-strands-agent
sudo chown -R ubuntu:ubuntu /opt/aws-strands-agent
cd /opt/aws-strands-agent

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate    

# Install AWS Strands Agent SDK and dependencies
echo "Installing AWS Strands Agent SDK..."
pip install --upgrade pip
pip install boto3 botocore
pip install strands-agents
pip install strands-agents-tools

# Install additional AWS and AI/ML dependencies
echo "Installing additional dependencies..."
pip install awscli
pip install requests

# Configure AWS CLI (user will need to add credentials)
echo "Configuring AWS CLI..."
mkdir -p ~/.aws
cat > ~/.aws/config << 'EOF'
[default]
region = us-east-1
output = json
EOF

echo ""
echo "NOTE: Please configure AWS credentials by running:"
echo "  aws configure"
echo "Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
echo ""

# Create instructions file for uploading application
echo "Creating setup instructions..."
cat > SETUP_INSTRUCTIONS.txt << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AWS STRANDS WEATHER FORECAST BOT - DEPLOYMENT INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: Upload Your Application Files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

From your local machine, upload the weather-forecast.py file to the EC2 instance:

Option A - Using SCP:
```bash
scp -i your-key.pem weather-forecast.py ubuntu@your-ec2-ip:/opt/aws-strands-agent/
```

Option B - Using SFTP:
```bash
sftp -i your-key.pem ubuntu@your-ec2-ip
cd /opt/aws-strands-agent
put weather-forecast.py
exit
```

Option C - Using Git (if your code is in a repository):
```bash
cd /opt/aws-strands-agent
git clone https://github.com/your-username/your-repo.git
cp your-repo/weather-forecast.py .
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2: Verify File Upload
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SSH into your EC2 instance and verify:
```bash
cd /opt/aws-strands-agent
ls -la weather-forecast.py
```

You should see the file with proper permissions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3: Set File Permissions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Make the file executable:
```bash
chmod +x weather-forecast.py
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4: Activate Virtual Environment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Activate the Python environment:
```bash
source activate.sh
```

Or manually:
```bash
source venv/bin/activate
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5: Test the Application
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run the weather forecast bot:
```bash
python weather-forecast.py
```

When prompted, enter a city name:
```
Which city would you like to check? San Francisco
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 6: Test Lambda Handler (Optional)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Test the Lambda handler function locally:
```bash
python -c "
from weather_forecast import lambda_handler
event = {'body': '{\"city\": \"Tokyo\"}'}
result = lambda_handler(event, None)
print(result)
"
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 7: Create a Test Script (Optional)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create a simple test script to demo multiple cities:
```bash
cat > test_weather_bot.py << 'TESTEOF'
from weather_forecast import analyze_weather

cities = ["San Francisco", "Tokyo", "London", "Paris"]

for city in cities:
    print(f"\n{'='*60}")
    print(f"Weather for {city}")
    print('='*60)
    result = analyze_weather(city)
    if "error" not in result:
        print(f"Temperature: {result['current']['temp']}°C")
        print(f"Summary: {result['summary']}")
    else:
        print(f"Error: {result['error']}")
TESTEOF

python test_weather_bot.py
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue: ModuleNotFoundError: No module named 'strands_agents'
Solution: Ensure virtual environment is activated and packages are installed
```bash
source venv/bin/activate
pip install strands-agents strands-agents-tools
```

Issue: AccessDeniedException from Bedrock
Solution: Configure AWS credentials
```bash
aws configure
```

Issue: File not found
Solution: Verify you're in the correct directory
```bash
cd /opt/aws-strands-agent
pwd
ls -la
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEXT STEPS FOR PRODUCTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Package for Lambda deployment
2. Set up API Gateway for HTTP access
3. Configure CloudWatch logging
4. Implement rate limiting
5. Add caching for weather data
6. Set up monitoring and alerts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

# Note: README.md should be in your project repository
# The setup script focuses on environment preparation only

# Set proper permissions
echo "Setting permissions..."
sudo chown -R ubuntu:ubuntu /opt/aws-strands-agent

# Create environment activation script
cat > /opt/aws-strands-agent/activate.sh << 'EOF'
#!/bin/bash
source /opt/aws-strands-agent/venv/bin/activate
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "AWS Strands Weather Forecast Bot - Environment Activated"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next Steps:"
echo "  1. Upload your weather-forecast.py file to this directory"
echo "  2. Run: python weather-forecast.py"
echo ""
echo "For detailed instructions, see: SETUP_INSTRUCTIONS.txt"
echo ""
EOF
chmod +x /opt/aws-strands-agent/activate.sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "AWS Strands Weather Forecast Bot - Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Installation Directory: /opt/aws-strands-agent"
echo ""
echo "What's Installed:"
echo "  ✓ Python 3.11 with virtual environment"
echo "  ✓ AWS Strands Agents SDK (strands-agents)"
echo "  ✓ Strands Agents Tools (strands-agents-tools)"
echo "  ✓ Boto3 for AWS Bedrock integration"
echo "  ✓ Requests library for API calls"
echo "  ✓ AWS CLI configured"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Configure AWS Credentials:"
echo "   aws configure"
echo "   (Enter your AWS Access Key, Secret Key, and Region: us-east-1)"
echo ""
echo "2. Upload Your Application File:"
echo "   From your local machine, run:"
echo "   scp -i your-key.pem weather-forecast.py ubuntu@$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):/opt/aws-strands-agent/"
echo ""
echo "3. Activate the Environment:"
echo "   cd /opt/aws-strands-agent"
echo "   source activate.sh"
echo ""
echo "4. Run Your Weather Forecast Bot:"
echo "   python weather-forecast.py"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DOCUMENTATION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  → Setup Instructions: /opt/aws-strands-agent/SETUP_INSTRUCTIONS.txt"
echo "  → View with: cat /opt/aws-strands-agent/SETUP_INSTRUCTIONS.txt"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "VERIFY INSTALLATION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Check installed packages:"
echo "  source /opt/aws-strands-agent/venv/bin/activate"
echo "  pip list | grep -E 'boto3|strands|requests'"
echo ""
echo "Expected output:"
echo "  boto3                    1.x.x"
echo "  strands-agents           0.x.x"
echo "  strands-agents-tools     0.x.x"
echo "  requests                 2.x.x"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Setup completed successfully! Follow the next steps above to deploy your bot."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
