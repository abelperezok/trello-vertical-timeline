import pytest
import docker
import boto3


table_name = 'test_table'
local_url = 'http://localhost:8000'

def scan_table():
    dynamodb = boto3.resource('dynamodb', endpoint_url=local_url)
    table = dynamodb.Table(table_name)
    response = table.scan()
    print(response.get('Items', []))

def create_table():
    client = boto3.client('dynamodb', endpoint_url=local_url)
    response = client.create_table(
        AttributeDefinitions=[
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'},
            {'AttributeName': 'GSI1', 'AttributeType': 'S'}
        ],
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'PK', 'KeyType': 'HASH'},
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}
        ],
        BillingMode='PROVISIONED',
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        },
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {'AttributeName': 'GSI1', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            },
        ]
    )
    waiter = client.get_waiter('table_exists')
    waiter.wait(TableName=table_name, WaiterConfig={
                'Delay': 3, 'MaxAttempts': 10})
    return response


@pytest.fixture(scope="session")
def docker_dynamodb():
    client = docker.from_env()
    container = client.containers.run(
        image='amazon/dynamodb-local',
        ports={'8000/tcp': 8000},
        publish_all_ports=True,
        auto_remove=True,
        detach=True)
    table = create_table()
    yield table
    container.stop()