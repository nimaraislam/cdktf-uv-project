"""Pulumi program: three public GCS website buckets.

During the initial migration from CDKTF, ``importing=True`` instructs
``WebsiteBucket`` to import the already-deployed GCS bucket and object ACL
into Pulumi state.  After a successful ``pulumi up``, remove the
``importing=True`` flag so subsequent runs simply track the resources normally.
"""

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
        importing=True,  # Remove after the initial migration 'pulumi up' succeeds.
    )
