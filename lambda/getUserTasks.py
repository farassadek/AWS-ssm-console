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
    tablename = 'tasks'
    region = 'us-west-2'
    table = dynamoDBtbl(tablename,region)

    # Get user tasks
    usertasks = getUserTasks (userid, table)
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
def getUserTasks (userid, table):
    keyname   = 'userid'
    indexname = 'userid-index'
    response  = readFromDB(table, userid, keyname, indexname)
    return (response)

# Search the user (with userid) tasks
def readFromDB(table, userid, keyname, indexname):
    keyValue = userid
    keyName = keyname
    try:
        response = table.query (
            IndexName=indexname,
            KeyConditionExpression=Key(keyName).eq(keyValue)
        )
    except botocore.exceptions.ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return (response)

