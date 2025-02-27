# Configuration Documentation

## Design Choices and Reasoning

### Infrastructure Design

- **Container Technology**: Used plain Docker on EC2 as specified in the assessment requirements rather than ECS or EKS. This approach demonstrates fundamental container deployment while maintaining simplicity. In a production environment, a managed Kubernetes service (EKS) with a microservice architecture would be more appropriate for scalability and manageability.

- **Single CloudFormation Stack**: Chosen over nested stacks for simplicity and ease of maintenance. This approach simplifies deployment and troubleshooting for demonstration purposes. In a production environment, nested stacks might be preferable for modular infrastructure management.

- **VPC Configuration**: Used default AWS VPC CIDR (10.0.0.0/16) with two public subnets across availability zones for demonstration. In a production environment, a custom VPC with private subnets and network segregation would be preferable for better security isolation.

- **Auto Scaling Group**: Implemented with simple scaling policies for demonstration. The minimum size of 1 and maximum of 3 instances provides basic high availability while controlling costs. In production, target tracking policies would offer more granular scaling based on actual metrics.

- **Load Balancer Configuration**: Application Load Balancer with HTTP/HTTPS listeners provides scalability and availability. Port 8080 was specifically chosen for the health probe to separate application traffic from health check traffic, a common practice in microservice architectures.

### Docker Configuration

- **Container Selection**: The `yeasy/simple-web` Docker image was chosen because it already integrates source and destination communication checking by returning IP information automatically. This simplified development while still demonstrating the container connectivity requirements.

- **Health Check Container**: Separated the main application from the health check by using a dedicated nginx container on port 8080. This pattern follows the separation of concerns principle and allows independent scaling of components.

- **User Data Script**: Designed to automatically provision Docker and launch containers upon instance creation. The script retrieves configuration values directly from CloudFormation stack outputs, demonstrating infrastructure-as-code best practices.

### Database Configuration

- **RDS Instance Type**: Selected `db.t3.micro` as it provides a cost-effective option for demonstration purposes while still supporting encryption at rest and other essential security features.

- **Storage Type**: Chose `gp2` storage as it's well-suited for development/testing environments per AWS documentation. For production workloads with higher I/O demands, `gp3` or provisioned IOPS would be more appropriate.

- **Character Set and Collation**: Initially configured for UTF8, but after research, updated to UTF8MB4 (with collation `utf8mb4_general_ci`) as it's the MySQL 8.0 default and supports a wider range of special characters, providing better internationalization support.

- **Multi-AZ Configuration**: Enabled for automated failover and improved availability, demonstrating production-ready design principles even in a test environment.

- **Backup Retention**: Configured a 7-day backup retention period (verified in main.yaml) to balance data protection with cost efficiency for the assessment. This timeframe provides sufficient recovery options while preventing unnecessary storage costs.

### Storage Configuration

- **S3 Lifecycle Policy**: Configured S3 objects to transition to Standard-IA after 90 days and deletion after 365 days for cost optimization. This approach balances accessibility with cost-efficiency for demonstration purposes.

- **S3 Bucket Permissions**: Granted full access (get, put, delete, and list) to the EC2 IAM Role for flexibility in the demonstration environment. In production, more restrictive permissions following the principle of least privilege would be appropriate.

- **Versioning and Encryption**: Enabled S3 bucket versioning and AES-256 encryption for data protection, demonstrating security best practices.

### Security Configuration

- **Load Balancer Choice**: Selected Application Load Balancer rather than Network Load Balancer due to its support for HTTP/HTTPS health checks, SSL termination capabilities, and potential for multiple target groups. This provides a more feature-rich entry point for the application while maintaining high availability.

- **Security Groups**: Configured in a layered approach:
  - ALB security group accepts traffic from the internet on ports 80, 443, and 8080
  - EC2 security group accepts traffic only from the ALB on application ports and SSH for testing
  - RDS security group accepts traffic only from the EC2 security group on port 3306

- **SSH Access**: Maintained open SSH access (0.0.0.0/0) for testing purposes. In a production environment, this would be restricted to specific IP ranges or VPN/bastion hosts.

- **IAM Roles and Policies**: Created with specific permissions for EC2 instances to access S3, CloudWatch, and Systems Manager. Followed the principle of least privilege while maintaining operational functionality. Used a single EC2 instance role with multiple attached policies to centralize access control and simplify permission management.

### Monitoring and Logging

- **CloudWatch Integration**: Configured a log group with 30-day retention to balance operational visibility with cost efficiency. The EC2 instance IAM role was granted specific CloudWatch permissions:
  - `cloudwatch:PutMetricData`, `cloudwatch:GetMetricStatistics`, `cloudwatch:ListMetrics`
  - `logs:CreateLogStream`, `logs:CreateLogGroup`, `logs:PutLogEvents`, `logs:DescribeLogStreams`

- **Test Connectivity Script**: Developed a comprehensive Python script to verify all infrastructure components:
  - Used the `requests` library for HTTP testing due to its simplicity and excellent documentation
  - Utilized `mysql.connector` for RDS connectivity testing, enabling verification of both connection and CRUD operations
  - Implemented `boto3` for S3 testing with appropriate error handling

## Implementation Challenges and Solutions

### Security Group Configuration

- Encountered an issue where adding the 8080 port to the EC2 security group inadvertently overwrote the port 80 setting. Solution was to add a separate ingress rule for port 80.

### Database Character Set Configuration

- Initially set collation server to UTF8, but discovered that the default server for UTF8 is `utf8_general_ci`. After further research, updated to UTF8MB4 (MySQL 8.0 default) which allows for a wider range of special characters:
  ```yaml
  character_set_server: utf8mb4
  collation_server: utf8mb4_general_ci
  ```

### Auto Scaling Policy Configuration

- Identified that the ScaleUpPolicy contained an additional parameter (`EstimatedInstanceWarmup`) not supported by SimpleScaling policy type. Removed this parameter to ensure compatibility.

### Load Balancer Health Checks

- The health check endpoint was failing despite the container running correctly. Investigation revealed two issues:
  1. No listener was configured on the ALB for port 8080 - added an additional listener
  2. The ALB security group needed to allow incoming traffic on port 8080 - updated security group rules

### EC2 User Data Execution

- Initially experienced a 502 bad gateway when accessing the application. Traced the issue to permissions for the external S3 bucket storing the user-data script being incorrectly mapped. This prevented the script from running and consequently Docker was never set up.

## Testing Methodology

Testing after deployment follows a systematic approach:

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
   The `test-connectivity.py` script automates validation of all components:
   ***Note***: this script is copied into the system PATH during setup, and set to executable
   ```bash
   # Run after SSH into EC2 instance
    test-connectivity.py <alb_dns_name> <rds_endpoint> <s3_bucket> <db_password>
   ```

## Production Considerations

For adaptation to a production environment, several enhancements would be recommended:

1. **Web Application Firewall (WAF)**: Though listed as optional in the assessment, a WAF would be essential in production to protect against common web exploits and attacks. This was omitted from the current implementation to prioritize demonstrating high availability and data retention features within the time constraints.

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

These considerations would elevate the demonstration architecture to a production-ready solution with improved security, scalability, and operational efficiency.