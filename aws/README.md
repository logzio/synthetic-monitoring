# LightS

LightS is a web monitoring solution to check availability and load performance of your web site. <br>
**This solution will be deployed on your AWS account.**

#### Configuration

<div class="tasklist">

##### Create Task


To start just press the button and follow the instructions:

[![Deploy to AWS](https://dytvr9ot2sszz.cloudfront.net/logz-docs/lights/LightS-button.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/template?templateURL=https://sm-template.s3.amazonaws.com/0.0.2/auto-deployment.yaml&stackName=logzio-sm-auto-deployment)

You'll be taken to AWS, where you'll configure the resources to be deployed.
Keep the defaults and click Next on the following screen

![Customized template](https://dytvr9ot2sszz.cloudfront.net/logz-docs/lights/lights-create-stack.png)

##### Specify stack details

![Customized template](https://dytvr9ot2sszz.cloudfront.net/logz-docs/lights/lights-params-12182020.png)

| Parameter | Description |
|---|---|
| logzioLogsToken | Token for shipping logs to your Logz.io account. |
| logzioMetricsToken | Token for shipping metrics to your Logz.io account. |
| logzioURL | (optional) Set a custom URL to ship metrics & logs to (e.g., http://localhost:9200). This overrides the region_code configurationfor further information. |
| logzioRegion | Your Logz.io region code. For example if your region is US, then your region code is `us`. You can find your region code here: https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls for further information. |
| regions | A comma separated list of AWS regions for deployment, (example: us-east-1,ap-south-1). |
| scrapeInterval | Cloudwatch events rate schedule Expression (in minutes). See https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html#RateExpressions. |
| urls | A comma-delimited list of the URLs you want to monitor. For example : https://www.logz.io,https://example.com |
| memory | `Default: 512 (MB)`. The memory size you want to assign to the lambda function that runs LightS. <br> Note that the more URLs you choose to monitor, the more memory you'll need. These default settings are just a starting point. Check your Lambda usage regularly, and adjust that value if you need to. <br> 512 MB is the minimum size we recommend. |

and click Next

##### Configure stack

On the following page fill Tags to easily identified your Lambda function and press Next
![Customized template](https://dytvr9ot2sszz.cloudfront.net/logz-docs/lights/lights-stack-options.png)


###### Confirm IAM Role permissions and create the stack

AWS will automatically show a notice requesting that you acknowledge that AWS CloudFormation might create IAM resources.

![AWS IAM Role notice](https://dytvr9ot2sszz.cloudfront.net/logz-docs/lights/LightS-IAM-role-notice.png)

Check the box to acknowledge this option and click **Create stack**.

This Deploymet will create the following resources in your AWS account:
#### Global (us-east-1):
| Logical ID | Resource type |
|---|---|
| LogzioAutoDeploymentFunction | AWS::Lambda::Function |
| LogzioSyntheticMonitoringBinLayer | AWS::Lambda::LayerVersion |
| LogzioSyntheticMonitoringPythonLayer | AWS::Lambda::LayerVersion |
| LogzioInvoke | AWS::CloudFormation::CustomResource |
| LogzioLambdaExecutionRole | AWS::IAM::Role |
#### In every region specified in `regions` parameter:
| Logical ID | Resource type |
|---|---|
| LogzioSyntheticMonitoringFunction | AWS::Lambda::Function |
| LogzioSyntheticMonitoringBinLayer | AWS::Lambda::LayerVersion |
| LogzioSyntheticMonitoringPythonLayer | AWS::Lambda::LayerVersion |
| LogzioPermissionForEventsToInvokeLambda | AWS::Lambda::Permission |
| LogzioLambdaExecutionRole | AWS::IAM::Role |
| LogzioScheduledRule | AWS::Events::Rule |

##### Open your Synthetic Monitoring dashboard in Logz.io

Give your metrics some time to get from your system to ours, and then open [Logz.io Metrics](https://app.logz.io/#/dashboard/grafana/).

Your metrics should appear in the preconfigured dashboard in your Metrics account. Use the Synthetic Monitoring Dashboard to monitor your website performance and availability via Logz.io.

</div>

#### Important notes:
* The lambda function will be deployed to **your** AWS account.
* Due to setup and initialization, the lambda function's first run may take longer than usual.



