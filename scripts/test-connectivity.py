#!/usr/bin/env python3
"""Test connectivity between EC2, RDS, and S3 components."""

import argparse
import os
import sys
import time
import requests
import boto3
import mysql.connector
import warnings
import boto3.exceptions

# Suppressing warnings from Boto3. AWS default python verion = 3.7, not 3.8
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=boto3.exceptions.PythonDeprecationWarning)


# color codes
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'


# Simple output formatting
def log(message, success=None):
    """Print formatted message."""
    if success is True:
        prefix = f"{GREEN}\u2713{RESET}"
    elif success is False:
        prefix = f"{RED}\u2717{RESET}"
    else:
        prefix = ""
    print(f"{prefix} {message}")



def test_http_endpoint(url, name):
    """Test HTTP endpoint connectivity using requests."""
    try:
        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()  # Raises exception for 4XX/5XX status codes
        log(f"{name} is accessible at {url}", True)
        return True
    except requests.exceptions.HTTPError as e:
        log(f"{name} returned error status code: {e}", False)
        return False
    except requests.exceptions.RequestException as e:
        log(f"Error connecting to {name}: {e}", False)
        return False



def test_rds_connectivity(rds_endpoint, db_user, db_password, db_name):
    """Test RDS database connection."""
    try:
        conn = mysql.connector.connect(
            host=rds_endpoint, user=db_user, password=db_password, database=db_name
        )
        cursor = conn.cursor()
        
        # Check MySQL version
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        log(f"RDS connection successful (MySQL version: {version[0]})", True)
        
        # Create test table and insert record
        cursor.execute("SHOW TABLES LIKE 'test_connectivity'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE test_connectivity (
                id INT AUTO_INCREMENT PRIMARY KEY,
                test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                test_result VARCHAR(255)
            )""")
        
        cursor.execute("INSERT INTO test_connectivity (test_result) VALUES ('Test successful')")
        conn.commit()
        log("Successfully wrote to database", True)
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        log(f"RDS connection failed: {e}", False)
        return False



def test_s3_connectivity(s3_bucket):
    """Test S3 bucket connectivity using put_object."""
    try:
        s3 = boto3.client('s3')
        test_key = f"test-object-{int(time.time())}.txt"
        
        s3.put_object(
            Bucket=s3_bucket,
            Key=test_key,
            Body="Test content",
            ContentType="text/plain"
        )
        
        s3.delete_object(Bucket=s3_bucket, Key=test_key)
        log(f"S3 bucket {s3_bucket} test successful", True)
        
        return True
    except Exception as e:
        log(f"S3 operation failed: {e}", False)
        return False



def main():
    parser = argparse.ArgumentParser(description='Test infrastructure connectivity')
    parser.add_argument('alb_dns_name', help='DNS name of the ALB')
    parser.add_argument('rds_endpoint', help='Endpoint of the RDS instance')
    parser.add_argument('s3_bucket', help='Name of the S3 bucket')
    parser.add_argument('db_password', help='Password for the DB')
    parser.add_argument('--db-user', default='admin', help='Database username (default: admin)')
    parser.add_argument('--db-name', default='applicationdb', help='Database name (default: applicationdb)')
    
    args = parser.parse_args()
    
    log("\n\n=== Running Tests ===\n---------------------")
    
    # Run all tests
    all_passed = True
    
    log("Checking ALB connectivity")
    if not test_http_endpoint(f"http://{args.alb_dns_name}", "ALB"):
        all_passed = False
        
    log("\nChecking health endpoint")
    if not test_http_endpoint(f"http://{args.alb_dns_name}:8080/index.html", "Health endpoint"):
        all_passed = False
        
    log("\nTesting RDS connectivity")
    if not test_rds_connectivity(args.rds_endpoint, args.db_user, args.db_password, args.db_name):
        all_passed = False
        
    log("\nTesting S3 connectivity")
    if not test_s3_connectivity(args.s3_bucket):
        all_passed = False
    
    # Print summary
    log("\n\n=== Test Summary ===\n--------------------")
    log(f"Tests completed: {GREEN+'All tests passed'+RESET if all_passed else RED+'Some tests failed'+RESET}\n", all_passed)



if __name__ == "__main__":
    sys.exit(main())