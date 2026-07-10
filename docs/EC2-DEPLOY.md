# Deploying CloudOptimizer to a Single EC2 Instance

This is an alternative to the serverless deploy (`scripts/deploy.sh`, which
uses Lambda + EventBridge). Use this if you want everything — API, dashboard,
and the nightly scan — running on one EC2 box instead, e.g. for a portfolio
demo where a persistent, sshable instance is easier to show off than Lambda.

**What stays the same:** DynamoDB (findings storage) and SNS (alerts) are
still real AWS services — you provision those with Terraform as before.
**What changes:** instead of a Lambda + EventBridge rule running the scan,
an EC2 instance runs the API (via systemd + nginx) and the scan (via cron).

---

## 1. Provision DynamoDB + SNS (keep using Terraform for these)

You don't need the Lambda or EventBridge modules for this path. From
`terraform/environments/dev/main.tf`, comment out (or `-target` around) the
`lambda` and `eventbridge` modules, then apply the rest:

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars   # fill in alert_email, region
terraform init
terraform apply \
  -target=module.dynamodb \
  -target=module.sns \
  -target=module.s3_reports
terraform output   # note the DynamoDB table names and SNS topic ARN
```

## 2. Launch the EC2 instance

Console or CLI, either works. Minimum spec: `t3.small` (2GB RAM is enough
for FastAPI + nginx + a Python scan process; go `t3.medium` if you also plan
to build the frontend on the box rather than uploading a pre-built `dist/`).

```bash
aws ec2 run-instances \
  --image-id ami-0f918f7e67a3323f0 \
  --instance-type t3.small \
  --key-name your-keypair \
  --security-group-ids sg-xxxxxxxx \
  --subnet-id subnet-xxxxxxxx \
  --iam-instance-profile Name=cloudoptimizer-ec2-profile \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=cloudoptimizer}]'
```
(AMI ID above is an example Ubuntu 22.04 LTS in `ap-south-1` — check
[the current one](https://cloud-images.ubuntu.com/locator/ec2/) for your region.)

Security group needs:
| Port | Source | Purpose |
|---|---|---|
| 22 | your IP only | SSH |
| 80 | 0.0.0.0/0 (or your IP) | dashboard + API via nginx |

## 3. Create the IAM instance role

The instance needs the same least-privilege permissions as the Lambda role
did — read-only resource discovery, scoped DynamoDB read/write, SNS publish,
and the same safe-remediation actions the API's `/optimize` endpoint allows.
Policy documents are provided:

```bash
aws iam create-role \
  --role-name cloudoptimizer-ec2-role \
  --assume-role-policy-document file://deploy/ec2/trust-policy.json

aws iam put-role-policy \
  --role-name cloudoptimizer-ec2-role \
  --policy-name cloudoptimizer-scan-policy \
  --policy-document file://deploy/ec2/instance-role-policy.json

aws iam create-instance-profile --instance-profile-name cloudoptimizer-ec2-profile
aws iam add-role-to-instance-profile \
  --instance-profile-name cloudoptimizer-ec2-profile \
  --role-name cloudoptimizer-ec2-role
```
Attach `cloudoptimizer-ec2-profile` to the instance (either at launch, as
above, or after with `aws ec2 associate-iam-instance-profile`).

## 4. Upload the code

```bash
# From your local machine, with the repo at ./cloudoptimizer
scp -r -i your-keypair.pem cloudoptimizer ubuntu@<instance-ip>:/tmp/cloudoptimizer
ssh -i your-keypair.pem ubuntu@<instance-ip>
sudo mv /tmp/cloudoptimizer /opt/cloudoptimizer
```
(Or `git clone` your repo directly onto the instance instead of `scp`.)

## 5. Run the bootstrap script

```bash
cd /opt/cloudoptimizer
sudo bash deploy/ec2/bootstrap.sh
```

This installs Python 3.12 / Node 20 / nginx, sets up a venv, builds the
frontend, installs the API as a systemd service (`cloudoptimizer-api`,
listening on `127.0.0.1:8000`), configures nginx to serve the frontend on
port 80 and reverse-proxy `/api/*` to the API, and adds a cron job that
runs the scanner nightly at 02:00 UTC.

Before running it, edit `deploy/ec2/cloudoptimizer-api.service` if your
DynamoDB table names differ from the defaults (`cloudoptimizer-resources-dev`
/ `cloudoptimizer-resources-dev-scan-history`) or if you want SNS alerts —
set `SNS_TOPIC_ARN` to the ARN from the Terraform output in step 1.

## 6. Verify

```bash
curl http://localhost/api/health          # {"status":"ok"}
curl http://<instance-public-ip>/         # dashboard HTML
```
Open `http://<instance-public-ip>/` in a browser — you should see the
CloudOptimizer dashboard. Click **Run Scan Now**: since no
`SCANNER_LAMBDA_NAME` is configured, the API runs the scan in-process on a
background thread (see `trigger_scan()` in `backend/api/main.py`) instead of
invoking a Lambda, so this works with zero Lambda involved.

## 7. Useful commands on the instance

```bash
sudo systemctl status cloudoptimizer-api      # API service status
sudo journalctl -u cloudoptimizer-api -f       # API logs, live
sudo tail -f /var/log/cloudoptimizer-scan.log  # cron scan output
sudo -u cloudoptimizer /opt/cloudoptimizer/backend/.venv/bin/python \
  /opt/cloudoptimizer/deploy/ec2/run_scan.py    # trigger a scan manually
```

## Notes / trade-offs vs. the serverless deploy

- **Cost**: a `t3.small` running 24/7 costs more per month than a Lambda that
  only runs for ~30 seconds a day. This path is about demo convenience, not
  cost — use the serverless deploy (`scripts/deploy.sh`) for a real always-on
  account monitor.
- **No auto-scaling / no HA**: one instance, one point of failure. Fine for a
  portfolio demo; for production put it behind an ALB + Auto Scaling Group,
  or just use the Lambda path.
- **HTTPS**: this guide serves plain HTTP on port 80. Put an ACM certificate
  behind an ALB, or run `certbot` for nginx, before sharing the URL widely.
