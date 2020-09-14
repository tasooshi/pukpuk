# pukpuk

    ░▒▓ pukpuk ▓▒░ HTTP services discovery toolkit

## Functionality

* Screen and HTTP response grabber
* Reverse DNS lookup and certificate parsing

## Installation

### From sources

    $ git clone https://github.com/tasooshi/pukpuk.git
    $ cd pukpuk
    $ pip3 install .

### Using PyPI

    $ pip3 install pukpuk

## How it works

* For a given IP address (e.g. 10.10.10.1) and selected ports (e.g. 80/http 443/https) create a list of URLs:
    * http://10.10.10.1:80/
    * http://10.10.10.1:443/
    * http://example.com:80/
    * https://example.com:443/
* Next, for each of these URLs:
    * Dump HTTP response headers (`pukpuk.mods.response`)
    * Grab the screen using Chromium/Chrome (`pukpuk.mods.grabber`)
* Save output to a directory

## Usage

### Default OS nameserver, using `chromium` and default ports (80/http, 443/https) by default

    pukpuk -c 10.0.0.0/24

### Custom nameserver and ports, using `chrome.exe`

    pukpuk -c 10.0.0.0/24 -r 84.200.69.80 -e chrome.exe -p 80/http 443/https 8000/http 8443/https

### Use IP list instead of CIDR notation

    pukpuk -l hosts.txt

## Requirements

* Python 3.x
* Chrome / Chromium for screen grabbing functionality

## Changelog

### 0.4

* Simplified usage: removed option to launch selected modules since there are only two for now
* Creates directory for storing results by default
* Saves logging output by default
* Less detailed logging at info level
* Adjusted default timeouts
* Added usage examples

### 0.3

* Graceful exit, cancelling steps
* Remove blank screenshots
* Added timestamp to default logging level

### 0.2

* Initial commit