# system manager 

Cognito:
  1) Create pool and name it
  2) Enable MFA required during the creation process , otherwise the MFA will be optional.
  3) Use the trigger for more security
  4) During development time (and it might be on the production too) : on Policies -> check "Only allow administrators to create users"


S3:
  1) Upload the content of the website folder into S3 bucket
  2) Fix js/config.js to have the PoolId and ClientPoolId
  3) Make the bucket public
  4) js/config.js is public??? Security issue ??? NOT based answer on :
     a) AWS answer on: https://forums.aws.amazon.com/message.jspa?messageID=757990#757990 
     b) Also answer and solution on : https://github.com/amazon-archives/amazon-cognito-identity-js/issues/312


Lambda:
  1) 
  2) upload the lambdas in the repository as functions in Lambda
  3) Lambda needs the role to 
    a) GetItem and PutItem in DynamoDB
    b) Manipulate S3 objects
  4) Test lambda with the testLambda code provided in the test folder
  5) the Access-Control-Allow-Origin in Lambda (specifically in the return(response))  code was important


API GateWay:
  1) Authorizer: 
     From Cognito get the user pool name
  2) Post and Get
    a) In method request settings Select the name of the Authorization created in step 1
    b) In integration request , then select Use Lambda and use Lambda proxy integration
  2) Authorizationto
    a) Userpool 
    b) Client ID auth pool
  3) enable CORS (Access-Control-Allow-Origin ) from the world ? 


DynamoDB:
  1) Create a table with the parameter needed
  2) Table name will be used in Lambda function
  3) Table schema : 
        Table name : tasks
        Primary Key : taskid
        SortKey : userid
        Seconday index : userid-index from userid key
        Note that : Lambda should have query access to tasks and tasks/*


Issues: 
  1) Admin can create users from the console, but the temporary user password need to change from an API call not from the console. 
     https://stackoverflow.com/questions/40287012/how-to-change-user-status-force-change-password
     It is an issue because what if we want to disable user registeration and only admin add users. Then Admin need API calls to confirm the password.

  2) If MFA enabled and Role created for it, then role need to be removed first if normal user add and update would resume.
     https://forums.aws.amazon.com/thread.jspa?threadID=236942 

  3) Lambda parallel execution (Lambda Maximum execution duration per request	300 seconds (5 minutes)) :
     https://github.com/serverless/serverless/issues/180
     https://aws.amazon.com/blogs/big-data/building-scalable-and-responsive-big-data-interfaces-with-aws-lambda/
     https://aws.amazon.com/blogs/compute/parallel-processing-in-python-with-aws-lambda/


Resources:
  * Serverless Web App: https://aws.amazon.com/getting-started/projects/build-serverless-web-app-lambda-apigateway-s3-dynamodb-cognito/
                        https://www.youtube.com/watch?v=Byhg9BBsbJw
  * Cognito JavaScriptSDK: https://docs.aws.amazon.com/cognito/latest/developerguide/using-amazon-cognito-user-identity-pools-javascript-examples.html
  * DynamoDB : https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.03.html
               https://stackoverflow.com/questions/42371411/dynamodb-how-to-query-by-sort-key-only
               https://stackoverflow.com/questions/35758924/how-do-we-query-on-a-secondary-index-of-dynamodb-using-boto3
               http://programalittleaday.blogspot.com/2016/02/query-dynamodb-gsi-global-secondary.html

