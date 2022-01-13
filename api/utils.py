import boto3
import uuid
from ownroom.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME

PREFIX = 'files/'


class S3Client:
    def __init__(self, access_key, secret_key, bucket_name):
        self.s3client = boto3.client(
            's3',
            aws_access_key_id = access_key,
            aws_secret_access_key = secret_key
        )
        self.bucket_name = bucket_name

    def upload(self, file):
        try:
            fileId = str(uuid.uuid4())
            extra_args = {'ContentType': file.content_type}
            final_path = PREFIX + fileId
            self.s3client.upload_fileobj(
                file,
                self.bucket_name,
                final_path,
                ExtraArgs = extra_args
            )
            return final_path
        except:
            return None


s3client = S3Client(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME)