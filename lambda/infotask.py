import logging
import json
import datetime
import decimal

import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr

def test_auth(event):
    try:
        username = event['requestContext']['authorizer']['claims']['cognito:username']
        return(True)
    except:
        return(False)

# Get the talbe from dynamoDB
def dynamoDBtbl(tablename,region):
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(tablename)
    return(table)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


# Search task with taskid and return the userid of that task.
def readFromDB(table, userid , tablename, taskid):
    keyValue = userid
    try:
        response = table.query (
            TableName=tablename,
            KeyConditionExpression=Key('taskid').eq(taskid)
        )
    except botocore.exceptions.ClientError as e:
        print(e.response['Error']['Message'])
    else:
        if response:

            if len(response['Items']) > 0:
                return (response)
            else:
                # The taskid have no userid in the database
                return("Task belong to no body")
        else:
            return("NoUserFound")


def getTaskInfo (userid,taskid,BUCKET_NAME):
    s3resource  = boto3.resource('s3')                                                                             
    # Get path based on the taskid
    path = userid + "/" + taskid
    # Get the real path (this need to be revisited as it work with one object only)
    bucket = s3resource.Bucket(BUCKET_NAME)
    error = ""
    output= ""
    for obj in bucket.objects.filter(Prefix=path):
        key = obj.key
        if "stderr" in key:
            error =  signedURL(BUCKET_NAME, key)
        else:
            output =  signedURL(BUCKET_NAME, key)
    return((output, error))

def signedURL(BUCKET_NAME, key):
    s3client    = boto3.client('s3')
    # Generate the URL to get 'key-name' from 'bucket-name'
    url = s3client.generate_presigned_url(
        ClientMethod='get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': key
            }
    )
    return (url)

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()
    
def lambda_handler(event, context):
    if (not test_auth(event)):
        return {
            "statusCode": 404,
            "body": json.dumps("User is not authenticated", indent=4, cls=DecimalEncoder),
            "headers": {
                'Content-Type': 'application/json', 
                'Access-Control-Allow-Origin': '*' 
            }
    }
    
    try:
        username = event['requestContext']['authorizer']['claims']['cognito:username']
        resourceParams = json.loads(event['body'])
        taskid = resourceParams['Resource']['taskid']
        tablename = resourceParams['Resource']['taskstable']
    except:
        return {
            "statusCode": 404,
            "body": json.dumps("Some parameters are missing", indent=4, cls=DecimalEncoder),
            "headers": {
                'Content-Type': 'application/json', 
                'Access-Control-Allow-Origin': '*' 
            }
        }


    userid = username
    region = 'us-west-2'
    table = dynamoDBtbl(tablename,region)

    # Get user tasks
    response  = readFromDB(table, userid , tablename, taskid)
    taskowner = response['Items'][0]['userid']
    
    BUCKET_NAME= "tasks-uploads-app"

    if taskowner == userid:
        (output,error) = getTaskInfo (userid,taskid,BUCKET_NAME)
        data = {'url': {'output': output, 'error':error} , 'response':response['Items'][0]}
        return {
            "statusCode": 200,
            "body": json.dumps(data, default=myconverter ,indent=4, cls=DecimalEncoder),
            "headers": {
               #'Content-Type': 'text/plain', 
               'Content-Type': 'application/json',
               'Access-Control-Allow-Origin': '*' 
            }
        }
    else:
        return {
            "statusCode": 404,
            "body": json.dumps('Select your task to display first', indent=4, cls=DecimalEncoder),
            "headers": {
               'Content-Type': 'text/plain', 
               'Access-Control-Allow-Origin': '*' 
            }
        }
