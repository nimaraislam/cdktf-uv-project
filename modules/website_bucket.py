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
        importing: When True, imports the existing bucket and ACL from GCP
                   rather than creating new ones. Set to False after the initial
                   migration 'pulumi up' has completed successfully.
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
        importing: bool = False,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("custom:storage:WebsiteBucket", name, {}, opts)

        # Bucket: import the existing GCS bucket during migration, otherwise create.
        # The name is set explicitly to match the already-deployed resource.
        # Fine-grained ACLs require uniform_bucket_level_access to be disabled.
        self.bucket = gcp.storage.Bucket(
            f"{name}-bucket",
            name=bucket_name,
            location="US",
            uniform_bucket_level_access=False,
            opts=pulumi.ResourceOptions(
                parent=self,
                import_=bucket_name if importing else None,
            ),
        )

        # BucketObject does not support import. On the first 'pulumi up' this
        # re-uploads index.html; since the content is identical GCS treats it as
        # an in-place overwrite with no observable impact on serving.
        self.website_file = gcp.storage.BucketObject(
            f"{name}-index-html",
            name="index.html",
            bucket=self.bucket.name,
            source=pulumi.FileAsset(source_file),
            opts=pulumi.ResourceOptions(parent=self),
        )

        # ACL: import the existing allUsers READER grant during migration.
        # Import ID format: {bucket}/{object}/{entity}
        self.public_access = gcp.storage.ObjectAccessControl(
            f"{name}-public-access",
            bucket=self.bucket.name,
            object=self.website_file.output_name,
            role="READER",
            entity="allUsers",
            opts=pulumi.ResourceOptions(
                parent=self,
                import_=(
                    f"{bucket_name}/index.html/allUsers" if importing else None
                ),
            ),
        )

        self.register_outputs({"bucket_name": self.bucket.name})
