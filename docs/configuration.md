

resources:
    Drupal docker page
        https://hub.docker.com/_/drupal
    Drupal's Docker image docs: https://www.drupal.org/docs/develop/development-tools/docker
    Docker Installation on Amazon Linux 2:
    AWS Documentation: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/create-container-image.html
    Docker's official docs: https://docs.docker.com/engine/install/

    Docker Compose Installation:
    Official documentation: https://docs.docker.com/compose/install/

    Drupal S3 Configuration:
    S3 File System module: https://www.drupal.org/project/s3fs
    AWS S3 module: https://www.drupal.org/project/s3

    Drupal Database Configuration:
    Database configuration guide: https://www.drupal.org/docs/installing-drupal/step-3-create-a-database
    RDS connection guide: https://aws.amazon.com/blogs/database/deploying-drupal-on-amazon-rds/


I chose yeasy/simple-web docker image because it already integrates the source and destination communication check by returning IP info automatically.


ec2-user chosen because it's the default Linux AMI user

Single cloud formation stack chosen instead of nested stacks because of relative simplicity of project, and ease of maintenance with single stack. 


Chose default AWS VPC config for simplicity and time saving just for demonstartion. In a prod environment, custom VPC with private subnets, and network segregation would be preffered.  


S3 transitioning to Standard IA adter 90 days, and deletion after 365 for storage cost savings. Would likely change to accomidate goals with prod workflow.

Gave full access to EC2 IAM Role to S3 bucket for get, put, delete and list. For flexibility sake for demonstration.

Chose db.t3.micro for RDS because it's a budget option, but capable of ecryption at rest.
gp2 storage type listed as "best suited for development / testing environments"

Chose to keep open SSH access to to EC2 for testing purposes. Would otherwise restrict to HQ CIDR / IP

Chose port 8080 for health probe to test HTTP protocol, but 8080 is typically used for testing / dev purposes. LB traffic still comes in over 80.


after testing the networking between resources, it was time to add complexity to the initially simple user-data script. 
Found Yeasy/simple-web docker container. configured the docker image to use this. updated template to use the healthport 8080 to match the image.






Issues encountered:
    - Tags not application to Launch Template:
        Removed tags
    - Collation server was set to utf8. 
        Found default server for utf8 is utf8_general_ci
        Researching, I learned UTF8mb4 is MySQL 8.0 default, and allows special characters. Decided to update for futureproofing:
            character_set_server: utf8mb4
            collation_server: utf8mb4_0900_ai_ci
    - ScaleUpPolicy had an additional parameter not accepted by SimpleScaling policy.
        Removed EstimatedInstanceWarmup parameter





Testing log:
    Deployment worked with all resources, IAM policies, and Gateways for the first time.    02-25-25
    Tested EC2 > S3 connection
        from ec2 instance:
        Created test.txt and copied to S3. worked.
    Curled App Load Balancer health
        502 bad gateway
        Permissions to external bucket storing user-data script were incorrectly mapped. script never ran, so Docker was never set up, and /health endpoint never set up.
    After imlementing the testing script, it passes both RDS, and s3 connectivity, but fails both HTTP tests to ALB, and health enpoint.
        When adding the 8080 port to the EC2 security group ingress settings, I mistakingly overwrote the port 80 setting. 🙃
        Added a new section for port 80
    Health enpoint still failing test.
        The health check container is running, and returning OK locally
        There is no listener on the ALB for port 8080.. Added additional listener.
        Added an allowance into the ALB security group for this port as well.










Testing after deployment:
s3://healthmine-docker-assessment-bucket/test-connectivity.py

SSH into ec2 instance, run: (arguments are outputs of the stack deployment)
    aws s3 cp s3://healthmine-docker-assessment-bucket/test-connectivity.py /tmp/test-connectivity.py
    sudo chmod +x /tmp/test-connectivity.py
    /tmp/test-connectivity.py <alb_dns_name> <rds_endpoint> <s3_bucket> <db_password>