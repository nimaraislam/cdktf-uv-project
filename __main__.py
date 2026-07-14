"""Pulumi program: three public GCS website buckets."""

from modules.website_bucket import WebsiteBucket

# Number of website buckets to provision.
BUCKET_COUNT = 3

# HTML file served from each bucket, relative to the project root.
SOURCE_FILE = "website/index.html"

for i in range(1, BUCKET_COUNT + 1):
    WebsiteBucket(
        f"website-{i}",
        bucket_name=f"cdktf-website-{i:03d}-nimara",
        source_file=SOURCE_FILE,
    )
