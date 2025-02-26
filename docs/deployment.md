# Healthmine Docker Web Application - Deployment Guide

This document provides step-by-step instructions for deploying the Healthmine Docker Web Application infrastructure using AWS CloudFormation.

## Prerequisites

Before deployment, ensure you have:

1. **AWS CLI**: Installed and configured with appropriate permissions
2. **S3 Dependencies Bucket**: You must create your own S3 bucket to host the required scripts
   - The template default (`healthmine-docker-assessment-bucket`) is just a placeholder
   - S3 bucket names are globally unique, so you'll need to create your own with a unique name
   - This bucket must be in the same region as your deployment
3. **Database Password**: A secure password for the RDS instance (min 8 characters)
4. **SSL Certificate** (Optional): ARN of an ACM certificate for HTTPS

## Preparation Steps

### 1. Create and Prepare S3 Dependencies Bucket

First, create your own S3 bucket to host the required scripts:

```bash
# Create a unique bucket name - replace with your own unique identifier
BUCKET_NAME="healthmine-assessment-$(openssl rand -hex 4)"

# Create the bucket in your preferred region
aws s3 mb s3://${BUCKET_NAME} --region us-east-1

# Make note of this bucket name as you'll need it for the CloudFormation parameters
echo "Your dependencies bucket name is: ${BUCKET_NAME}"
```

Then upload the required scripts from the repository to your dependencies bucket root:

```bash
# Copy both scripts to your S3 bucket
aws s3 cp scripts/user-data.sh s3://${BUCKET_NAME}/
aws s3 cp scripts/test-connectivity.py s3://${BUCKET_NAME}/
```

**Important**: The CloudFormation template uses these specific file paths:
- `s3://<your-bucket>/user-data.sh`
- `s3://<your-bucket>/test-connectivity.py`

Make sure the files are uploaded with exactly these names to your bucket's root.

### 2. Parameter Preparation

Prepare the parameters required for deployment. You can either provide these directly during stack creation or create a parameters file:

**parameters.json**:
```json
[
  {
    "ParameterKey": "ProjectNamePrefix",
    "ParameterValue": "healthmine"
  },
  {
    "ParameterKey": "EnvironmentType",
    "ParameterValue": "assessment"
  },
  {
    "ParameterKey": "HTTPHealthPort",
    "ParameterValue": "8080"
  },
  {
    "ParameterKey": "CertificateARN",
    "ParameterValue": ""
  },
  {
    "ParameterKey": "DBUsername",
    "ParameterValue": "admin"
  },
  {
    "ParameterKey": "DBPassword",
    "ParameterValue": "YourSecurePassword"
  },
  {
    "ParameterKey": "InstanceType",
    "ParameterValue": "t3.micro"
  },
  {
    "ParameterKey": "ProjectDependenciesBucket",
    "ParameterValue": "YOUR-DEPENDENCIES-BUCKET-NAME"
  }
]
```

## Deployment Methods

### Method 1: AWS Management Console

1. Sign in to the AWS Management Console
2. Navigate to CloudFormation service
3. Click "Create stack" > "With new resources (standard)"
4. Select "Upload a template file" and upload `cloudformation/main.yaml`
5. Click "Next"
6. Enter stack name (e.g., "healthmine-webapp")
7. Enter parameter values as required
8. Click "Next"
9. Configure stack options (tags, permissions, etc.) if needed
10. Click "Next"
11. Review the configuration and click "Create stack"

### Method 2: AWS CLI

Deploy using the AWS CLI with parameters file:

```bash
aws cloudformation create-stack \
  --stack-name healthmine-webapp \
  --template-body file://cloudformation/main.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM
```

Or with inline parameters:

```bash
aws cloudformation create-stack \
  --stack-name healthmine-webapp \
  --template-body file://cloudformation/main.yaml \
  --parameters \
      ParameterKey=ProjectNamePrefix,ParameterValue=healthmine \
      ParameterKey=EnvironmentType,ParameterValue=assessment \
      ParameterKey=HTTPHealthPort,ParameterValue=8080 \
      ParameterKey=CertificateARN,ParameterValue="" \
      ParameterKey=DBUsername,ParameterValue=admin \
      ParameterKey=DBPassword,ParameterValue=YourSecurePassword \
      ParameterKey=InstanceType,ParameterValue=t3.micro \
      ParameterKey=ProjectDependenciesBucket,ParameterValue=YOUR-DEPENDENCIES-BUCKET-NAME \
  --capabilities CAPABILITY_IAM
```

## Stack Deployment Monitoring

### Console Monitoring

1. Navigate to the CloudFormation service
2. Select your stack
3. Go to the "Events" tab to monitor deployment progress
4. Wait for the status to change to "CREATE_COMPLETE"

### CLI Monitoring

```bash
aws cloudformation describe-stacks \
  --stack-name healthmine-webapp \
  --query "Stacks[0].StackStatus"
```

Or monitor events:

```bash
aws cloudformation describe-stack-events \
  --stack-name healthmine-webapp \
  --query "StackEvents[].{Timestamp:Timestamp,Resource:LogicalResourceId,Status:ResourceStatus,Reason:ResourceStatusReason}"
```

## Accessing Deployment Outputs

After successful deployment, retrieve the outputs to access your resources:

### Console Method

1. Navigate to the CloudFormation service
2. Select your stack
3. Go to the "Outputs" tab

### CLI Method

```bash
aws cloudformation describe-stacks \
  --stack-name healthmine-webapp \
  --query "Stacks[0].Outputs"
```

Key outputs include:
- `LoadBalancerDNSName` - URL to access the web application
- `RDSEndpoint` - Database connection endpoint
- `S3BucketName` - Application S3 bucket name
- `CloudWatchLogGroup` - Log group for application logs

## Testing the Deployment

### 1. Basic Connectivity Testing

Access the web application via the load balancer URL:
```
http://<LoadBalancerDNSName>
```

Check the health endpoint:
```
http://<LoadBalancerDNSName>:8080
```

### 2. Comprehensive Testing

SSH into any EC2 instance in the Auto Scaling Group, then run the connectivity test:

```bash
# Use your own dependencies bucket name here
aws s3 cp s3://YOUR-DEPENDENCIES-BUCKET-NAME/test-connectivity.py /tmp/test-connectivity.py
sudo chmod +x /tmp/test-connectivity.py
/tmp/test-connectivity.py <LoadBalancerDNSName> <RDSEndpoint> <S3BucketName> <DBPassword>
```

This script will test:
- Load balancer connectivity
- Health endpoint accessibility
- RDS database connection and operations
- S3 bucket upload and deletion operations

## Troubleshooting

### Common Issues and Solutions

1. **Stack Creation Failure**
   - Check CloudFormation events for specific error messages
   - Verify IAM permissions for the user or role executing the deployment

2. **EC2 Instance Not Connecting to RDS**
   - Check security groups to ensure port 3306 is open from EC2 to RDS
   - Verify that the user-data script executed successfully by checking `/var/log/user-data.log`

3. **Health Checks Failing**
   - SSH into an EC2 instance and verify Docker containers are running:
     ```bash
     docker ps
     ```
   - Check if the health endpoint is responding locally:
     ```bash
     curl http://localhost:8080
     ```

4. **Application Not Accessible via Load Balancer**
   - Verify target group health in the EC2 console
   - Check ALB security group allows traffic on ports 80 and 8080
   - Verify EC2 security group allows traffic from the ALB

### Viewing Logs

Check Docker logs:
```bash
docker logs simple-web
docker logs health-check
```

Check user-data script execution logs:
```bash
cat /var/log/user-data.log
```

Check CloudWatch logs:
```bash
aws logs get-log-events \
  --log-group-name /${ProjectNamePrefix}/${EnvironmentType}/app-logs \
  --log-stream-name <log-stream-name>
```

## Updating the Stack

To update the stack with new parameters or template changes:

### Console Method

1. Navigate to the CloudFormation service
2. Select your stack
3. Click "Update"
4. Choose update method (Replace current template or Use current template)
5. Update parameters as needed
6. Click through the wizard and confirm updates

### CLI Method

```bash
aws cloudformation update-stack \
  --stack-name healthmine-webapp \
  --template-body file://cloudformation/main.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM
```

## Cleaning Up Resources

When you're finished with the infrastructure, you can delete all resources:

### Console Method

1. Navigate to the CloudFormation service
2. Select your stack
3. Click "Delete"
4. Confirm deletion

### CLI Method

```bash
aws cloudformation delete-stack --stack-name healthmine-webapp
```

**Note:** This will delete all resources created by the stack, including the RDS instance and S3 bucket. The RDS instance will create a final snapshot before deletion as configured in the template.