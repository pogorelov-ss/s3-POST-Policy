from datetime import datetime, timedelta
from base64 import b64encode
from json import dumps
import hmac
import hashlib


class S3Policy:
    """
    Generate s3 post policy and sign it
    """

    def __init__(self, bucket, key_prefix, access_key, content_max_size=20971520, acl='public-read', time_frame=240,
                 content_type='image/png'):
        """

        :param bucket: s3 bucket name
        :param key_prefix: full s3 key or key prefix
        :param access_key: s3 access key
        :param content_max_size: max file size
        :param acl: Canned ACL from this doc http://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html
        :param time_frame: policy expiration in seconds
        :param content_type: file content type
        """             
        self.bucket_url = 'https://{}.s3.amazonaws.com'.format(bucket)
        self.bucket = bucket
        self.acl = acl
        self.access_key = access_key
        self.key_prefix = key_prefix
        self.time_frame = time_frame
        self.content_max_size = content_max_size
        self.expiration = None
        self.policy = None
        self.content_type = content_type

    def generate_policy_str(self):
        expiration = (datetime.utcnow() + timedelta(seconds=self.time_frame)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        policy_document = {
            'expiration': expiration,
            'conditions': [
                {'bucket': self.bucket},
                ['starts-with', '$key', self.key_prefix],
                {'acl': self.acl},
                {'success_action_status': '201'},
                ['starts-with', '$Content-Type', ''],
                ['content-length-range', 0, self.content_max_size]
            ]
        }
        self.expiration = expiration
        self.policy = b64encode((dumps(policy_document).replace('\n', '').replace('\r', '')).encode('ascii'))

    def signed(self, secret_key):
        """
        Sign generated policy
        :param secret_key: aws secret key
        :return: dict with policy and extra data useful for creating post request
        """
        def to_unicode(s):
            return s if type(s) == str else s.decode('unicode_escape')
        self.generate_policy_str()
        signed = b64encode(hmac.new(str.encode(to_unicode(secret_key)), self.policy, hashlib.sha1).digest()).decode(
            'unicode_escape')
        return {
            'extra':
                {
                    'bucket_url': self.bucket_url,
                    'key_prefix': to_unicode(self.key_prefix),
                    'expiration': to_unicode(self.expiration),
                },
            'policy':
                {
                    'policy': to_unicode(self.policy),
                    'signature': signed,
                    'AWSAccessKeyId': to_unicode(self.access_key),
                    'acl': self.acl,
                    'Content-Type': self.content_type,
                    'success_action_status': '201',
                    'key': to_unicode(self.key_prefix),
                }
        }
