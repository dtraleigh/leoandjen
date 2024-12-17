import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from django.core.management.base import BaseCommand
import environ
from pathlib import Path


class Command(BaseCommand):
    help = "Check S3 connection and verify media storage"

    def handle(self, *args, **options):
        try:
            # Set up environ to read .env
            BASE_DIR = Path(__file__).resolve().parent.parent.parent
            env = environ.Env()
            environ.Env.read_env(BASE_DIR / ".env")

            # Extract AWS configuration from .env
            bucket_name = env("AWS_STORAGE_BUCKET_NAME", default=None)
            access_key = env("AWS_ACCESS_KEY_ID", default=None)
            secret_key = env("AWS_SECRET_ACCESS_KEY", default=None)
            region_name = env("AWS_S3_REGION_NAME", default="us-east-1")

            if not all([bucket_name, access_key, secret_key]):
                raise KeyError(
                    "Missing one or more required AWS environment variables: "
                    "'AWS_STORAGE_BUCKET_NAME', 'AWS_ACCESS_KEY_ID', or 'AWS_SECRET_ACCESS_KEY'."
                )

            # Create S3 client
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region_name,
            )

            # Verify bucket access
            self.stdout.write(f"Verifying access to bucket: {bucket_name}")
            s3_client.head_bucket(Bucket=bucket_name)
            self.stdout.write(f"Access to bucket '{bucket_name}' verified.")

            # Upload a test file
            test_key = "s3_test_file.txt"
            test_content = "This is a test file for S3 connectivity."
            s3_client.put_object(Bucket=bucket_name, Key=test_key, Body=test_content)
            self.stdout.write(f"Test file '{test_key}' uploaded successfully.")

            # Retrieve the test file
            response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
            retrieved_content = response["Body"].read().decode("utf-8")
            assert retrieved_content == test_content, "Content mismatch!"

            self.stdout.write("Test file retrieved and verified successfully.")

            # Clean up: Delete the test file
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            self.stdout.write(f"Test file '{test_key}' deleted successfully.")

            self.stdout.write("S3 connection test passed.")

        except KeyError as e:
            self.stderr.write(f"Missing configuration: {e}")
        except (NoCredentialsError, PartialCredentialsError) as e:
            self.stderr.write(f"Credential error: {e}")
        except ClientError as e:
            self.stderr.write(f"AWS Client error: {e.response['Error']['Message']}")
        except Exception as e:
            self.stderr.write(f"An unexpected error occurred: {e}")
