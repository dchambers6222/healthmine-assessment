# Healthmine Docker Web App - Architecture Document

## 1. Network Infrastructure

**VPC Configuration**
- VPC CIDR: `10.0.0.0/16` with DNS support and hostnames enabled
- **Public Subnet 1**: `10.0.1.0/24` in first AZ, auto-assigns public IPs
- **Public Subnet 2**: `10.0.2.0/24` in second AZ, auto-assigns public IPs
- **Internet Gateway** attached to VPC
- **Route Table**: Default route (`0.0.0.0/0`) to Internet Gateway, associated with both subnets

## 2. Security Components

**Security Groups**
- **ALB SG**: Inbound (80, 443, 8080) from internet; All outbound
- **EC2 SG**: Inbound (80, 8080) from ALB SG, (22) from internet; All outbound
- **RDS SG**: Inbound (3306) from EC2 SG only

**IAM Configuration**
- **EC2 Instance Role** with attached policies:
  - **S3 Access Policy**: CRUD operations on application S3 bucket
  - **External S3 Access Policy**: Read-only access to deployment scripts
  - **CloudWatch Access Policy**: Metrics and logging permissions
  - **SSM Managed Policy**: Systems Manager access
- **EC2 Instance Profile** links role to instances

## 3. Compute Layer

**Launch Template**
- **AMI**: Amazon Linux 2 (via SSM Parameter)
- **Instance Type**: Parameter-defined (default: `t3.micro`)
- **UserData Script Operations**:
  1. System updates and Docker installation
  2. Retrieves RDS/S3 info from CloudFormation outputs
  3. Launches two containers:
     - Main app (`yeasy/simple-web`) on port 80
     - Health check (nginx) on port 8080
  4. Sets up connectivity testing

**Auto Scaling Group**
- Spans both public subnets
- Min: 2, Max: 6, Desired: 2 instances
- **Scaling Policies**: Target tracking based on 50% CPU utilization with 300s warmup
- **Metrics Collection**: Detailed 1-minute metrics for instance counts and states

## 4. Load Balancing

**Application Load Balancer**
- Internet-facing, spans both public subnets
- **Target Group**: HTTP on port 80, health check on port 8080
- **Listeners**:
  - HTTP (80) → Target Group
  - Health (8080) → Target Group
  - HTTPS (443) → Target Group (created only when CertificateARN parameter is provided)

## 5. Database Layer

**RDS MySQL Instance**
- **Engine**: MySQL 8.0, `db.t3.micro`, 20GB GP2 storage
- **Multi-AZ**: Enabled with automated failover
- **Subnet Group**: Spans both public subnets
- **Parameter Group**: utf8mb4 character set and collation
- **Backup**: 7-day retention, 03:00-04:00 UTC window
- **Maintenance**: Monday 04:00-05:00 UTC
- **Network**: Not publicly accessible
- **Deletion Policy**: Creates snapshot on delete

## 6. Storage Resources

**Application S3 Bucket**
- Named using pattern: `${ProjectNamePrefix}-${EnvironmentType}-app-files-${AWS::AccountId}-${AWS::Region}`
- Versioning enabled, AES-256 encryption
- **Lifecycle Policy**: STANDARD_IA after 90 days, expire after 365
- **Access Control**: Public access blocked, restricted via bucket policy

**Dependencies S3 Bucket** (External)
- Contains `user-data.sh` and `test-connectivity.py`
- EC2 instances have read-only access

## 7. Monitoring and Testing

**CloudWatch Logs**
- Log group path: `/${ProjectNamePrefix}/${EnvironmentType}/app-logs`
- 30-day retention period

**CloudWatch Dashboard**
- Custom dashboard for EC2 instance monitoring: `${ProjectNamePrefix}-${EnvironmentType}-ec2-scaling-dashboard`
- Displays:
  - ASG CPU Utilization
  - ASG Instance Count

**Connectivity Testing Script**
- Tests all infrastructure components:
  - ALB HTTP access
  - Health endpoint
  - RDS read/write operations
  - S3 upload/delete operations

## 8. Docker Container Configuration

**Main Application Container**
- Image: Parameterized (default: `yeasy/simple-web:latest`)
- Port 80 exposed, environment variables for RDS endpoint and S3 bucket
- Configuration managed via docker run command in user-data.sh

**Health Check Container**
- Image: `nginx:alpine`
- Port 8080 exposed, static health file mounted
- Used by ALB to verify instance health

## 9. Stack Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| ProjectNamePrefix | healthmine | Resource naming prefix |
| EnvironmentType | assessment | Deployment environment |
| HTTPHealthPort | 8080 | Health check port |
| CertificateARN | - | Optional SSL cert ARN (HTTPS listener relies on this) |
| AMIID | Amazon Linux 2 | AMI ID |
| DBUsername | admin | RDS username |
| DBPassword | - | RDS password |
| InstanceType | t3.micro | EC2 size |
| ProjectDependenciesBucket | - | S3 bucket with scripts |

## 10. Stack Outputs

- **VpcId**: Created VPC ID
- **LoadBalancerDNSName**: ALB DNS name
- **RDSEndpoint**: Database connection string
- **S3BucketName**: App S3 bucket name
- **CloudWatchLogGroup**: Log group name

## 11. Architecture Principles Implemented

**High Availability**
- Multi-AZ for EC2 (via ASG) and RDS
- Load balancer spanning multiple AZs

**Scalability**
- Auto Scaling Group with scaling policies
- Separation of application and database tiers

**Security**
- Least-privilege security groups and IAM roles
- Encrypted storage, no public database access
- Optional HTTPS support

**Operational**
- Health checks, centralized logging
- Automated instance provisioning
- Infrastructure testing script

**Cost Optimization**
- Right-sized default instances
- S3 lifecycle policies
- Log retention limits

## 12. Improvement Considerations If Applied to Prod Workflow

**Security**
- Move RDS to private subnets
- Restrict SSH access to specific IP ranges
- Use Secrets Manager for credentials
- Implement VPC endpoints for AWS services

**Performance**
- Implement target tracking scaling policies
- Add RDS read replicas

**Monitoring**
- CloudWatch Alarms
- Implement more sophisticated health checks
- Add X-Ray for distributed tracing

**Deployment**
- Implement CI/CD pipeline
- Add CloudFormation validation
- Blue/green deployment capabilities