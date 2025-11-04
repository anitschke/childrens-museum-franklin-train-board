# childrens-museum-franklin-train-board

xxx add background

xxx add animation of train here

xxx add recording of display

xxx link to https://github.com/anitschke/childrens-museum-franklin-train-board-data-analysis

## Maxtrix Portal Setup

### Flash with CircuitPython

The [instructions on setting up the Matrix Portal S3](https://learn.adafruit.com/adafruit-matrixportal-s3/install-circuitpython) that state you can just drag and drop the circuit python `.u2` file onto the `MATRXS3BOOT` drive don't seem to work correctly. However I was able to install it using the web installer on
* https://circuitpython.org/board/adafruit_matrixportal_s3/
* "Open Installer"
* "Install CircuitPython 10.0.0 UF2 Only"
* Continue following install instructions

Currently using `adafruit-circuitpython-matrixportal_m4-en_US-10.0.0`

### Install Adafruit Library

After setting up CircuitPython we need to install the Adafruit python libraries onto the device. This can be done by running the `install_circuitpython_lib.sh` script. This script installs EVERYTHING from that python bundle. There is a lot more than we need in that lib, but it is only 1MB so it isn't worth it to figure out what we do/don't need.

### `settings.toml`

A `settings.toml` must be created inside this directory containing secrets and API keys. It will be copied over to the device when `install.sh` is run in the next step.

* `CIRCUITPY_WIFI_SSID` and `CIRCUITPY_WIFI_PASSWORD` need to contain the wifi SSID and password so the board can connect to wifi
* `CIRCUITPY_WEB_API_PASSWORD` should be set to a strong random password. This password can be used to connect remotely to the CircuitPython web server to make live changes to the board.
* `ADAFRUIT_AIO_USERNAME` and `ADAFRUIT_AIO_KEY` are required so it can push logs to the adafruit.io log feed and connect to the adafruit.io NTP time server so it can fetch the current time. A free account can be created at io.adafruit.com . xxx instructions on creating a feed

xxx doc
```toml
CIRCUITPY_WIFI_SSID = "REDACTED"
CIRCUITPY_WIFI_PASSWORD = "REDACTED"
CIRCUITPY_WEB_API_PASSWORD = "REDACTED"
CIRCUITPY_WEB_API_PORT = 80
ADAFRUIT_AIO_USERNAME = "REDACTED"
ADAFRUIT_AIO_KEY      = "REDACTED"
```
### Install the program

Run `install.sh` to install all of the 

## Notes

### dependency injection

xxx comments on how I am doing dependency injection and how that makes it easier to test

### `main.py` vs `code.py`

Most circuit python codebases seem to use `code.py` for the main entrypoint file, however circuit python also accept `main.py` as the main entrypoint file. We use `main.py` because VSCode test plugin hits the following error if we attempt to run tests and `code.py` exists. So we will just work around this and name the entry point file `main.py` instead.

```
Traceback (most recent call last):
  File "/home/anitschk/.vscode/extensions/ms-python.python-2025.16.0-linux-x64/python_files/unittestadapter/execution.py", line 24, in <module>
    from django_handler import django_execution_runner  # noqa: E402
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/anitschk/.vscode/extensions/ms-python.python-2025.16.0-linux-x64/python_files/unittestadapter/django_handler.py", line 15, in <module>
    from pvsc_utils import (  # noqa: E402
        VSCodeUnittestError,
    )
  File "/home/anitschk/.vscode/extensions/ms-python.python-2025.16.0-linux-x64/python_files/unittestadapter/pvsc_utils.py", line 6, in <module>
    import doctest
  File "/usr/lib/python3.13/doctest.py", line 101, in <module>
    import pdb
  File "/usr/lib/python3.13/pdb.py", line 77, in <module>
    import code
  File "/home/anitschk/sandbox/childrens-museum-franklin-train-board/code.py", line 4, in <module>
    import microcontroller
ModuleNotFoundError: No module named 'microcontroller'
Finished running tests!
```


### Read Only Filesystem

xxx

https://github.com/adafruit/circuitpython/issues/9528#issuecomment-2293527157

xxx then reinstall

## References
* https://github.com/alejandrorascovan/mta-portal
* https://jegamboafuentes.medium.com/i-created-my-own-subway-arrival-board-with-real-time-data-to-dont-miss-my-train-anymore-28bfded312c0
* https://www.mbta.com/developers/v3-api
* https://github.com/jegamboafuentes/Train_schedule_board
* https://docs.circuitpython.org/projects/matrixportal/en/latest/
