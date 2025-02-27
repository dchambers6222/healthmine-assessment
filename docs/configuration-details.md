# Configuration Documentation

## Design Choices and Reasoning

### Infrastructure Design

- **Container Technology**: I used plain Docker on EC2 as specified in the assessment requirements rather than ECS or EKS. This approach demonstrates fundamental container deployment while maintaining simplicity. In production, a managed Kubernetes service (EKS) with a microservice architecture would be more appropriate for scalability and manageability.

- **Single CloudFormation Stack**: I chose this over nested stacks for simplicity and ease of maintenance. This simplified my deployment and troubleshooting for demonstration purposes. In production, nested stacks might be preferable for modular infrastructure management.

- **VPC Configuration**: I'm using the default AWS VPC CIDR (10.0.0.0/16) with two public subnets across availability zones for this demonstration. In production, I'd implement a custom VPC with private subnets and network segregation for better security isolation.

- **Auto Scaling Group**: I implemented simple scaling policies for the demonstration. The minimum size of 1 and maximum of 3 instances provides basic high availability while controlling costs. In production, I'd use target tracking policies for more granular scaling based on actual metrics.

- **Load Balancer Configuration**: I set up an Application Load Balancer with HTTP/HTTPS listeners to provide scalability and availability. I specifically chose port 8080 for the health probe to separate application traffic from health check traffic, a common practice in microservice architectures.

### Docker Configuration

- **Container Selection**: I selected the `yeasy/simple-web` Docker image because it already integrates source and destination communication checking by returning IP information automatically. This simplified my development while still demonstrating the container connectivity requirements.

- **Health Check Container**: I separated the main application from the health check by using a dedicated nginx container on port 8080. This pattern follows the separation of concerns principle and allows independent scaling of components.

- **User Data Script**: I designed this to automatically provision Docker and launch containers upon instance creation. The script retrieves configuration values directly from CloudFormation stack outputs, demonstrating infrastructure-as-code best practices.

### Database Configuration

- **RDS Instance Type**: I selected `db.t3.micro` as it provides a cost-effective option for demonstration purposes while still supporting encryption at rest and other essential security features.

- **Storage Type**: I chose `gp2` storage as it's well-suited for development/testing environments per AWS documentation. For production workloads with higher I/O demands, `gp3` or provisioned IOPS would be more appropriate.

- **Character Set and Collation**: I initially configured for UTF8, but after research, updated to UTF8MB4 (with collation `utf8mb4_general_ci`) as it's the MySQL 8.0 default and supports a wider range of special characters, providing better internationalization support.

- **Multi-AZ Configuration**: I enabled this for automated failover and improved availability, demonstrating production-ready design principles even in a test environment.

- **Backup Retention**: I configured a 7-day backup retention period (verified in main.yaml) to balance data protection with cost efficiency for the assessment. This timeframe provides sufficient recovery options while preventing unnecessary storage costs.

### Storage Configuration

- **S3 Lifecycle Policy**: I configured S3 objects to transition to Standard-IA after 90 days and deletion after 365 days for cost optimization. This approach balances accessibility with cost-efficiency for the demonstration.

- **S3 Bucket Permissions**: I granted full access (get, put, delete, and list) to the EC2 IAM Role for flexibility in the demonstration environment. In production, more restrictive permissions following the principle of least privilege would be appropriate.

- **Versioning and Encryption**: I enabled S3 bucket versioning and AES-256 encryption for data protection, demonstrating security best practices.

### Security Configuration

- **Load Balancer Choice**: I selected Application Load Balancer rather than Network Load Balancer due to its support for HTTP/HTTPS health checks, SSL termination capabilities, and potential for multiple target groups. This provides a more feature-rich entry point for the application while maintaining high availability.

- **Security Groups**: I configured these in a layered approach:
  - ALB security group accepts traffic from the internet on ports 80, 443, and 8080
  - EC2 security group accepts traffic only from the ALB on application ports and SSH for testing
  - RDS security group accepts traffic only from the EC2 security group on port 3306

- **SSH Access**: I maintained open SSH access (0.0.0.0/0) for testing purposes. In production, I would restrict this to specific IP ranges or VPN/bastion hosts.

- **IAM Roles and Policies**: I created these with specific permissions for EC2 instances to access S3, CloudWatch, and Systems Manager. I followed the principle of least privilege while maintaining operational functionality. I used a single EC2 instance role with multiple attached policies to centralize access control and simplify permission management.

### Monitoring and Logging

- **CloudWatch Integration**: I configured a log group with 30-day retention to balance operational visibility with cost efficiency. I granted the EC2 instance IAM role specific CloudWatch permissions:
  - `cloudwatch:PutMetricData`, `cloudwatch:GetMetricStatistics`, `cloudwatch:ListMetrics`
  - `logs:CreateLogStream`, `logs:CreateLogGroup`, `logs:PutLogEvents`, `logs:DescribeLogStreams`

- **Test Connectivity Script**: I developed a comprehensive Python script to verify all infrastructure components:
  - Used the `requests` library for HTTP testing due to its simplicity and excellent documentation
  - Utilized `mysql.connector` for RDS connectivity testing, enabling verification of both connection and CRUD operations
  - Implemented `boto3` for S3 testing with appropriate error handling

## Implementation Challenges and Solutions

### Security Group Configuration

- I encountered an issue where adding the 8080 port to the EC2 security group inadvertently overwrote the port 80 setting. My solution was to add a separate ingress rule for port 80.

### Database Character Set Configuration

- I initially set collation server to UTF8, but discovered that the default server for UTF8 is `utf8_general_ci`. After further research, I updated to UTF8MB4 (MySQL 8.0 default) which allows for a wider range of special characters:
  ```yaml
  character_set_server: utf8mb4
  collation_server: utf8mb4_general_ci
  ```

### Auto Scaling Policy Configuration

- I identified that the ScaleUpPolicy contained an additional parameter (`EstimatedInstanceWarmup`) not supported by SimpleScaling policy type. I removed this parameter to ensure compatibility.

### Load Balancer Health Checks

- The health check endpoint was failing despite the container running correctly. My investigation revealed two issues:
  1. No listener was configured on the ALB for port 8080 - I added an additional listener
  2. The ALB security group needed to allow incoming traffic on port 8080 - I updated security group rules

### EC2 User Data Execution

- I initially experienced a 502 bad gateway when accessing the application. I traced the issue to permissions for the external S3 bucket storing the user-data script being incorrectly mapped. This prevented the script from running and consequently Docker was never set up.

## Testing Methodology

My testing after deployment follows a systematic approach:

1. **S3 Connectivity Test**: 
   - Created and copied test files to verify S3 bucket access
   - Confirmed IAM roles were working correctly

2. **Application Load Balancer Test**:
   - Verified HTTP endpoints were accessible
   - Confirmed health check was properly configured and responding

3. **RDS Connectivity Test**:
   - Verified database connections and operations
   - Tested creating tables and inserting records

4. **Automation Script**:
   I created the `test-connectivity.py` script to automate validation of all components:
   ***Note***: this script is copied into the system PATH during setup, and set to executable
   ```bash
   # Run after SSH into EC2 instance
    test-connectivity.py <alb_dns_name> <rds_endpoint> <s3_bucket> <db_password>
   ```

## Production Considerations

For adaptation to a production environment, I would recommend several enhancements:

1. **Web Application Firewall (WAF)**: Though listed as optional in the assessment, a WAF would be essential in production to protect against common web exploits and attacks. I omitted this from the current implementation to prioritize demonstrating high availability and data retention features within the time constraints.

2. **Security Enhancements**:
   - Move RDS to private subnets
   - Restrict SSH access to specific IP ranges
   - Use AWS Secrets Manager for database credentials
   - Implement more granular IAM policies

3. **Networking**:
   - Implement a proper network architecture with private subnets
   - Use VPC endpoints for AWS services to avoid public internet traffic
   - Implement network ACLs as an additional security layer

4. **Monitoring Enhancements**:
   - Add CloudWatch alarms for resource utilization
   - Implement enhanced health checks
   - Consider AWS X-Ray for distributed tracing

5. **Database Optimizations**:
   - Use parameter groups optimized for workload type
   - Consider read replicas for read-heavy workloads
   - Implement automated backup strategies

6. **Deployment Pipeline**:
   - Implement CI/CD for infrastructure changes
   - Add automated testing before deployment
   - Implement blue/green deployment capabilities

These considerations would elevate my demonstration architecture to a production-ready solution with improved security, scalability, and operational efficiency.