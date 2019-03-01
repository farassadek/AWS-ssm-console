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
        

# Get the talbe from dynamoDB
def dynamoDBtbl(tablename,region):
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(tablename)
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
    
    taskParams = json.loads(event['body'])
    
    checkresparm = checkTaskParams(taskParams)
    
    userid = username
    region = 'us-west-2'
    tablename = "tasks"
    BUCKET_NAME = 'tasks-uploads-app'

    if (checkresparm):
        table = dynamoDBtbl(tablename,region)
    
        # Get user tasks
        keyname   = 'userid'
        indexname = 'userid-index'

        # Creating new task
        taskid = createTask (userid, taskParams,BUCKET_NAME,region)
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
    environ = taskParams['Resource']['ENV']
    if cmd and environ:
        return (True)
    else:
        return (False)


# Create the task with task id = taskid
def createTask (userid, taskParams,BUCKET_NAME,region):
    command = taskParams['Resource']['CMD']
    environ = taskParams['Resource']['ENV']
    task    = runOneTask(userid, command, environ,BUCKET_NAME,region)
    taskid  = task['Command']['CommandId']
    return(taskid)
    

def runOneTask(userid, cmd, environ, BUCKET_NAME,region):
        ssmclient = boto3.client('ssm', region_name=region)
        task = ssmclient.send_command(Parameters={'commands': [cmd,]},Targets=[{'Key': 'tag:Name','Values': [environ,]},],DocumentName='AWS-RunShellScript',DocumentVersion='$LATEST',OutputS3BucketName=BUCKET_NAME,OutputS3KeyPrefix=userid,CloudWatchOutputConfig={'CloudWatchLogGroupName': 'agentstatus','CloudWatchOutputEnabled': True})
        return (task)
