import os
import json
import boto3
import requests
import datetime

LOGZIO_LISTENER = os.getenv("LOGZIO_CUSTOM_LISTENER", "listener.logz.io")
LOGZIO_METRICS_TOKEN = os.environ["LOGZIO_METRICS_TOKEN"]
LOGZIO_LOGS_TOKEN = os.environ["LOGZIO_LOGS_TOKEN"]
LOGZIO_REGION = os.environ["LOGZIO_REGION"]
SCRAPE_INTERVAL = os.environ["SCRAPE_INTERVAL"]
REGIONS = list(os.environ["REGIONS"].replace(' ', '').split(","))
PROTOCOL = os.getenv("PROTOCOL", "https")
URL = os.environ["URL"]
responseStatus = 'SUCCESS'


def _format_url(url):
    f_url = url.replace('.', '')
    f_url = f_url.replace('://', '')
    return f_url


URL_LABEL = _format_url(URL)


def _send_log(message):
    timestamp = _format_timestamp(datetime.datetime.now(tz=datetime.timezone.utc))
    log = {"@timestamp": timestamp, "message": message, "type": "synthetic-monitoring"}
    _send_data(json.dumps(log), is_metrics=False)


def _send_data(data, is_metrics=True):
    try:
        port = _get_port_by_protocol()
        token = LOGZIO_METRICS_TOKEN if is_metrics else LOGZIO_LOGS_TOKEN
        url = "{}://{}:{}/?token={}".format(PROTOCOL, LOGZIO_LISTENER, port, token)
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


def _format_timestamp(timestamp):
    return "{}Z".format(timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])


def _deploy_stack(region):
    try:
        _send_log("Starting to deploy cloudformation stack to {} region".format(region))
        client = boto3.client('cloudformation', region_name=region)
        response = client.create_stack(
            StackName='logzio-sm-{}-{}'.format(region, URL_LABEL),
            TemplateURL='https://sm-template.s3.amazonaws.com/sm-stack-{}.yaml'.format(region),
            Parameters=[
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
    print('RESPONSE BODY:n' + responseBody)

    return responseBody


def lambda_handler(event, context):
    try:
        for region in REGIONS:
            _deploy_stack(region)
    except Exception as e:
        _send_log("Error while creating cloudformation stacks. message: {}".format(e))

    try:
        req = requests.put(event['ResponseURL'], data=getResponse(event, context, responseStatus))
        if req.status_code != 200:
            print(req.text)
            raise Exception('Received non 200 response while sending response to CFN.')
    except requests.exceptions.RequestException as e:
        _send_log(e)
        raise
    return
    print("COMPLETE")
