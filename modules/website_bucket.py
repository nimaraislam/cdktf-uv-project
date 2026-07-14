"""Pulumi ComponentResource for a public GCS website bucket."""

import pulumi
import pulumi_gcp as gcp


class WebsiteBucket(pulumi.ComponentResource):
    """A GCS bucket configured for static website hosting with public read access.

    Creates a bucket, uploads an index.html file, and grants public read access
    to the uploaded object via a fine-grained object ACL.

    Args:
        name: The Pulumi logical name for this component.
        bucket_name: The GCS bucket name (used as-is; no auto-naming).
        source_file: Local path to the HTML file to upload as index.html.
        opts: Standard Pulumi resource options.
    """

    bucket: gcp.storage.Bucket
    website_file: gcp.storage.BucketObject
    public_access: gcp.storage.ObjectAccessControl

    def __init__(
        self,
        name: str,
        bucket_name: str,
        source_file: str,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("custom:storage:WebsiteBucket", name, {}, opts)

        # Bucket: the name is set explicitly to match the already-deployed resource.
        # Fine-grained ACLs require uniform_bucket_level_access to be disabled.
        self.bucket = gcp.storage.Bucket(
            f"{name}-bucket",
            name=bucket_name,
            location="US",
            uniform_bucket_level_access=False,
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Re-upload index.html on every run if the content changes.
        self.website_file = gcp.storage.BucketObject(
            f"{name}-index-html",
            name="index.html",
            bucket=self.bucket.name,
            source=pulumi.FileAsset(source_file),
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Grant public read access to the object.
        self.public_access = gcp.storage.ObjectAccessControl(
            f"{name}-public-access",
            bucket=self.bucket.name,
            object=self.website_file.output_name,
            role="READER",
            entity="allUsers",
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.register_outputs({"bucket_name": self.bucket.name})
