import boto3

from os import environ


def lambda_handler(event: dict, context: dict) -> None:
    print('event: {}'.format(event))

    process(event)


def process(event: dict) -> None:
    const = Constants
    print('process')

    records: list = event[const.KEY_RECORDS]

    for item in records:
        if item[const.KEY_EVENT_NAME] == const.DDB_EVENT_INSERT:
            new_data: dict = item[const.KEY_DYNAMO_DB][const.KEY_NEW_IMAGE]

            #event_data: dict = new_data[const.KEY_EVENT_DATA][const.KEY_DDB_TYPE_STRING]
            #event_name: str = event_data[const.KEY_NAME][const.KEY_DDB_TYPE_STRING]
            # BUG: The input format is different from what's expected here
            event_name: str = const.EVENT_APP_START

            # NOTE: We're connecting to the Docker container called motoserver
            dynamodb: any = boto3.resource(const.KEY_DYNAMO_DB, endpoint_url="http://motoserver:5000")

            table = dynamodb.Table(environ[const.ENV_DDB_TABLE_DEVICES_APPLICATIONS_STATUS])
            try:
                response = table.put_item(
                    Item={
                        const.KEY_DEVICE_ID: new_data[const.KEY_DEVICE_ID][const.KEY_DDB_TYPE_STRING],
                        const.KEY_NAME: new_data[const.KEY_SOURCE][const.KEY_DDB_TYPE_STRING],
                        const.KEY_PACKAGE: new_data[const.KEY_PACKAGE][const.KEY_DDB_TYPE_STRING],
                        const.KEY_STATUS: const.STATUS_ON if event_name == const.EVENT_APP_START else const.STATUS_OFF,
                        const.KEY_TIMESTAMP: new_data[const.KEY_TIMESTAMP][const.KEY_DDB_TYPE_STRING]
                    },
                    ConditionExpression="(attribute_exists(device_id) AND attribute_exists(package) AND #timestamp < :new_timestamp) OR (attribute_not_exists(device_id) AND attribute_not_exists(package))",
                    ExpressionAttributeNames={
                        "#timestamp": const.KEY_TIMESTAMP
                    },
                    ExpressionAttributeValues={
                        ":new_timestamp": new_data[const.KEY_TIMESTAMP][const.KEY_DDB_TYPE_STRING]
                    }
                )
                print("response: {}".format(response))
            except Exception as error:
                print('--ERROR process: {}'.format(error))


class Constants:
    KEY_RECORDS: str = 'Records'
    KEY_EVENT_NAME: str = 'eventName'
    KEY_DYNAMO_DB: str = 'dynamodb'
    KEY_NEW_IMAGE: str = 'NewImage'
    KEY_DEVICE_ID: str = 'device_id'
    KEY_PACKAGE: str = 'package'
    KEY_EVENT_DATA: str = 'event_data'
    KEY_NAME: str = 'name'
    KEY_SOURCE: str = 'source'
    KEY_TIMESTAMP: str = 'timestamp'
    KEY_STATUS: str = 'status'
    KEY_DDB_TYPE_STRING: str = 'S'
    KEY_DDB_TYPE_MAP: str = 'M'
    DDB_EVENT_INSERT: str = 'INSERT'
    STATUS_ON: str = 'on'
    STATUS_OFF: str = 'off'
    EVENT_APP_START = 'APP_START'
    ENV_DDB_TABLE_DEVICES_APPLICATIONS_STATUS: str = 'DDB_TABLE_DEVICES_APPLICATIONS_STATUS'

