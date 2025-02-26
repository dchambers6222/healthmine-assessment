# Healthmine Docker Web Application - Deployment Guide

This document provides step-by-step instructions for deploying the Healthmine Docker Web Application infrastructure using AWS CloudFormation.

<br>

## Prerequisites


Before deployment, ensure you have:

1. **AWS CLI**: Installed and configured with appropriate permissions
2. **S3 Dependencies Bucket**: You must create your own S3 bucket to host the required scripts
   - This bucket must be in the same region as your deployment
3. **Database Password**: A secure password for the RDS instance (min 8 characters)
4. **SSL Certificate** (Optional): ARN of an ACM certificate for HTTPS

<br>

## Preparation Steps


### 1. Create and Prepare S3 Dependencies Bucket

First, create your own S3 bucket to host the required scripts:

```bash
# Create a unique bucket name - replace with your own unique identifier
BUCKET_NAME="healthmine-assessment-dependencies-$(openssl rand -hex 4)"

# Create the bucket in your preferred region
aws s3 mb s3://${BUCKET_NAME} --region us-east-1

# Make note of this bucket name. You'll need it for the CloudFormation parameters
echo "Your dependencies bucket name is: ${BUCKET_NAME}"
```

<br>

Then upload the required scripts from the repository to your dependencies bucket root:
#### Option A: Using AWS CLI to copy files from the repository 
<details>
<summary>Click to expand/collapse</summary>

```bash
# Clone the repository
git clone https://github.com/dchambers6222/healthmine-assessment.git

# Navigate to the repository directory
cd healthmine-assessment

# Copy the scripts to your S3 bucket
aws s3 cp scripts/user-data.sh s3://${BUCKET_NAME}/
aws s3 cp scripts/test-connectivity.py s3://${BUCKET_NAME}/

# Clean up (optional)
cd .. && rm -rf healthmine-assessment
```
</details>

#### Option B: Using the AWS S3 Console UI 
<details>
<summary>Click to expand/collapse</summary>

1. Clone or download the repository from GitHub:
```bash
git clone https://github.com/dchambers6222/healthmine-assessment.git
```

2. Navigate to the AWS S3 Console: https://s3.console.aws.amazon.com/
3. Find and click on your bucket name
4. Click the "Upload" button
5. Click "Add files" or drag and drop the following files:
- healthmine-assessment/scripts/user-data.sh
- healthmine-assessment/scripts/test-connectivity.py
6. Click "Upload"
7. Verify that both files appear in the root of your bucket
</details>

<br>

##### **Important**: The CloudFormation template uses these specific file paths: 
- `s3://<your-bucket>/user-data.sh`
- `s3://<your-bucket>/test-connectivity.py`

Make sure the files are uploaded with exactly these names to your bucket's root.

<br> 

### 2. Parameter Preparation

The repository includes parameter files in both JSON and YAML formats under `cloudformation/params/`.

***Note***: Use parameters.json with the `--parameters file=` option or parameters.yaml with the `--parameters-file` option. If using AWS Management console to deploy, parameters can instead be edited in the deployment UI 

***Security tip***: For production deployments, sensitive values like DBPassword would be stored using AWS Secrets Manager or parameter overrides instead of in a parameter file.

<details>
<summary>Option A: Using parameters.json</summary>

Edit the `cloudformation/params/parameters.json` file with your specific values, especially:
- `DBPassword`: Your secure database password
- `ProjectDependenciesBucket`: The S3 bucket name you created in the previous step
</details>

<details>
<summary>Option B: Using parameters.yaml</summary>

Edit the `cloudformation/params/parameters.yaml` file with your specific values, especially:
- `DBPassword`: Your secure database password
- `ProjectDependenciesBucket`: The S3 bucket name you created in the previous step
</details>


<br>

## Deployment Methods


### Method 1: AWS Management Console

1. Sign in to the AWS Management Console
2. Navigate to CloudFormation service
3. Click "Create stack" > "With new resources (standard)"
4. Select "Upload a template file" and upload `cloudformation/main.yaml`
5. Click "Next"
6. Enter stack name (e.g., "healthmine-webapp")
7. Enter parameter values as required, making sure to:
   - Set your S3 dependencies bucket name
   - Use a secure database password
8. Click "Next"
9. Configure stack options (tags, permissions, etc.) if needed
10. Click "Next"
11. Review the configuration and click "Create stack"

### Method 2: AWS CLI

<details>
<summary>Option A: Deploy using JSON parameters file</summary>

```bash
# Clone the repository if you haven't already
git clone https://github.com/dchambers6222/healthmine-assessment.git
cd healthmine-assessment

# Update the parameters file with your values
# Be sure to replace YOUR-DEPENDENCIES-BUCKET-NAME with your actual bucket name
# and set a secure password

# Deploy the stack
aws cloudformation create-stack \
  --stack-name healthmine-webapp \
  --template-body file://cloudformation/main.yaml \
  --parameters file://cloudformation/params/parameters.json \
  --capabilities CAPABILITY_IAM
```
</details>

<details>
<summary>Option B: Deploy using YAML parameters file</summary>

```bash
# Clone the repository if you haven't already
git clone https://github.com/dchambers6222/healthmine-assessment.git
cd healthmine-assessment

# Update the parameters file with your values
# Be sure to replace YOUR-DEPENDENCIES-BUCKET-NAME with your actual bucket name
# and set a secure password

# Deploy the stack
aws cloudformation create-stack \
  --stack-name healthmine-webapp \
  --template-body file://cloudformation/main.yaml \
  --parameters-file cloudformation/params/parameters.yaml \
  --capabilities CAPABILITY_IAM
```
</details>

<details>
<summary>Option C: Deploy with inline parameters</summary>

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

Remember to replace `YOUR-DEPENDENCIES-BUCKET-NAME` with your actual bucket name and set a secure password.
</details>

<br>

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

<br>

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

***Note***: You will need these for the testing script.


<br>

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

<br>

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

<br>

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

<details>
<summary>Option A: Update using JSON parameters file</summary>

```bash
aws cloudformation update-stack \
  --stack-name healthmine-webapp \
  --template-body file://cloudformation/main.yaml \
  --parameters file://cloudformation/params/parameters.json \
  --capabilities CAPABILITY_IAM
```
</details>

<details>
<summary>Option B: Update using YAML parameters file</summary>

```bash
aws cloudformation update-stack \
  --stack-name healthmine-webapp \
  --template-body file://cloudformation/main.yaml \
  --parameters-file cloudformation/params/parameters.yaml \
  --capabilities CAPABILITY_IAM
```
</details>

<br>

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

**Note:** Because this will delete all resources created by the stack, including the RDS instance and S3 bucket, the RDS instance will create a final snapshot before deletion (as configured in the template). This will have to be removed after as well.