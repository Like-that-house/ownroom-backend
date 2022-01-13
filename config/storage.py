from storages.backends.s3boto3 import S3Boto3Storage

__all__ = (
    'MediaStorage',
    'StaticStorage',
)

# for media
class MediaStorage(S3Boto3Storage):
    default_acl = 'public-read'
    location = 'media'


# for static
class StaticStorage(S3Boto3Storage):
    default_acl = 'public-read'
    location = 'static'