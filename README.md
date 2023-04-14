# 使用Python Boto3从CloudWatch获取S3存储桶大小的Metric值

## 一、背景

对象式存储S3是用于存储海量文件的，当文件达到百万、千万、上亿的时候，S3可正常响应查询、写入的请求，而普通OS上的文件系统在这个数量级必须引入目录散列，并且伴随着性能下降，且如果是虚拟机本地盘还可能出现inodes使用满的情况。这种场景下，S3对象存储针对海量文件是非常友好的。因此使用S3是很有必要的。

S3也有不方便的地方，例如统计文件大小。传统的文件系统方式是做遍历后求和。那么S3上数百万个文件做一次遍历，开销极其巨大，而且产生了巨大的读取费用（List也算读取，参考S3收费文档）。由此，S3有个功能是S3 Inventory，即每天一次生成文件清单，并可通过Athena做进一步查询文件名称和大小。此外，还可以通过S3 Storage Lens查看各存储桶的总数据量和类型。

如果只希望看到存储桶体积，并且还需要通过API能获取，那么可以查询CloudWatch Metrics的S3类型，即可看到本存储桶名称对应的多种存储级别的容量。不过需要注意的是，此数据存在一定的延迟，需要以天为颗粒度查看，不像其他EC2、RDS等监控参数可以调整到60秒的颗粒度。如下截图。

![](https://blogimg.bitipcman.com/workshop/S3-BucketSize/BucketSize01.png)

在以上CloudWatch界面可以做求和运算，生成本存储桶所有类型的总容量。那么如何将这一数据从API上获取呢？

## 二、使用Python代码获取S3存储桶容量

请注意本机需要事先安装好AWSCLI并配置正确的Access Key/Secret Key（简称AKSK），这样即可无需在代码中显式声明密钥。如果是在AWS云上环境运行这段代码，还可以通过IAM Role授权策略实现免密钥访问。

构建代码如下。

```
import boto3
import datetime
import time

# 请注意S3 Bucket所在的对应region
bucketname="mybucketname"

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
        totalsize = totalsize +size1
        # 输出信息
        print(storage_type_list.ljust(30) + str(size1).rjust(25))

    print("---------------------------------------------------------")
    print("Total Size (GB) = ".rjust(50) + str(totalsize))

getBucketSizeForAllStorageType(bucketname)
```

请注意Python代码需要严格的缩进，复制时候注意格式不要乱掉。运行以上代码，返回结果如下截图。

![](https://blogimg.bitipcman.com/workshop/S3-BucketSize/BucketSize02.png)

由此即可获取S3存储桶容量。

## 三、参考文档

Boto3 1.26.113 documentation - get_metric_statistics

[https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch/client/get_metric_statistics.html]()

Github: adaam/cloudwatch_s3_size.py

[https://gist.github.com/adaam/9df974a081253efd9db22bf06d997b00]()