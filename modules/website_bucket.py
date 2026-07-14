from constructs import Construct
from cdktf_cdktf_provider_google.storage_bucket import StorageBucket
from cdktf_cdktf_provider_google.storage_bucket_object import StorageBucketObject
from cdktf_cdktf_provider_google.storage_object_access_control import StorageObjectAccessControl

class WebsiteBucket(Construct):
    def __init__(self,scope:Construct,id:str,bucket_name:str,source_file:str):
        super().__init__(scope,id)


        bucket=StorageBucket(
            self,
            "bucket",
            name=bucket_name,
            location="US"
        )

        website_file=StorageBucketObject(
            self,
            "websitefile",
            name="index.html",
            bucket=bucket.name,
            source=source_file)
        
        StorageObjectAccessControl(
            self,
            "publicAccess",
            bucket=bucket.name,
            object=website_file.name,
            role="READER",
            entity="allUsers"
        )