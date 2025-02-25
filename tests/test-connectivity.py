#!/usr/bin/env python3
"""Test connectivity between EC2, RDS, and S3 components."""

import argparse
import os
import sys
import time
import urllib.request
import boto3
import mysql.connector
from botocore.exceptions import ClientError

# ANSI color codes
GREEN, RED, BLUE, BOLD, ENDC = '\033[92m', '\033[91m', '\033[94m', '\033[1m', '\033[0m'

def log(message, status=None):
    """Print formatted message based on status."""
    prefix = {
        "success": f"{GREEN}✓",
        "error": f"{RED}✗",
        "header": f"{BLUE}{BOLD}"
    }.get(status, "")
    suffix = ENDC if status else ""
    print(f"{prefix} {message}{suffix}")

def test_http_endpoint(url, name):
    """Test HTTP endpoint connectivity."""
    try:
        response = urllib.request.urlopen(url, timeout=10)
        if response.getcode() == 200:
            log(f"{name} is accessible at {url}", "success")
            return True
        else:
            log(f"{name} returned status code {response.getcode()}", "error")
            return False
    except Exception as e:
        log(f"Error connecting to {name}: {e}", "error")
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
        log(f"RDS connection successful (MySQL version: {version[0]})", "success")
        
        # Create test table if not exists
        cursor.execute("SHOW TABLES LIKE 'test_connectivity'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE test_connectivity (
                id INT AUTO_INCREMENT PRIMARY KEY,
                test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                test_result VARCHAR(255)
            )""")
            log("Created test_connectivity table", "success")
        
        # Insert test record
        cursor.execute("INSERT INTO test_connectivity (test_result) VALUES ('Test successful')")
        conn.commit()
        log("Successfully inserted test record into database", "success")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        log(f"RDS connection failed: {e}", "error")
        return False

def test_s3_connectivity(s3_bucket):
    """Test S3 bucket connectivity by uploading a file."""
    try:
        s3 = boto3.client('s3')
        test_file_name = f"test-file-{int(time.time())}.txt"
        
        # Create, upload, verify, and cleanup test file
        with open(test_file_name, 'w') as f:
            f.write(f"Test file created at {time.ctime()}")
        
        s3.upload_file(test_file_name, s3_bucket, test_file_name)
        log(f"Uploaded {test_file_name} to S3 bucket {s3_bucket}", "success")
        
        response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=test_file_name)
        if 'Contents' in response:
            log("Verified file exists in S3 bucket", "success")
        
        s3.delete_object(Bucket=s3_bucket, Key=test_file_name)
        os.remove(test_file_name)
        log("Deleted test file from S3 bucket", "success")
        
        return True
    except Exception as e:
        log(f"S3 operation failed: {e}", "error")
        return False

def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description='Test AWS infrastructure connectivity')
    parser.add_argument('alb_dns_name', help='DNS name of the ALB')
    parser.add_argument('rds_endpoint', help='Endpoint of the RDS instance')
    parser.add_argument('s3_bucket', help='Name of the S3 bucket')
    parser.add_argument('db_password', help='Password for the database')
    parser.add_argument('--db-user', default='admin', help='Database username (default: admin)')
    parser.add_argument('--db-name', default='applicationdb', help='Database name (default: applicationdb)')
    
    args = parser.parse_args()
    
    log("\n\n=== Testing Infrastructure ===", "header")
    
    # Run all tests
    tests = [
        ("Test 1: Checking ALB connectivity", 
         test_http_endpoint, [f"http://{args.alb_dns_name}", "ALB"]),
        
        ("Test 2: Checking health endpoint", 
         test_http_endpoint, [f"http://{args.alb_dns_name}:8080/index.html", "Health endpoint"]),
        
        ("Test 3: Testing RDS connectivity", 
         test_rds_connectivity, [args.rds_endpoint, args.db_user, args.db_password, args.db_name]),
        
        ("Test 4: Testing S3 connectivity", 
         test_s3_connectivity, [args.s3_bucket])
    ]
    
    results = []
    for title, func, params in tests:
        log(title, "header")
        results.append(func(*params))
    
    # Print summary
    log("=== Test Summary ===", "header")
    print(f"ALB Endpoint: {args.alb_dns_name}")
    print(f"RDS Endpoint: {args.rds_endpoint}")
    print(f"S3 Bucket: {args.s3_bucket}")
    
    passed = sum(results)
    total = len(results)
    
    status = "success" if passed == total else "error"
    message = f"All tests passed! ({passed}/{total})" if passed == total else f"Some tests failed. ({passed}/{total} passed)"
    log(message, status)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())