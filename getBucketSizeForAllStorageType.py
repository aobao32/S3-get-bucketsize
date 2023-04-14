import boto3
import datetime
import time

# 请注意S3 Bucket所在的对应region
bucketname="lxy-sa-software"

def getBucketSizeForAllStorageType(bucketname):
    # CloudWatch的BucketSize存在以天为单位的延迟，因此取前2天的数据
    now = datetime.datetime.now()
    start_time = (now-datetime.timedelta(days=2)).isoformat()
    end_time = (now-datetime.timedelta(days=1)).isoformat()
    
    # 打印列首信息
    print("---------------------------------------------------------")
    print("Bucket Name :  " + bucketname)
    print("Date of Metric : " + time.strftime('%Y-%m-%d'))
    print('S3 Storage Type'.ljust(30) + 'Size in GB'.rjust(25))
    print("---------------------------------------------------------")
    
    cloudwatch = boto3.client('cloudwatch')
    # 取回多个存储类型
    response1 = cloudwatch.list_metrics(
        Namespace = 'AWS/S3',
        MetricName = 'BucketSizeBytes',
        Dimensions = [
                        {
                            'Name': 'BucketName',
                            'Value': bucketname
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
                                'Value': bucketname
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

getBucketSizeForAllStorageType(bucketname)