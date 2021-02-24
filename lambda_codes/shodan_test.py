import boto3
import urllib3
import json

http = urllib3.PoolManager()

def shodantest(dynamoDBTableName, default_region, clientDynamo):
    response = clientDynamo.scan(
        TableName = dynamoDBTableName,
        AttributesToGet=[
                'EIP',
            ],
    )
    responseItems = response['Items']
    responseIPs = []
    for responseItem in responseItems:
        responseIPs.append(responseItem['EIP']['S'])

    client = boto3.client('ssm', default_region)
    ssmResponse = client.get_parameters(
        Names=[
            'shodan_key'
        ],
        WithDecryption=True
    )
    shodan_key = ssmResponse['Parameters'][0]['Value']
    for IP in responseIPs:
        URL = r"https://api.shodan.io/shodan/host/"
        PARAMS = {
            "key": shodan_key
        }
        r = http.request(method = 'GET', url = URL+IP, fields = PARAMS)
        data = json.loads(r.data.decode('utf-8'))
        if ("error" in data.keys() and (data['error'] == "No information available for that IP." or data['error'] == "Invalid IP")):
            continue
        else:
            updateresponse = clientDynamo.update_item(
                TableName = dynamoDBTableName, 
                Key = {
                    "EIP": {
                        'S': str(IP)
                    }
                },
                UpdateExpression='SET Risk = :riskVal, ExploitLink = :shodanURL',
                ExpressionAttributeValues={
                    ':riskVal':  {
                        'S': 'Medium'
                    },
                    ':shodanURL':  {
                        'S': "https://www.shodan.io/host/"+str(IP)
                    }
                }
            )
    return True