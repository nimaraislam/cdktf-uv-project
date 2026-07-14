#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from cdktf_cdktf_provider_google.provider import GoogleProvider 
from cdktf_cdktf_provider_google.storage_bucket import StorageBucket 
from cdktf_cdktf_provider_google.storage_bucket_object import StorageBucketObject 
from cdktf_cdktf_provider_google.storage_object_access_control import StorageObjectAccessControl
from modules.website_bucket import WebsiteBucket
from modules.website_bucket_factory import WebsiteBucketFactory


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # Configure Google Provider
        GoogleProvider( self,
                       "Google",
                       credentials=open("terraform-lab-nimara-ea0ad309859c.json").read(),
                       project="terraform-lab-nimara",
                       region="us-central1"
                       )
        
        '''
        WebsiteBucket(
            self,
            "myWebsite3",
            bucket_name="demo-website-by-nimara-2026_uv",
            source_file="/Users/nimaraislam-insighta/GitHub/cdktf-python-gcp/website/index.html"
                      )
        
        number_of_buckets = 3

        for i in range(1,number_of_buckets+1):
            WebsiteBucket(
                self,
                f"website-{i}",
                bucket_name=f"demo-website-{i:03d}-nimara",
                source_file="/Users/nimaraislam-insighta/GitHub/cdktf-python-gcp/website/index.html"
            )
        '''

        factory = WebsiteBucketFactory(self)
        factory.create(
                3,
                "/Users/nimaraislam-insighta/GitHub/cdktf-python-gcp/website/index.html"
                )

app = App()
MyStack(app, "pyhton-cdktf-gcp-prac")

app.synth()
