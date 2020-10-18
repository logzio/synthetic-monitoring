# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:2.0-python3.7-appservice
FROM mcr.microsoft.com/azure-functions/python:2.0-python3.7

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY requirements.txt /
RUN pip install -r /requirements.txt
RUN apt-get update
RUN apt-get install -y chromium chromium-l10n
RUN apt-get install --only-upgrade chromium
RUN curl https://raw.githubusercontent.com/logzio/public-certificates/master/AAACertificateServices.crt --create-dirs -o /etc/pki/tls/certs/COMODORSADomainValidationSecureServerCA.crt
RUN curl https://raw.githubusercontent.com/logzio/public-certificates/master/AAACertificateServices.crt --create-dirs -o /etc/ssl/certs/COMODORSADomainValidationSecureServerCA.crt

COPY . /home/site/wwwroot