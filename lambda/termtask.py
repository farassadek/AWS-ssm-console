
import logging
import json

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
        
def dynamoDBtbl():
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table('tasks')
    return(table)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


# Search database for task with taskid and check if it belong to the userid
def checkUserTaskOwnership(table, userid , tablename, taskid):
    try:
        response = table.query (
            TableName=tablename,
            KeyConditionExpression=Key('taskid').eq(taskid)
        )
    except botocore.exceptions.ClientError as e:
        print(e.response['Error']['Message'])
        return(False)
    else:
        flag = False
        try:
            if (response['Items'][0]['userid'] == userid):
                flag = True
        except:
            pass
        return(flag)
     
# Search the user (with userid) tasks
def updateDB(table, taskid, userid):
    try:
        response = table.delete_item(
            Key={
                'taskid': taskid,
                'userid' : userid
            }
        )
    except botocore.exceptions.ClientError as e:
        print(e.response['Error']['Message'])
        return(False)
    else:
        return (True)


# Delete task with id = taskid
def terminateusertask (userid,taskid,BUCKET_NAME):
    try:
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(BUCKET_NAME)
        path = userid + "/" + taskid
        bucket.objects.filter(Prefix=path).delete()
        return(True)
    except:
        return(False)



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
    table = dynamoDBtbl()

    # Get user tasks
    tablename = 'tasks'
    BUCKET_NAME = "tasks-uploads"
    
    if checkUserTaskOwnership(table, userid , tablename, taskid):
        updResp=False
        terRes = terminateusertask(userid,taskid,BUCKET_NAME)
        if terRes:
            updResp = updateDB(table, taskid, userid)
        if terRes and updResp:
            return {
                "statusCode": 200,
                "body": json.dumps("Task terminated and the database updated", indent=4, cls=DecimalEncoder),
                "headers": {
                   'Content-Type': 'text/plain', 
                   'Access-Control-Allow-Origin': '*' 
                }
            }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps("Something went wrong please ask the Admin to cleanup your resources manually", indent=4, cls=DecimalEncoder),
                "headers": {
                   'Content-Type': 'text/plain', 
                   'Access-Control-Allow-Origin': '*' 
                }
            }
            
    else:
        return {
            "statusCode": 404,
            "body": json.dumps('Task not accessible or this user is no permitted to delete this task', indent=4, cls=DecimalEncoder),
            "headers": {
               'Content-Type': 'text/plain', 
               'Access-Control-Allow-Origin': '*' 
           }
        }

