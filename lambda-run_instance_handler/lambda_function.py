import urllib.request
import json
import boto3
import os

ec2 = boto3.client('ec2', region_name='us-east-1')
s3 = boto3.client('s3')


def plant_flag(ticket):
    return

    s3.put_object(
        Body='',
        Bucket=os.environ['S3_OUTPUT_BUCKET'],
        Key=ticket
    )

def ticket_in_flight(ticket):
    return False

    resp = s3.list_objects_v2(
        Bucket=os.environ['S3_OUTPUT_BUCKET'],
        MaxKeys=123,
        Prefix=ticket
    )

    return len(resp.get('Contents', [])) > 0


def provision(event):
    payload = json.loads(event['Records'][0]['body'])

    if 'ticket' not in payload:
        raise Exception('No ticket provided')

    ticket = payload['ticket']

    print(f'Recieved ticket {ticket}')

    #if ticket_in_flight(ticket):
    #    print('Ticket already being processed')
    #    return


    #plant_flag(ticket)

    input_ = payload['input']

    input_['MinCount'] = 1
    input_['MaxCount'] = 1

    resp = {}

    try:
        r = ec2.run_instances(**input_)

        print(f'Provisioned instance: {r["Instances"][0]["InstanceId"]}')

        resp['instance_id'] = r['Instances'][0]['InstanceId']

        if len(s3.list_objects_v2(
            Bucket=os.environ['S3_OUTPUT_BUCKET'],
            MaxKeys=123,
            Prefix=ticket
        ).get('Contents', [])) > 0:
            return
    except Exception as ex:
        resp['error'] = {
            'message': str(ex),
            'type': ex.__class__.__name__
        }

    s3.put_object(
        Body=json.dumps(resp),
        Bucket=os.environ['S3_OUTPUT_BUCKET'],
        Key=payload['ticket']
    )

def lambda_handler(event, context):
    try:
        provision(event)
    except Exception as ex:
        s3.put_object(
            Body=json.dumps({
                'error': {
                    'message': str(ex),
                    'type': ex.__class__.__name__
                }
            }),
            Bucket=os.environ['S3_OUTPUT_BUCKET'],
            Key='error'
        )
