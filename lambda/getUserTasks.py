from __future__ import division, print_function, unicode_literals
from boto3.dynamodb.conditions import Key, Attr

from datetime import datetime
import logging
import json
import sys

import decimal

import boto3
import botocore

def test_auth(event):
    try:
        username = event['requestContext']['authorizer']['claims']['cognito:username']
        return(True)
    except:
        return(False)
        
def dynamoDBtbl(tableName):
    dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
    table = dynamodb.Table(tableName)
    return(table)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


    
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

    # Get user tasks
    usertasks = getUserTasks (userid, 'tasks')
    sendUserTasks = {"resources" : usertasks['Items'],}
    
    return {
        "statusCode": 200,
        "body": json.dumps(sendUserTasks, indent=4, cls=DecimalEncoder),
        "headers": {
           'Content-Type': 'application/json', 
           'Access-Control-Allow-Origin': '*' 
       }
    }

# Get user Tasks
def getUserTasks (userid, tablename):
    table = dynamoDBtbl(tablename)
    keyname   = 'userid'
    indexname = 'userid-index'
    response  = readFromDB(table, userid , tablename, keyname, indexname)
    return (response)

# Search the user (with userid) tasks
def readFromDB(table, userid , tablename, keyname, indexname):
    keyValue = userid
    keyName = keyname
    try:
        response = table.query (
            TableName=tablename,
            IndexName=indexname,
            KeyConditionExpression=Key(keyName).eq(keyValue)
        )
    except botocore.exceptions.ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return (response)
