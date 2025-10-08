# childrens-museum-franklin-train-board





## Maxtrix Portal Setup

### Flash with CircuitPython

The [instructions on setting up the Matrix Portal S3](https://learn.adafruit.com/adafruit-matrixportal-s3/install-circuitpython) that state you can just drag and drop the circuit python `.u2` file onto the `MATRXS3BOOT` drive don't seem to work correctly. However I was able to install it using the web installer on
* https://circuitpython.org/board/adafruit_matrixportal_s3/
* "Open Installer"
* "Install CircuitPython 10.0.0 UF2 Only"
* Continue following install instructions

Currently using `adafruit-circuitpython-matrixportal_m4-en_US-10.0.0`

### Install Adafruit Library
Downloaded 10.x bundle from https://circuitpython.org/libraries and just installed entire `lib` directory from the bundle into the `lib` directory on the device. There is a lot more in that lib that we don't need but it is only 1MB so it isn't worth it to figure out what we do/don't need.

Documentation: https://docs.circuitpython.org/projects/matrixportal/en/latest/

Currently using `adafruit-circuitpython-bundle-10.x-mpy-20251004`

### `settings.toml`

A `settings.toml` must be created at the root directory containing secrets and API keys.

* `CIRCUITPY_WIFI_SSID` and `CIRCUITPY_WIFI_PASSWORD` need to contain the wifi SSID and password so the board can connect to wifi
* `CIRCUITPY_WEB_API_PASSWORD` should be set to a strong random password. This password can be used to connect remotely to the CircuitPython web server to make live changes to the board.
* `ADAFRUIT_AIO_USERNAME` and `ADAFRUIT_AIO_KEY` are required so it can connect to the Adafruit NTP time server so it can fetch the current time. A free account can be created at io.adafruit.com .

xxx doc
```toml
CIRCUITPY_WIFI_SSID = "REDACTED"
CIRCUITPY_WIFI_PASSWORD = "REDACTED"
CIRCUITPY_WEB_API_PASSWORD = "REDACTED"
CIRCUITPY_WEB_API_PORT = 80
ADAFRUIT_AIO_USERNAME = "REDACTED"
ADAFRUIT_AIO_KEY      = "REDACTED"
```

## References
* https://github.com/alejandrorascovan/mta-portal
* https://jegamboafuentes.medium.com/i-created-my-own-subway-arrival-board-with-real-time-data-to-dont-miss-my-train-anymore-28bfded312c0
* https://www.mbta.com/developers/v3-api
* https://github.com/jegamboafuentes/Train_schedule_board
* https://docs.circuitpython.org/projects/matrixportal/en/latest/
