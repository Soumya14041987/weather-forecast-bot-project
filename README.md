AI-Powered Weather Forecast Application

A modern weather forecast application built with AWS Lambda, Amazon Bedrock (Nova Lite), and Open-Meteo API. This project demonstrates how to build a production-ready serverless application with AI-powered insights for under $5 per month.

---

Features

- 10-day weather forecast with minimum and maximum temperatures
- "Feels like" temperature calculations using apparent temperature data
- Automated weather alerts for rain, snow, and storms with timing predictions
- AI-generated weather insights using Amazon Bedrock Nova Lite
- Real-time data from Open-Meteo API (completely free)
- Beautiful mobile-first user interface with glassmorphism design
- Auto-search functionality with 800ms debounce
- Fully responsive design that works on desktop and mobile
- Serverless architecture that scales automatically

---

Architecture Overview

The application follows a simple flow:

Browser → S3 Static Website → Lambda Function → Bedrock AI + Weather APIs → Response

Components:
- Frontend: HTML, CSS, JavaScript hosted on S3
- Backend: Python Lambda function
- AI Service: Amazon Bedrock Nova Lite for weather analysis
- Data Sources: Open-Meteo API for weather data, Geocoding API for coordinates

---

Project Structure

aws-strands-agent/
├── weather-forecast.py      (Lambda function handler)
├── requirements.txt         (Python dependencies)
├── deploy.sh               (Deployment script)
├── frontend/
│   ├── index.html          (Main HTML)
│   ├── styles.css          (Responsive CSS)
│   └── app.js              (Frontend JavaScript)
├── README.md               (This file)
└── weather.md              (Code explanation)

---

Getting Started

Prerequisites

You'll need:
- Python 3.11 or higher
- AWS Account with Bedrock access enabled
- AWS CLI configured with appropriate credentials
- Basic understanding of Python and REST APIs

System Requirements:
- 4GB RAM minimum
- 2GB free disk space
- Internet connection
- Modern web browser

---

Installation Steps

Step 1: Clone and Setup

Clone the repository and set up your environment:

```
git clone <your-repo>
cd aws-strands-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, use `.venv\Scripts\activate` instead.

Step 2: Test Locally

Run the script locally to verify everything works:

```
python weather-forecast.py
```

Enter a city name when prompted. You should see weather analysis results.

Step 3: Deploy

Run the deployment script:

```
bash deploy.sh
```

This will:
- Package the Lambda function with all dependencies
- Create weather-bot.zip (approximately 40MB)
- Upload frontend files to S3
- Display next steps

Step 4: Create Lambda Function

Using AWS Console:

1. Navigate to AWS Lambda Console
2. Click "Create function"
3. Select "Author from scratch"
4. Configure:
   - Function name: weather-forecast-app
   - Runtime: Python 3.11
   - Architecture: x86_64
5. Click "Create function"
6. Upload weather-bot.zip under Code section
7. Set Handler to: weather-forecast.lambda_handler
8. Configure:
   - Memory: 512 MB
   - Timeout: 30 seconds

Using AWS CLI:

```
aws lambda create-function \
  --function-name weather-forecast-app \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-weather-role \
  --handler weather-forecast.lambda_handler \
  --zip-file fileb://weather-bot.zip \
  --timeout 30 \
  --memory-size 512
```

Step 5: Create Function URL

In AWS Console:
1. Go to your Lambda function
2. Navigate to Configuration → Function URL
3. Click "Create function URL"
4. Set Auth type to NONE
5. Leave CORS disabled (handled in code)
6. Save and copy the URL

Using AWS CLI:

```
aws lambda create-function-url-config \
  --function-name weather-forecast-app \
  --auth-type NONE
```

Step 6: Configure Frontend

Edit frontend/app.js and update the Lambda URL:

```javascript
const LAMBDA_URL = 'https://YOUR-LAMBDA-URL.lambda-url.us-east-1.on.aws/';
```

Step 7: Setup S3 Bucket

Create an S3 bucket for hosting:

1. Go to S3 Console
2. Create bucket with a unique name (e.g., weather-app-yourname)
3. Uncheck "Block all public access"
4. Enable static website hosting in Properties
5. Set index document to index.html
6. Add bucket policy for public read access

Bucket Policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

Step 8: Access Your Application

Open your browser and navigate to:
http://global-weather-bot.s3-website-us-east-1.amazonaws.com

---

Configuration

IAM Permissions

Your Lambda execution role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "arn:aws:bedrock:*::foundation-model/us.amazon.nova-lite-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

Enable Bedrock Access

1. Go to AWS Bedrock Console
2. Click "Model access" in the sidebar
3. Request access to "Amazon Nova Lite"
4. Wait for approval (usually instant)

---

Testing

Test Lambda Function

Use this test event in AWS Console:

```json
{
  "version": "2.0",
  "routeKey": "$default",
  "rawPath": "/",
  "headers": {
    "content-type": "application/json"
  },
  "requestContext": {
    "http": {
      "method": "POST",
      "path": "/"
    }
  },
  "body": "{\"city\": \"London\"}",
  "isBase64Encoded": false
}
```

Expected Response:

```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "{\"location\":{\"city\":\"London\",...}}"
}
```

Test Frontend Locally

```
cd frontend
python3 -m http.server 8000
```

Open http://localhost:8000 in your browser.

---

API Response Format

The Lambda function returns structured JSON:

```json
{
  "location": {
    "city": "London",
    "country": "United Kingdom",
    "lat": 51.5074,
    "lon": -0.1278
  },
  "current": {
    "temp": 15.2,
    "feels_like": 14.1,
    "temp_max": 18.5,
    "temp_min": 12.3
  },
  "summary": "Pleasant weather expected...",
  "current_condition": "partly-cloudy",
  "insights": [
    "Maximum temperatures are decreasing steadily",
    "Nighttime temperatures are falling significantly"
  ],
  "recommendation": "Enjoy outdoor activities...",
  "forecast": [
    {
      "date": "2026-01-04",
      "temp_max": 18.5,
      "temp_min": 12.3,
      "precipitation": 0.0,
      "snowfall": 0.0
    }
  ],
  "alerts": []
}
```

---

Troubleshooting

Common Issues and Solutions

"City not found" Error
- Check spelling of city name
- Try major cities first
- Use English city names

CORS Error in Browser
- Ensure Lambda Function URL CORS is disabled
- Verify Lambda returns Access-Control-Allow-Origin header
- Check browser console for exact error

502 Bad Gateway
- Check Lambda CloudWatch logs
- Verify Bedrock model access is enabled
- Increase Lambda timeout to 30+ seconds
- Verify IAM permissions

"Undefined" or "NaN" in UI
- Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
- Clear browser cache
- Check browser console for errors
- Verify Lambda returns all required fields

Lambda Package Too Large
- Current size is about 40MB (under 50MB limit)
- If you add dependencies and exceed limit, use Lambda Layers
- Or upload zip to S3 and deploy from there

---

Cost Estimate

Based on 10,000 requests per month:

Service: Lambda
Usage: 10K invocations, 512MB, 5s average
Cost: $0.10

Service: Bedrock
Usage: 10K requests, approximately 500 tokens each
Cost: $4.00

Service: S3
Usage: 1GB storage, 10K requests
Cost: $0.05

Service: Data Transfer
Usage: 1GB outbound
Cost: $0.09

Total Monthly Cost: Approximately $4.24

Free Tier Benefits:
- Lambda: 1M requests per month free
- S3: 5GB storage, 20K GET requests free
- Bedrock: Pay as you go (no free tier)

---

Security Considerations

For production deployments:

1. Add authentication to Lambda Function URL
2. Use CloudFront for HTTPS and better performance
3. Implement API rate limiting to prevent abuse
4. Input validation is already implemented
5. No API keys needed (all services use IAM)

---

Production Enhancements

Add CloudFront CDN

```
aws cloudfront create-distribution \
  --origin-domain-name YOUR-BUCKET.s3.amazonaws.com \
  --default-root-object index.html
```

Add Custom Domain

1. Register domain in Route 53
2. Create SSL certificate in ACM
3. Configure CloudFront with custom domain
4. Update DNS records

Add Monitoring

```
aws lambda update-function-configuration \
  --function-name weather-forecast-app \
  --layers arn:aws:lambda:us-east-1:580247275435:layer:LambdaInsightsExtension:14
```

Add Caching

Implement Redis or ElastiCache to cache weather data for 1 hour.

---

Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

License

MIT License - Free to use for personal or commercial purposes.

---

Support

For issues or questions:
- Open a GitHub issue
- Check CloudWatch logs for Lambda errors
- Review AWS Bedrock documentation

---

Acknowledgments

- Open-Meteo API for free weather data
- Amazon Bedrock for AI-powered insights
- AWS Lambda for serverless compute
- Inter Font for typography

---

Built using AWS Serverless Technologies
