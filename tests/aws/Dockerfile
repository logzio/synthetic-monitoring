FROM lambci/lambda:python3.7

USER root

ENV AWS_LAMBDA_FUNCTION_NAME aws-test

ENV AWS_LAMBDA_FUNCTION_MEMORY_SIZE 512

ENV AWS_LAMBDA_FUNCTION_TIMEOUT 420

ENV AWS_REGION us-east-1

COPY ./aws/lambda_function.py /var/task/

COPY ./*.py /var/task/

RUN yum install -y wget \
    && yum install unzip \
    && wget https://logzio-sm-us-east-1.s3.amazonaws.com/python.zip \
    && wget https://logzio-sm-us-east-1.s3.amazonaws.com/bin.zip \
    && unzip python.zip \
    && unzip bin.zip \
    && mv python /opt \
    && mv bin /opt \
    && rm python.zip \
    && rm bin.zip

CMD ["lambda_function.lambda_handler"]
