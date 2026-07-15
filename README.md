# cdktf-uv-project
# CDKTF to Pulumi migration runbook

This guide records how this repository was migrated from CDK for Terraform
(CDKTF) to Pulumi, and how it authenticates to Google Cloud without a
service-account JSON key.

## 1. What this project manages

The project manages three public GCS static-website buckets in the Google Cloud
project `terraform-lab-nimara`.

| Pulumi component | GCS bucket |
| --- | --- |
| `website-1` | `cdktf-website-001-nimara` |
| `website-2` | `cdktf-website-002-nimara` |
| `website-3` | `cdktf-website-003-nimara` |

For every bucket, Pulumi manages the bucket, `website/index.html` uploaded as
`index.html`, and a public-read `allUsers` object ACL. Public read means
anyone on the internet can read the file; never use this for private content.

## 2. Names used by this setup

| Item | Value |
| --- | --- |
| Pulumi organization | `nimara` |
| Pulumi project | `cdktf-uv-project` |
| Pulumi stack | `dev` |
| Pulumi ESC environment | `nimara/cdktf-uv-project/dev` |
| GCP project ID | `terraform-lab-nimara` |
| GCP project number | `168056669287` |
| Workload Identity Pool ID | `pulumi-esc` |
| OIDC provider ID | `pulumi-esc` |
| GCP service account | `pulumi-esc@terraform-lab-nimara.iam.gserviceaccount.com` |

## 3. What changed in the migration

The CDKTF program was removed:

- `main.py` and `cdktf.json`
- `modules/website_bucket_factory.py`
- Generated CDKTF output and local Terraform state

The Pulumi program now uses:

- `Pulumi.yaml`: Pulumi Python project configuration using `uv`.
- `Pulumi.dev.yaml`: selects ESC environment `cdktf-uv-project/dev` and
  GCP project `terraform-lab-nimara`.
- `__main__.py`: program entry point; creates the three website components.
- `modules/website_bucket.py`: bucket, object upload, and public ACL.
- `pyproject.toml` and `uv.lock`: `pulumi` and `pulumi-gcp` dependencies.

`.gitignore` now excludes generated CDKTF output, service-account key files,
and Terraform state:

```gitignore
cdktf.out/
terraform-lab-*.json
*.tfstate
*.tfstate.*
```

Never commit a service-account JSON key. The Pulumi program uses short-lived
credentials from ESC and GCP Workload Identity Federation instead. Revoke the
old JSON key in Google Cloud if that has not already been done.

## 4. How GCP authentication works

```text
Pulumi ESC environment
        │ short-lived OIDC token (OpenID Connect)
        ▼
GCP Workload Identity Pool: pulumi-esc
        │ impersonates
        ▼
GCP service account: pulumi-esc
        │ Cloud Storage permissions
        ▼
GCS buckets
```

The OIDC token must match:

- Issuer: `https://api.pulumi.com/oidc`
- Audience: `gcp:nimara`
- Subject:

```text
pulumi:environments:pulumi.organization.login:nimara:currentEnvironment.name:cdktf-uv-project/dev
```

## 5. Configure Pulumi ESC (one time)

1. Sign in to [Pulumi Cloud](https://app.pulumi.com/) and select `nimara`.
2. Open **Environments** and create:
   - Project: `cdktf-uv-project`
   - Environment: `dev`
3. Save this environment definition:

```yaml
values:
  gcp:
    login:
      fn::open::gcp-login:
        project: 168056669287
        oidc:
          workloadPoolId: pulumi-esc
          providerId: pulumi-esc
          serviceAccount: pulumi-esc@terraform-lab-nimara.iam.gserviceaccount.com
          region: global
          subjectAttributes:
            - currentEnvironment.name

  environmentVariables:
    GOOGLE_CLOUD_PROJECT: ${gcp.login.project}
    GOOGLE_OAUTH_ACCESS_TOKEN: ${gcp.login.accessToken}
    CLOUDSDK_CORE_PROJECT: terraform-lab-nimara
    CLOUDSDK_AUTH_ACCESS_TOKEN: ${gcp.login.accessToken}
```

`subjectAttributes` makes the subject specific to this one environment.

## 6. Configure GCP Workload Identity Federation (one time)

In **Google Cloud Console → IAM & Admin → Workload Identity Federation**, open
the pool `pulumi-esc`, then its `pulumi-esc` OIDC provider.

| Provider setting | Required value |
| --- | --- |
| Issuer URL | `https://api.pulumi.com/oidc` |
| Allowed audience | `gcp:nimara` |
| Enabled | Yes |
| Attribute mapping | `google.subject` → `assertion.sub` |
| Attribute conditions | None |

Do not add an `attribute.org` mapping. The single `google.subject` mapping
is sufficient.

### Grant the service-account impersonation permission

The exact ESC subject needs `roles/iam.workloadIdentityUser` on the
`pulumi-esc` service account. In Google Cloud Console, open **Cloud Shell**
(`>_`) and run:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  pulumi-esc@terraform-lab-nimara.iam.gserviceaccount.com \
  --project=terraform-lab-nimara \
  --role=roles/iam.workloadIdentityUser \
  --member="principal://iam.googleapis.com/projects/168056669287/locations/global/workloadIdentityPools/pulumi-esc/subject/pulumi:environments:pulumi.organization.login:nimara:currentEnvironment.name:cdktf-uv-project/dev"
```

This command is safe to run again. A successful result says:

```text
Updated IAM policy for serviceAccount [...]
```

The `pulumi-esc` service account also needs access to the resources it
manages. For this learning project, **Storage Admin** is sufficient. In a
production project, grant the smallest appropriate role, preferably on the
specific buckets rather than the whole project.

## 7. Verify credentials

Install and log in to Pulumi if needed:

```bash
brew install pulumi/tap/pulumi
pulumi login
```

Check that ESC can issue credentials:

```bash
pulumi env open nimara/cdktf-uv-project/dev
```

This can print temporary tokens. Do not paste its output into GitHub, chat, or
source code.

If OIDC fails, check in this order:

1. The ESC environment name and `subjectAttributes`.
2. Provider audience `gcp:nimara`.
3. Provider mapping `google.subject = assertion.sub`.
4. No provider attribute condition.
5. The exact Workload Identity User binding in the Cloud Shell command above.

## 8. Run Pulumi locally

From the repository root:

```bash
uv sync
pulumi stack select dev
pulumi preview
```

Read the preview. A stable project should show no changes. To apply an expected
change:

```bash
pulumi up
```

For example, changing `website/index.html` and running `pulumi up` updates
the object in all three buckets.

## 9. How Neo performed this migration

Neo was started in Pulumi Cloud with the GitHub repository
`nimaraislam/cdktf-uv-project`. The correct migration choice was **Migrate
Terraform to Pulumi**, because CDKTF creates Terraform configuration and state.

Neo then:

1. Translated the CDKTF Python code into Pulumi Python.
2. Created PR #1.
3. Imported the three existing buckets into Pulumi state.
4. Re-uploaded the identical `index.html` files.
5. Found that the old deployment did not contain the public object ACLs.
6. Created the three missing ACLs.
7. Verified the `dev` stack has 13 resources: 1 stack, 3 components, 3
   buckets, 3 objects, and 3 ACLs.

After merging the PR, the local repository was updated with:

```bash
git pull --ff-only origin main
```

## 10. Daily workflow

1. Edit the Pulumi source or website files.
2. Run `uv sync` if dependencies changed.
3. Run `pulumi preview` and inspect every planned action.
4. Run `pulumi up` only when the plan is correct.
5. Commit source files only. Never commit keys, state, or generated output.

To update local code after a merged pull request:

```bash
git pull --ff-only origin main
```

If the command fails, preserve your local work and inspect the error before
using any overwrite or force command.

## 11. Official references

- [Pulumi ESC Google Cloud OIDC setup](https://www.pulumi.com/docs/esc/guides/configuring-oidc/gcp/)
- [Pulumi ESC GCP login provider](https://www.pulumi.com/docs/esc/providers/login/gcp-login/)
- [Google Cloud Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Pulumi CLI documentation](https://www.pulumi.com/docs/iac/cli/)

