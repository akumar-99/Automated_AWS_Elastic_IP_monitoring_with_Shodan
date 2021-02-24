import boto3
import datetime
import socket
import re
import os

# Variables
months = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
}

# Convert datetime to epochtime
def datetimeToepochtime(dateTime):
    time = dateTime[4].split(':')

    epoch_time = datetime.datetime(
        year=int(dateTime[3]),
        month=int(months[dateTime[2]]),
        day=int(dateTime[1]),
        hour=int(time[0]),
        minute=int(time[1]),
        second=int(time[2])
    ).timestamp()

    return(epoch_time)

# Get account ID
accountID = boto3.client('sts').get_caller_identity()['Account']


#####################################

# Get all elastic IPs and push them simultaneously
def get_EIPs(activeRegionNames, dynamoDBTableName, clientDynamo):
    for regionName in activeRegionNames:
        clientEIP = boto3.client('ec2', region_name=regionName)
        response = clientEIP.describe_addresses()
        EIPList = response['Addresses']
        
        # Skip the region if no addresses found
        if len(EIPList) == 0:
            continue

        dateTime = response['ResponseMetadata']['HTTPHeaders']['date'].split()
        epochTime = datetimeToepochtime(dateTime)

        for i in EIPList:
            status = False
            if 'AssociationId' in i.keys():
                status = True
            Item={
                "EIP": {
                    'S': str(i['PublicIp']),
                },
                "Time of scan": {
                    'S': str(epochTime)
                },
                "Region": {
                    'S': str(regionName)
                },
                "Account ID": {
                    'S': str(accountID)
                },
                "Active": {
                    'BOOL': status
                },
                "AWS Service": {
                    'S': "EC2"
                }
            }
            response = clientDynamo.put_item(
                TableName=dynamoDBTableName,
                Item = Item
            )
    return("EIPs done")
######################################


# Get all ELBv2 IPs and push them simultaneously
def get_elbv2IPs(activeRegionNames, dynamoDBTableName, clientDynamo):
    for regionName in activeRegionNames:
        clientEIP = boto3.client('elbv2', region_name=regionName)
        response = clientEIP.describe_load_balancers()
        elbv2List = response['LoadBalancers']

        # Skip the region if no addresses found
        if len(elbv2List) == 0:
            continue

        dateTime = response['ResponseMetadata']['HTTPHeaders']['date'].split()
        epochTime = datetimeToepochtime(dateTime)
        for elbv2 in elbv2List:
            status = False
            if elbv2['Scheme'] == "internet-facing" and (elbv2["Type"] == "network" or elbv2["Type"] == "application"):
                if elbv2['State']['Code'] == 'active':
                    status = True
                Item={
                    "EIP": {
                        'S': str(socket.gethostbyname(elbv2["DNSName"])),
                    },
                    "Time of scan": {
                        'S': str(epochTime)
                    },
                    "Region": {
                        'S': str(regionName)
                    },
                    "Account ID": {
                        'S': str(accountID)
                    },
                    "Active": {
                        'BOOL': status
                    },
                    "AWS Service": {
                        'S': "ELBv2"
                    }

                }
                response = clientDynamo.put_item(
                    TableName=dynamoDBTableName,
                    Item = Item
                )
    return("ELBv2 done")
######################################


# Get all ELB IPs and push them simultaneously
def get_elbIPs(activeRegionNames, dynamoDBTableName, clientDynamo):
    for regionName in activeRegionNames:
        clientEIP = boto3.client('elb', region_name=regionName)
        response = clientEIP.describe_load_balancers()
        elbList = response['LoadBalancerDescriptions']

        # Skip the region if no addresses found
        if len(elbList) == 0:
            continue

        dateTime = response['ResponseMetadata']['HTTPHeaders']['date'].split()
        epochTime = datetimeToepochtime(dateTime)

        for elb in elbList:
            if elb['Scheme'] == "internet-facing":
                # ELB status could not be found
                status = True
                # if elb['State']['Code'] == 'active':
                #     status = True
                Item={
                    "EIP": {
                        'S': str(socket.gethostbyname(elb["DNSName"])),
                    },
                    "Time of scan": {
                        'S': str(epochTime)
                    },
                    "Region": {
                        'S': str(regionName)
                    },
                    "Account ID": {
                        'S': str(accountID)
                    },
                    "Active": {
                        'BOOL': status
                    },
                    "AWS Service": {
                        'S': "ELB"
                    }

                }
                response = clientDynamo.put_item(
                    TableName=dynamoDBTableName,
                    Item = Item
                )
    return("ELB done")
######################################


# Get all ES IPs and push them simultaneously
# solution for status ??
def get_esIPs(activeRegionNames, dynamoDBTableName, clientDynamo):
    for regionName in activeRegionNames:
        clientES = boto3.client('es', region_name=regionName)
        response = clientES.list_domain_names()
        esList = response['DomainNames']

        # Skip the region if no addresses found
        if len(esList) == 0:
            continue

        # print(esList)

        dateTime = response['ResponseMetadata']['HTTPHeaders']['date'].split()
        epochTime = datetimeToepochtime(dateTime)

        for es in esList:
            esResponse = clientES.describe_elasticsearch_domain(DomainName=es['DomainName'])
            esDomainStatus = esResponse['DomainStatus']

            # Skip private ES
            if "VPCOptions" in esDomainStatus.keys():
                continue

            if (esDomainStatus['Created'] == True and esDomainStatus['Deleted'] == False and "Endpoint" in esDomainStatus.keys()):
                esEndpoint = esDomainStatus['Endpoint']
                esIPs = socket.gethostbyname_ex(esEndpoint)[-1]
                status = True
                # if elb['State']['Code'] == 'active':
                #     status = True
                for esIP in esIPs:
                    Item={
                        "EIP": {
                            'S': str(esIP),
                        },
                        "Time of scan": {
                            'S': str(epochTime)
                        },
                        "Region": {
                            'S': str(regionName)
                        },
                        "Account ID": {
                            'S': str(accountID)
                        },
                        "Active": {
                            'BOOL': status
                        },
                        "AWS Service": {
                            'S': "ES"
                        }
                    }
                    response = clientDynamo.put_item(
                        TableName=dynamoDBTableName,
                        Item = Item
                    )
    return("ES done")
######################################


# Get all MQ IPs and push them simultaneously
# solution for status ??
def get_mqIPs(activeRegionNames, dynamoDBTableName, clientDynamo):
    for regionName in activeRegionNames:
        clientMQ = boto3.client('mq', region_name=regionName)
        response = clientMQ.list_brokers()
        mqList = response['BrokerSummaries']

        # Skip the region if no MQ found
        if len(mqList) == 0:
            continue

        dateTime = response['ResponseMetadata']['HTTPHeaders']['date'].split()
        epochTime = datetimeToepochtime(dateTime)

        mqIDList = []
        for mq in mqList:
            mqIDList.append(mq['BrokerId'])

        for mqID  in mqIDList:
            mqResponse = clientMQ.describe_broker(BrokerId=mqID)
            status = True
            # if elb['State']['Code'] == 'active':
            #     status = True
            for brokerinstance in mqResponse['BrokerInstances']:
                if (mqResponse['PubliclyAccessible'] == True and mqResponse['BrokerState'] == "RUNNING"):
                    brokerinstanceURL = brokerinstance['ConsoleURL']
                    brokerinstanceURL = brokerinstanceURL.replace('https://', "")
                    brokerinstanceURL = re.sub(r"((?::))(?:[0-9]+)$", "", brokerinstanceURL)
                    mqIPs = socket.gethostbyname_ex(brokerinstanceURL)[-1]
                    for mqIP in mqIPs:
                        Item={
                            "EIP": {
                                'S': str(mqIP),
                            },
                            "Time of scan": {
                                'S': str(epochTime)
                            },
                            "Region": {
                                'S': str(regionName)
                            },
                            "Account ID": {
                                'S': str(accountID)
                            },
                            "Active": {
                                'BOOL': status
                            },
                            "AWS Service": {
                                'S': "MQ"
                            }
                        }
                        response = clientDynamo.put_item(
                            TableName=dynamoDBTableName,
                            Item = Item
                        )
    return("MQ done")
######################################


# Get all DMS IPs and push them simultaneously
# solution for status ??
def get_dmsIPs(activeRegionNames, dynamoDBTableName, clientDynamo):
    for regionName in activeRegionNames:
        clientMQ = boto3.client('dms', region_name=regionName)
        response = clientMQ.describe_replication_instances()
        dmsList = response['ReplicationInstances']

        # Skip the region if no DMS found
        if len(dmsList) == 0:
            continue

        dateTime = response['ResponseMetadata']['HTTPHeaders']['date'].split()
        epochTime = datetimeToepochtime(dateTime)

        for dms in dmsList:
            status = True
            # if elb['State']['Code'] == 'active':
            #     status = True
            if dms['PubliclyAccessible'] == True:
                dmsIPs = dms['ReplicationInstancePublicIpAddresses']
                for dmsIP in dmsIPs:
                    Item={
                        "EIP": {
                            'S': str(dmsIP),
                        },
                        "Time of scan": {
                            'S': str(epochTime)
                        },
                        "Region": {
                            'S': str(regionName)
                        },
                        "Account ID": {
                            'S': str(accountID)
                        },
                        "Active": {
                            'BOOL': status
                        },
                        "AWS Service": {
                            'S': "DMS"
                        }
                    }
                    response = clientDynamo.put_item(
                        TableName=dynamoDBTableName,
                        Item = Item
                    )   
    return("DMS done")
######################################


# Get all RDS IPs and push them simultaneously
# solution for status ??
def get_rdsIPs(activeRegionNames, dynamoDBTableName, clientDynamo):
    for regionName in activeRegionNames:
        clientRDS = boto3.client('rds', region_name=regionName)
        response = clientRDS.describe_db_instances()
        dbList = response['DBInstances']

        # Skip the region if no DMS found
        if len(dbList) == 0:
            continue

        dateTime = response['ResponseMetadata']['HTTPHeaders']['date'].split()
        epochTime = datetimeToepochtime(dateTime)

        for db in dbList:
            if db['PubliclyAccessible'] == True and db['DBInstanceStatus'] == 'available': # need to check for modifying if required ??
                dbEndpoint = db['Endpoint']['Address']
                dbIPs = socket.gethostbyname_ex(dbEndpoint)[-1]
                status = True
                # if elb['State']['Code'] == 'active':
                #     status = True
                for dbIP in dbIPs:
                    Item={
                        "EIP": {
                            'S': str(dbIP),
                        },
                        "Time of scan": {
                            'S': str(epochTime)
                        },
                        "Region": {
                            'S': str(regionName)
                        },
                        "Account ID": {
                            'S': str(accountID)
                        },
                        "Active": {
                            'BOOL': status
                        },
                        "AWS Service": {
                            'S': "RDS"
                        }
                    }
                    response = clientDynamo.put_item(
                        TableName=dynamoDBTableName,
                        Item = Item
                    )
    return("RDS done")