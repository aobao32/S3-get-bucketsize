import boto3
import datetime
import time
import json

cloudwatch = boto3.client('cloudwatch')

# 请注意S3 Bucket所在的对应region
bucketName="lxy-sa-software"

now = datetime.datetime.now()
start_time = (now-datetime.timedelta(days=2)).isoformat()
end_time = (now-datetime.timedelta(days=1)).isoformat()

# 取回本存储桶有效的存储类型列表
def getStorageType(bucket):
    response = cloudwatch.list_metrics(
        Namespace = 'AWS/S3',
        MetricName = 'BucketSizeBytes',
        Dimensions = [
                        {
                            'Name': 'BucketName',
                            'Value': bucket
                        }                       
                    ] 
        )
    namespaces = response['Metrics']
    storageTypeList = []
    for dimension in namespaces:
        storageTypeList.append(dimension['Dimensions'][0]['Value'])
    return(storageTypeList)

# 分别获取各存储类型大小
def getSizeForEachType(bucket):
    output = []
    output1 = []
    # 取回本存储桶在使用的类型
    storageTypeList = getStorageType(bucket)
    for storage in storageTypeList:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='BucketSizeBytes',
            Dimensions=[
                            {
                                'Name': 'StorageType',
                                'Value': storage
                            },
                            {
                                'Name': 'BucketName',
                                'Value': bucket
                            }                       
                        ],   
            StartTime = start_time,
            EndTime = end_time,
            Period = 3600,
            Statistics=[
                'Maximum',
            ],
            Unit='Bytes'
            )
        size=round(response['Datapoints'][0]['Maximum']/1000/1000/1000,2)
        output = { 'type': storage , 'size': size}
        output1.append(output)

    return(json.dumps(output1))

def getBucketSizeForAllStorageType(bucket):
    # CloudWatch的BucketSize存在以天为单位的延迟，因此取前2天的数据
    # 打印列首信息
    print("---------------------------------------------------------")
    print("Bucket Name :  " + bucket)
    print("Date of Metric : " + time.strftime('%Y-%m-%d'))
    print('S3 Storage Type'.ljust(30) + 'Size in GB'.rjust(25))
    print("---------------------------------------------------------")
    
    # 取回多个存储类型
    response1 = cloudwatch.list_metrics(
        Namespace = 'AWS/S3',
        MetricName = 'BucketSizeBytes',
        Dimensions = [
                        {
                            'Name': 'BucketName',
                            'Value': bucket
                        }                       
                    ] 
        )
    namespaces = response1['Metrics']
    
    # 分别针对上一步查询到的多个存储类型，获取存储桶大小
    totalsize = 0
    for dimension in namespaces:
        storage_type_list = dimension['Dimensions'][0]['Value']
        response2 = cloudwatch.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='BucketSizeBytes',
            Dimensions=[
                            {
                                'Name': 'StorageType',
                                'Value': storage_type_list
                            },
                            {
                                'Name': 'BucketName',
                                'Value': bucket
                            }                       
                        ],   
            StartTime = start_time,
            EndTime = end_time,
            Period = 3600,
            Statistics=[
                'Maximum',
            ],
            Unit='Bytes'
            )
        size1=round(response2['Datapoints'][0]['Maximum']/1000/1000/1000,2)
        totalsize = totalsize + size1
        # 输出信息
        print(storage_type_list.ljust(30) + str(size1).rjust(25))

    print("---------------------------------------------------------")
    print("Total Size (GB) = ".rjust(50) + str(totalsize))


if __name__ == '__main__':
    getBucketSizeForAllStorageType(bucketName)