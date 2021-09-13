import unittest
import json
import boto3
import time

from mock_lambda_update_ddb_applications_status import MockDDBLambda


class PopulateDeviceApplicationStatusTest(unittest.TestCase):
    mocked_db: MockDDBLambda

    @classmethod
    def setUpClass(self):
        print("setUpClass")
        self.mocked_db = MockDDBLambda()
        self.mocked_db.create_ddb_tables()
        self.mocked_db.create_lambda()

    def test_android_event_put_ddb_stream_lambda(self):
        print('test_android_event_put_ddb_stream')

        # Add the stream on the lambda
        self.mocked_db.add_ddb_stream_on_lambda()

        dynamodb_client: any = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:5000")
        table: any = dynamodb_client.Table(self.mocked_db.table_android_events['TableDescription']['TableName'])
        table.put_item(
            Item={
                "id": "test-id-2",
                "timestamp":"2021-09-03 18:45:00",
                "unix_timestamp": "12312312321",
                "device_id": "test-device-id",
                "mac_address": "test-mac-address",
                "source": "test-source",
                "package": "test-package",
                "event_data": json.dumps({"name": "APP_START"})
            }
        )

        # Check the Device Application Status
        table_status: any = dynamodb_client.Table(self.mocked_db.table_devices_applications_status['TableDescription']['TableName'])
        response: any = table_status.scan()["Items"]
        print("")
        print('Scan response table_status: {}'.format(response))
        print("")

        log_group_name = "/aws/lambda/test-lambda-update-ddb-application-status"
        logs_conn = boto3.client("logs", region_name="us-east-1", endpoint_url="http://localhost:5000")
        streams = logs_conn.describe_log_streams(logGroupName=log_group_name)["logStreams"]
        events = logs_conn.get_log_events(
            logGroupName=log_group_name,
            logStreamName=streams[0]["logStreamName"],
        )["events"]
        for event in events:
            print(event["message"])

    @classmethod
    def tearDownClass(self):
        print("tearDownClass")
        self.mocked_db = None


if __name__ == '__main__':
    unittest.main()
