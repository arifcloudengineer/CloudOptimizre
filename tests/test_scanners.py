"""
Scanner tests using moto to mock AWS APIs -- no real AWS account or
credentials required. Each test creates the minimal fixture resources
needed to trigger (or deliberately avoid triggering) a finding.
"""
import boto3
import pytest
from moto import mock_aws

from scanner.ec2_scanner import scan_ec2
from scanner.ebs_scanner import scan_ebs
from scanner.eip_scanner import scan_eip
from scanner.s3_scanner import scan_s3


@mock_aws
def test_ec2_scan_flags_missing_tags():
    ec2 = boto3.client("ec2", region_name="ap-south-1")
    ec2.run_instances(ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t3.micro")

    findings = scan_ec2(region="ap-south-1")
    types = {f.resource_type for f in findings}
    assert "EC2:MissingTags" in types


@mock_aws
def test_ec2_scan_ignores_properly_tagged_instance_for_tag_check():
    ec2 = boto3.client("ec2", region_name="ap-south-1")
    resp = ec2.run_instances(
        ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t3.micro",
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Environment", "Value": "dev"}, {"Key": "Owner", "Value": "shaik"}],
        }],
    )
    instance_id = resp["Instances"][0]["InstanceId"]

    findings = scan_ec2(region="ap-south-1")
    tag_findings = [f for f in findings if f.resource_id == instance_id and f.resource_type == "EC2:MissingTags"]
    assert tag_findings == []


@mock_aws
def test_ebs_scan_flags_unattached_volume():
    ec2 = boto3.client("ec2", region_name="ap-south-1")
    ec2.create_volume(Size=20, AvailabilityZone="ap-south-1a", VolumeType="gp3")

    findings = scan_ebs(region="ap-south-1")
    types = {f.resource_type for f in findings}
    assert "EBS:Unattached" in types


@mock_aws
def test_ebs_scan_flags_large_volume():
    ec2 = boto3.client("ec2", region_name="ap-south-1")
    reservation = ec2.run_instances(ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t3.micro")
    instance_id = reservation["Instances"][0]["InstanceId"]
    volume = ec2.create_volume(Size=600, AvailabilityZone="ap-south-1a", VolumeType="gp3")
    ec2.attach_volume(VolumeId=volume["VolumeId"], InstanceId=instance_id, Device="/dev/sdf")

    findings = scan_ebs(region="ap-south-1")
    types = {f.resource_type for f in findings}
    assert "EBS:LargeVolume" in types


@mock_aws
def test_eip_scan_flags_unattached_address():
    ec2 = boto3.client("ec2", region_name="ap-south-1")
    ec2.allocate_address(Domain="vpc")

    findings = scan_eip(region="ap-south-1")
    assert len(findings) == 1
    assert findings[0].resource_type == "EIP:Unattached"


@mock_aws
def test_eip_scan_ignores_attached_address():
    ec2 = boto3.client("ec2", region_name="ap-south-1")
    reservation = ec2.run_instances(ImageId="ami-12345678", MinCount=1, MaxCount=1, InstanceType="t3.micro")
    instance_id = reservation["Instances"][0]["InstanceId"]
    alloc = ec2.allocate_address(Domain="vpc")
    ec2.associate_address(InstanceId=instance_id, AllocationId=alloc["AllocationId"])

    findings = scan_eip(region="ap-south-1")
    assert findings == []


@mock_aws
def test_s3_scan_flags_missing_lifecycle_policy():
    s3 = boto3.client("s3", region_name="ap-south-1")
    s3.create_bucket(Bucket="co-test-bucket", CreateBucketConfiguration={"LocationConstraint": "ap-south-1"})

    findings = scan_s3()
    types = {f.resource_type for f in findings}
    assert "S3:NoLifecyclePolicy" in types
