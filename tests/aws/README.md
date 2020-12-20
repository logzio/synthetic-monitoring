## Developing and testing with lambda docker image

the `lambda-lights` docker image is an image for simulating the AWS Lambda environment, for local development and testing.
<br> All `.py` files located in `/var/task`.
<br> All imported modules for this project located in `/opt/python`.
<br> All binaries for this project located in `/opt/bin`.
This image is based on `lambci/docker-lambda` docker image. See the project's [repo](https://github.com/lambci/docker-lambda) for further information.

### How to use the image

#### 1. Pull the Docker image
Download the `lambda-lights` image from docker hub:

```shell
docker pull logzio/lambda-lights
```

#### 2. Set your directories
If you wish to run your work in the docker container, make sure that you have a folder that contains the following files:
* lambda_function.py
* lights.py
* input_validator.py
* sys_region_adapter.py

#### 3. Run the container
```shell
docker run  \
--env LOGZIO_METRICS_TOKEN=<<METRICS-TOKEN>> \
--env LOGZIO_LOGS_TOKEN=<<LOGS-TOKEN>> \
--env URL=<<URLS-TO-MONITOR>> \
-v path/to/dir/with/files/from/step2:/var/task \
logzio/lambda-lights
```

#### Environment variables:
| Variable | Description |
| --- | --- |
| `LOGZIO_METRICS_TOKEN` | **Required**. Your logzio metrics account token. |
| `LOGZIO_LOGS_TOKEN` | **Required**. Your logzio logs account token. |
| `URL` | **Required**. A comma-separated list of the urls you'd want to monitor. |
| `LOGZIO_REGION` | `Default: us`. Your Logz.io region code. For example if your region is US, then your region code is `us`. You can find your region code here: https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls for further information. |
| `AWS_LAMBDA_FUNCTION_NAME`| `Default: aws-test`. <br>Your test lambda function name. |
| `AWS_LAMBDA_FUNCTION_MEMORY_SIZE` | `Default: 512`. Your function's memory size (in MB). |
| `AWS_LAMBDA_FUNCTION_TIMEOUT` | `Default: 420`. Your function timeout (in seconds). |
| `AWS_REGION` | `Default: us-east-1`. The AWS region you'd want to test from. |
