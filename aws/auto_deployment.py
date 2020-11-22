import os
import json
import boto3
import time
import requests
import datetime
import sys
sys.path.append(".")
import input_validator


MAX_DOM_COMPLETE = os.getenv("DOM_COMPLETE", "")
LOGZIO_CUSTOM_LISTENER = os.environ["LOGZIO_CUSTOM_LISTENER"]
LOGZIO_METRICS_TOKEN = os.environ["LOGZIO_METRICS_TOKEN"]
LOGZIO_LOGS_TOKEN = os.environ["LOGZIO_LOGS_TOKEN"]
LOGZIO_REGION = os.environ["LOGZIO_REGION"]
SCRAPE_INTERVAL = os.environ["SCRAPE_INTERVAL"]
REGIONS = list(os.environ["REGIONS"].replace(' ', '').split(","))
PROTOCOL = os.getenv("PROTOCOL", "https")
STACK_NAME=os.environ["STACK_NAME"]
URL = os.environ["URL"]
responseStatus = 'SUCCESS'

# input validations
input_validator.is_valid_logzio_token(LOGZIO_METRICS_TOKEN)
input_validator.is_valid_logzio_token(LOGZIO_LOGS_TOKEN)
input_validator.has_region_or_listener(LOGZIO_CUSTOM_LISTENER,LOGZIO_REGION)
input_validator.is_valid_logzio_region_code(LOGZIO_REGION)
for region in REGIONS:
    input_validator.is_valid_system_region("aws",region)
input_validator.is_valid_url(URL)
input_validator.is_valid_function_name(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
MAX_DOM_COMPLETE = input_validator.validate_max_dom_complete(MAX_DOM_COMPLETE,5)
input_validator.validate_aws_scrape_interval(SCRAPE_INTERVAL)



if LOGZIO_CUSTOM_LISTENER == "":
    if LOGZIO_REGION == "" or LOGZIO_REGION == "us":
        LOGZIO_LISTENER = "https://listener.logz.io:8071"
    else:
        LOGZIO_LISTENER = "https://listener-{}.logz.io:8071".format(LOGZIO_REGION)
else:
    LOGZIO_LISTENER = LOGZIO_CUSTOM_LISTENER

# _format_url removes unvalid characters for deployed stack name
def _format_url(url):
    f_url = url.replace('.', '')
    f_url = f_url.replace('://', '')
    return f_url


URL_LABEL = _format_url(URL)

# __send_log sends log to your logz.io account
def _send_log(message):
    timestamp = _format_timestamp(datetime.datetime.now(tz=datetime.timezone.utc))
    log = {"@timestamp": timestamp, "message": message, "type": "synthetic-monitoring"}
    _send_data(json.dumps(log), is_metrics=False)

 # __send_data sends over HTTPS either a log or a metric to your logz.io account,
# based on the token 
def _send_data(data, is_metrics=True):
    try:
        port = _get_port_by_protocol()
        token = LOGZIO_METRICS_TOKEN if is_metrics else LOGZIO_LOGS_TOKEN
        url = "{}/?token={}".format(LOGZIO_LISTENER, token)
        response = requests.post(url, data=data)
        if not response.ok:
            # TODO
            pass
    except Exception as e:
        # TODO
        pass


def _get_port_by_protocol():
    if PROTOCOL == "https":
        return "8071"
    else:
        return "8070"

# __format_timestamp formats a timestamp to logz.io's acceptable timestamp format 'yyyy-MM-ddTHH:mm:ss.SSSZ'
def _format_timestamp(timestamp):
    return "{}Z".format(timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])

# _deploy_stack uses boto3 libarary to deploy cloudforamtion stacks across all regions specified in `regions` parameter 
def _deploy_stack(region):
    try:
        _send_log("Starting to deploy cloudformation stack to {} region".format(region))
        client = boto3.client('cloudformation', region_name=region)
        response = client.create_stack(
            StackName='logzio-sm-{}-{}'.format(region, URL_LABEL),
            TemplateURL='https://sm-template.s3.amazonaws.com/sm-stack-{}.yaml'.format(region),
            Parameters=[
                {
                    'ParameterKey': 'domComplete',
                    'ParameterValue': MAX_DOM_COMPLETE,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'logzioURL',
                    'ParameterValue': LOGZIO_LISTENER,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'scrapeInterval',
                    'ParameterValue': SCRAPE_INTERVAL,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'logzioRegion',
                    'ParameterValue': LOGZIO_REGION,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'url',
                    'ParameterValue': URL,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'logzioMetricsToken',
                    'ParameterValue': LOGZIO_METRICS_TOKEN,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'logzioLogsToken',
                    'ParameterValue': LOGZIO_LOGS_TOKEN,
                    'UsePreviousValue': False,
                },
                {
                    'ParameterKey': 'shippingProtocol',
                    'ParameterValue': PROTOCOL,
                    'UsePreviousValue': False,
                }
            ],
            Capabilities=[
                'CAPABILITY_IAM'
            ]

        )
        _send_log(json.dumps(response))
    except Exception as e:
        _send_log("Error while creating cloudformation stack at {} region. message: {}".format(region, e))
        pass


def getResponse(event, context, responseStatus):
    responseBody = {'Status': responseStatus,
                    'PhysicalResourceId': context.log_stream_name,
                    'StackId': event['StackId'],
                    'RequestId': event['RequestId'],
                    'LogicalResourceId': event['LogicalResourceId'],
                    }
    responseBody = json.dumps(responseBody)

    return responseBody


def lambda_handler(event, context):
    try:
        for region in REGIONS:
            _deploy_stack(region)
    except Exception as e:
        _send_log("Error while creating cloudformation stacks. message: {}".format(e))
        
    time.sleep(240)
    try:
        _send_log("Starting to delete {} cloudformation stack".format(STACK_NAME))
        client = boto3.client('cloudformation', region_name="us-east-1")
        response = client.delete_stack(StackName=STACK_NAME)
        _send_log(json.dumps(response))
    except Exception as e:
        _send_log("Error while deleting {} cloudformation stack. message: {}".format(STACK_NAME,e))

    try:
        req = requests.put(event['ResponseURL'], data=getResponse(event, context, responseStatus))
        if req.status_code != 200:
            _send_log(req.text)
            raise Exception('Received non 200 response while sending response to CFN.')
    except requests.exceptions.RequestException as e:
        _send_log(e)
        raise
    return
