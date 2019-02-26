from __future__ import division, print_function, unicode_literals
from boto3.dynamodb.conditions import Key, Attr

from datetime import datetime
import logging
import json
import sys
import decimal

import boto3
import botocore

from random import randint


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
    
    username = event['requestContext']['authorizer']['claims']['cognito:username']
    userid = username
    
    taskParams = json.loads(event['body'])
    
    response = ""
    
    checkresparm = checkTaskParams(taskParams)
    
    if (checkresparm):
        table = dynamoDBtbl()
    
        # Get user tasks
        tablename = 'tasks'
        keyname   = 'userid'
        indexname = 'userid-index'

        # Creating new task
        taskid = createTask (userid, taskParams)
        #taskResponseCode =  int(taskresponse["ResponseMetadata"]["HTTPStatusCode"])
        if taskid:
            # Insert new field for the users' new task
            dynamoDBresponse = insertToDB(table, taskid, userid)
            dynamoDBresponseCode = int(dynamoDBresponse["ResponseMetadata"]["HTTPStatusCode"])
            return {
                "statusCode": dynamoDBresponseCode,
                "body": json.dumps("Your task is created, please allow few minutes for it to be ready", indent=4, cls=DecimalEncoder),
                "headers": {
                   'Content-Type': 'application/json', 
                   'Access-Control-Allow-Origin': '*' 
                }
            }
        else:
            return {
                #"statusCode": taskResponseCode,
                "statusCode": 200,
                "body": json.dumps("Failed to create the task", indent=4, cls=DecimalEncoder),
                "headers": {
                   'Content-Type': 'application/json', 
                   'Access-Control-Allow-Origin': '*' 
                }
            }
    else:
        return {
            "statusCode": 200,
            "body": json.dumps("Invalid or missing parameters", indent=4, cls=DecimalEncoder),
            "headers": {
               'Content-Type': 'application/json', 
               'Access-Control-Allow-Origin': '*' 
            }
        }


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

     
# Search the user (with userid) tasks
def insertToDB(table, taskid, userid):
    try:
        response = table.put_item(
            Item={
                'taskid': taskid,
                'userid': userid
            }
        )
    except botocore.exceptions.ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return (response)


# Check if the user submit valid parameters
def checkTaskParams(taskParams):
    cmd     = taskParams['Resource']['CMD']
    if cmd:
        return (True)
    else:
        return (False)


# Create the task with task id = taskid
def createTask (userid, taskParams):
    command = taskParams['Resource']['CMD']
    environ = 'Public_1a_AdminEC2'
    task    = runOneTask(userid, command, environ)
    taskid  = task['Command']['CommandId']
    return(taskid)
    

def runOneTask(userid, cmd, environ):
        ssmclient = boto3.client('ssm', region_name="us-east-1")
        AWS_BUCKET_NAME = 'tasks-uploads'
        task = ssmclient.send_command(Parameters={'commands': [cmd,]},Targets=[{'Key': 'tag:Name','Values': [environ,]},],DocumentName='AWS-RunShellScript',DocumentVersion='$LATEST',OutputS3BucketName=AWS_BUCKET_NAME,OutputS3KeyPrefix=userid,CloudWatchOutputConfig={'CloudWatchLogGroupName': 'agentstatus','CloudWatchOutputEnabled': True})
        return (task)


def save_file_to_bucket(userid, taskid, BUCKET_NAME, FILE_NAME):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)
    path = userid + "/" + taskid + "/" + FILE_NAME
    data = path
    bucket.put_object(
        #ACL='public-read',
        #ContentType='application/json',
        Key=path,
        Body=data,
    )

    body = {
        "uploaded": "true",
        "bucket": BUCKET_NAME,
        "path": path,
    }
    return {
        "statusCode": 200,
        "body": json.dumps(body)
    }
