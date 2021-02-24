import json
import os
import IPcrawler
import shodan_test
import boto3

def lambda_handler(event, context):

    default_region = os.environ['AWS_REGION']
    dynamoDBTableName = os.environ['dynamoDBTableName']
    clientDynamo = boto3.client('dynamodb', region_name=default_region)

    # Getting all active regions
    clientRegion = boto3.client('ec2', region_name=default_region)
    regions = clientRegion.describe_regions()
    Regions = regions['Regions']
    activeRegionNames = []
    for i in Regions:
        activeRegionNames.append(i['RegionName'])

    # Crawling all the IPs
    IPcrawler.get_EIPs(activeRegionNames = activeRegionNames, dynamoDBTableName = dynamoDBTableName, clientDynamo = clientDynamo)
    IPcrawler.get_elbv2IPs(activeRegionNames = activeRegionNames, dynamoDBTableName = dynamoDBTableName, clientDynamo = clientDynamo)
    IPcrawler.get_elbIPs(activeRegionNames = activeRegionNames, dynamoDBTableName = dynamoDBTableName, clientDynamo = clientDynamo)
    IPcrawler.get_esIPs(activeRegionNames = activeRegionNames, dynamoDBTableName = dynamoDBTableName, clientDynamo = clientDynamo)
    IPcrawler.get_mqIPs(activeRegionNames = activeRegionNames, dynamoDBTableName = dynamoDBTableName, clientDynamo = clientDynamo)
    IPcrawler.get_dmsIPs(activeRegionNames = activeRegionNames, dynamoDBTableName = dynamoDBTableName, clientDynamo = clientDynamo)
    IPcrawler.get_rdsIPs(activeRegionNames = activeRegionNames, dynamoDBTableName = dynamoDBTableName, clientDynamo = clientDynamo)

    # Test all the IPs
    shodan_test.shodantest(dynamoDBTableName = dynamoDBTableName, default_region = default_region, clientDynamo= clientDynamo)
    
    return {
        'statusCode': 200,
        'body': json.dumps("Done")
    }
