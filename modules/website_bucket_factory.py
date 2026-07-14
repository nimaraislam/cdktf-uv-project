from constructs import Construct
from modules.website_bucket import WebsiteBucket

class WebsiteBucketFactory:
    def __init__(self, scope: Construct):
        self.scope = scope

    def create(self, count, source_file):
        buckets = []

        for i in range(1,count+1):
            buckets.append(
                WebsiteBucket(
                    self.scope,
                    f"website-{i}",
                    bucket_name=f"cdktf-website-{i:03d}-nimara",
                    source_file=source_file
                )
            )

        return buckets