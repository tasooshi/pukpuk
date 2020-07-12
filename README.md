# pukpuk

    ░▒▓ pukpuk ▓▒░ HTTP discovery toolkit

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
    * Dump HTTP response headers (`-m pukpuk.mods.response`)
    * Grab the screen using Chromium/Chrome (`-m pukpuk.mods.grabber`)
* Save output to current directory

## Usage

### HTTP response only, default OS nameserver, using `chromium` by default

    pukpuk -c 10.0.0.0/24 -p 80/http 443/https 8000/http 8443/https

### Custom nameserver, using `chrome.exe`

    pukpuk -c 10.0.0.0/24 -r 84.200.69.80 -m pukpuk.mods.response pukpuk.mods.grabber -e chrome.exe -p 80/http 443/https 8000/http 8443/https

### Use IP list instead of CIDR notation

    pukpuk -l hosts.txt -p 80/http 443/https

## Requirements

* Chrome / Chromium for screen grabbing functionality

## Planned features

* Checking for vulnerabilities
* Concurrency improvements
* Password bruteforcing
* Database storage
