# Take-Home Interview Project: Deploying Docker, RDS, and S3 Using CloudFormation

## Objective
The goal of this project is to create a CloudFormation template that provisions a Linux server running Docker, an Amazon RDS database, and an Amazon S3 bucket. This project will demonstrate skills in infrastructure as code, AWS services, and general cloud architecture.

## Project Overview
The task involves creating a CloudFormation template that sets up an environment to host a Dockerized web application. This environment will include an EC2 instance running Docker, an Amazon RDS database for persistent storage, and an S3 bucket for file uploads.

## Requirements

### 1. Architecture Diagram and Documentation
- Design an architecture diagram for the application
- Provide documentation explaining your design choices, configuration steps, and any assumptions made during the project

### 2. CloudFormation Template
Create a CloudFormation template (YAML) that includes the following resources:
- An EC2 instance running a specified Amazon Linux AMI (or another Linux distribution)
- An IAM role with permissions for the EC2 instance to access the S3 bucket and RDS
- An Amazon RDS instance (e.g., MySQL, PostgreSQL) with the necessary configurations (database name, instance type, etc.)
- An S3 bucket for file storage
- Security groups to allow:
  - HTTP/HTTPS access to the EC2 instance
  - Access from the EC2 instance to the chosen database
  - Access from the EC2 instance to the S3 bucket
- Optional configuration of security and availability features, such as a load balancer, autoscaling group, and/or web application firewall

### 3. Docker Configuration
Write a user data script to run on the EC2 instance that:
- Installs Docker and Docker Compose
- Pulls a Dockerized web application image from a container registry (you can use a public image for demonstration)
- Starts the Docker container and ensures it connects to the RDS database

### 4. Database Configuration
- Configure the RDS instance to accept connections from the EC2 instance
- Specify any initial database setup you want (e.g., creating tables or seeding data)

### 5. S3 Bucket
- Create an S3 bucket for storing uploaded files from the application
- Implement a bucket policy that allows the EC2 instance IAM role to upload files

### 6. Documentation
Create a README file that includes:
- A brief description of the project
- Instructions for deploying the CloudFormation stack
- Details about the Dockerized application and its configuration
- Any relevant connection strings or environment variables used

### 7. Testing (Optional)
- Write a basic test or script that verifies the functionality of the web application, ensuring it can connect to the RDS database and upload files to the S3 bucket

## Deliverables
A GitHub or GitLab repository containing:
- Architectural documentation
- CloudFormation templates
- README file with documentation
- Any user data scripts or additional configuration files

## Evaluation Criteria
- **CloudFormation Quality:** Correctness and completeness of the CloudFormation template
- **Code Quality:** Clarity and structure of the user data scripts and any Docker configuration
- **AWS Configuration:** Proper use of AWS services, IAM roles, and security groups
- **Documentation Quality:** Clarity, completeness, and ease of understanding
- **Functionality:** Ability of the application to interact with the RDS database and S3 bucket

## Optional Enhancements
If time allows, consider adding:
- Integration with CloudWatch for logging and monitoring

## Repository Structure
```
├── README.md                 # Main documentation
├── docs/                     # Detailed documentation
│   ├── architecture.md         # Architecture details
│   ├── deployment.md           # Deployment instructions
│   └── configuration.md        # Configuration guide
├── cloudformation/           # CloudFormation template
│   ├── main.yaml               # Main stack
│   └── params/                 # Parameter files
├── scripts/                  # Any helper scripts
│   └── user-data.sh            # EC2 user data script
├── docker/                   # Docker configurations
│   └── docker-compose.yml      # May not need 
└── tests/                    # Any testing scripts
    └── test_functionality.sh   # Testing data flow
```