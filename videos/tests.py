from django.test import TestCase
from django.conf import settings
import boto3, os
from botocore.exceptions import ClientError
from unittest import skipUnless

@skipUnless(os.environ.get("RUN_SERVER_TESTS") == "1", "Skipping test unless RUN_SERVER_TESTS=1 is set")
class S3ConnectionTest(TestCase):
    def test_s3_connection(self):
        bucket_name = settings.STORAGES["default"]["OPTIONS"]["bucket_name"]
        region_name = settings.STORAGES["default"]["OPTIONS"]["region_name"]

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.STORAGES["default"]["OPTIONS"]["access_key"],
            aws_secret_access_key=settings.STORAGES["default"]["OPTIONS"]["secret_key"],
            region_name=region_name,
        )

        try:
            # Verify bucket access
            s3_client.head_bucket(Bucket=bucket_name)

            # Upload a test file
            test_key = "s3_test_file.txt"
            test_content = "This is a test file for S3 connectivity."
            s3_client.put_object(Bucket=bucket_name, Key=test_key, Body=test_content)

            # Retrieve and verify content
            response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
            retrieved_content = response["Body"].read().decode("utf-8")
            self.assertEqual(retrieved_content, test_content)

            # Clean up
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        except ClientError as e:
            self.fail(f"AWS Client error: {e.response['Error']['Message']}")
        except Exception as e:
            self.fail(f"Unexpected error: {e}")
