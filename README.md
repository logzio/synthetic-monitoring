# LightS

LightS is a lightweight web monitoring solution to check availability and load performance of your web site. <br>
LightS uses a simple script based on Python 3.7 and Selenium. You can easily deploy it to your account on the supported cloud platforms. <br>


## Supported platforms:
* [AWS](https://github.com/logzio/synthetic-monitoring/blob/master/aws/README.md)

## Versions

| LightS | Selenium | Requests | Chromium | Chromedriver |
|---|---|---|---|---|
| 0.0.1 | 3.14.0 | 2.24.0 | 86.0.4240.0 | 86.0.4240.22.0 |

## Notes
* If your web page is blocking automated scripts, LightS will not be able to monitor it properly.


### Change log:
* **0.0.2** - Supports monitoring multiple urls.
* **0.0.1** - Initial release

#### Acknowledgments
Special thanks for [@vittorio-nardone](https://github.com/vittorio-nardone) for his excellent [repo](https://github.com/vittorio-nardone/selenium-chromium-lambda).
