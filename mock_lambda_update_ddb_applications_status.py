import boto3

from os import environ

import shutil


class MockDDBLambda():
    table_android_events: any
    table_devices_applications_status: any
    lambda_function: dict
    event_source_uuid: str

    def __init__(self):
        print("INIT MOCK")
        environ['AWS_ACCESS_KEY_ID'] = '1234567'
        environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        environ['AWS_SECURITY_TOKEN'] = 'testing'
        environ['AWS_SESSION_TOKEN'] = 'testing'

    # Deleting (Calling destructor)
    def __del__(self):
        print('Destructor called')

    def create_ddb_tables(self) -> None:
        print('create_ddb_tables called')

        dynamodb_client: any = boto3.client('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:5000")
        # Create the table that will take in Android Events
        self.table_android_events = dynamodb_client.create_table(
            TableName='MockTableAndroidEvents',
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 2,
                'WriteCapacityUnits': 2
            },
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_AND_OLD_IMAGES'
            }
        )

        # Create the table that will store device's application status
        self.table_devices_applications_status = dynamodb_client.create_table(
            TableName='MockTableDeviceApplicationStatus',
            KeySchema=[
                {
                    'AttributeName': 'device_id',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'package',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'device_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'package',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 2,
                'WriteCapacityUnits': 2
            }
        )

    def create_lambda_role(self) -> dict:
        print('create_lambda_role called')

        iam_client: any = boto3.client("iam", region_name="us-east-1", endpoint_url="http://localhost:5000")
        # First Create Policy
        """
        {
            'Policy': {
                'PolicyName': 'string',
                'PolicyId': 'string',
                'Arn': 'string',
                'Path': 'string',
                'DefaultVersionId': 'string',
                'AttachmentCount': 123,
                'PermissionsBoundaryUsageCount': 123,
                'IsAttachable': True|False,
                'Description': 'string',
                'CreateDate': datetime(2015, 1, 1),
                'UpdateDate': datetime(2015, 1, 1),
                'Tags': [
                    {
                        'Key': 'string',
                        'Value': 'string'
                    },
                ]
            }
        }
        """
        # Now Create Role
        return iam_client.create_role(
            RoleName='role-lambda_update_ddb_applications_status',
            AssumeRolePolicyDocument="""{
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": [
                            "xray:PutTraceSegments",
                            "xray:PutTelemetryRecords"
                        ],
                        "Resource": "*",
                        "Effect": "Allow"
                    },
                    {
                        "Action": "dynamodb:PutItem",
                        "Resource": "arn:aws:dynamodb:eu-west-1:268976501186:table/analytics-manager-devices-applications-status",
                        "Effect": "Allow"
                    },
                    {
                        "Action": "dynamodb:ListStreams",
                        "Resource": "*",
                        "Effect": "Allow"
                    },
                    {
                        "Action": [
                            "dynamodb:DescribeStream",
                            "dynamodb:GetRecords",
                            "dynamodb:GetShardIterator"
                        ],
                        "Resource": "arn:aws:dynamodb:eu-west-1:268976501186:table/analytics-manager-events-android/stream/2021-09-02T08:55:28.380",
                        "Effect": "Allow"
                    }
                ]
            }"""
        )

    def create_lambda(self) -> None:
        print('create_lambda called')

        shutil.make_archive('mocklambda', 'zip', 'mockfunction/')

        role: dict = self.create_lambda_role()

        lambda_client: any = boto3.client('lambda', region_name='us-east-1', endpoint_url="http://localhost:5000")
        with open('mocklambda.zip', "rb") as in_file:
            self.lambda_function = lambda_client.create_function(
                FunctionName='test-lambda-update-ddb-application-status',
                Runtime='python3.8',
                Role=role['Role']['Arn'],
                Handler='lambda_function.lambda_handler',
                Code={
                    'ZipFile': in_file.read()
                },
                Publish=True,
                Timeout=30,
                MemorySize=128,
                Environment={
                    'Variables': {
                        'DDB_TABLE_DEVICES_APPLICATIONS_STATUS': self.table_devices_applications_status['TableDescription'][
                            'TableName']
                    }
                }
            )

    def add_ddb_stream_on_lambda(self) -> None:
        print('add_ddb_stream_on_lambda called')

        lambda_client: any = boto3.client('lambda', region_name='us-east-1', endpoint_url="http://localhost:5000")

        response: any = lambda_client.create_event_source_mapping(
            EventSourceArn=self.table_android_events['TableDescription']['LatestStreamArn'],
            FunctionName=self.lambda_function['FunctionArn'],
            Enabled=True
        )
        self.event_source_uuid = response['UUID']
        print('response: {}'.format(response))

    def print_event_source_mapping_details(self) -> None:
        print('print_event_source_mapping_details called')

        lambda_client: any = boto3.client('lambda', region_name='us-east-1', endpoint_url="http://localhost:5000")

        response = lambda_client.get_event_source_mapping(
            UUID=self.event_source_uuid
        )
        print("print_event_source_mapping_details response: {}".format(response))
