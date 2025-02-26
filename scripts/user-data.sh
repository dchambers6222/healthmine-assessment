#!/bin/bash
# Set up standard logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# Update then install Docker
yum update -y
yum install -y docker aws-cli jq
systemctl start docker
systemctl enable docker

# Get configuration info from the cloud formation stack
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
STACK_NAME=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=aws:cloudformation:stack-name" --query "Tags[0].Value" --output text --region $REGION)

RDS_ENDPOINT=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='RDSEndpoint'].OutputValue" --output text --region $REGION)
S3_BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='S3BucketName'].OutputValue" --output text --region $REGION)

# Create health check file
mkdir -p /health
echo "OK" > /health/index.html

# Run the simple web container
docker run -d --name simple-web -p 80:80 \
  -e RDS_ENDPOINT="$RDS_ENDPOINT" \
  -e S3_BUCKET="$S3_BUCKET" \
  yeasy/simple-web:latest

# Run separate container for health check
docker run -d --name health-check -p 8080:80 -v /health:/usr/share/nginx/html:ro nginx:alpine


# Install dependencies for the test-connectivity script
yum install -y python3 python3-pip
pip3 install boto3 mysql-connector-python
pip3 install requests

# Copy the test-connectivity script from seperate S3 bucket
aws s3 cp s3://${ProjectDependenciesBucket}/test-connectivity.py /usr/local/bin/
chmod +x /usr/local/bin/test-connectivity.py