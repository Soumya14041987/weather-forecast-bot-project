#!/bin/bash

echo "🚀 Starting deployment..."
echo ""

# Package Lambda function
echo "📦 Packaging Lambda function..."
cd "$(dirname "$0")"
rm -rf package weather-bot.zip

mkdir package
cd package
pip install -r ../requirements.txt -t . --no-cache-dir
cp ../weather-forecast.py .
find . -type d \( -name "*.dist-info" -o -name "*.egg-info" -o -name "__pycache__" \) -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete
zip -r ../weather-bot.zip . -x "*.pyc" "*/__pycache__/*" > /dev/null
cd ..

echo "✅ Lambda package created: weather-bot.zip ($(du -h weather-bot.zip | cut -f1))"
echo ""

# Upload frontend to S3
BUCKET_NAME="global-weather-bot"

echo "☁️  Uploading frontend to S3..."

aws s3 cp frontend/index.html s3://$BUCKET_NAME/index.html --content-type "text/html" && echo "  ✓ index.html"
aws s3 cp frontend/styles.css s3://$BUCKET_NAME/styles.css --content-type "text/css" && echo "  ✓ styles.css"
aws s3 cp frontend/app.js s3://$BUCKET_NAME/app.js --content-type "application/javascript" && echo "  ✓ app.js"

echo ""
echo "✅ Frontend uploaded to S3"
echo ""
echo "📝 Next steps:"
echo "   1. Upload weather-bot.zip to Lambda Console"
echo "   2. Test your app at: http://$BUCKET_NAME.s3-website-us-east-1.amazonaws.com"
echo ""