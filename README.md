![version](https://img.shields.io/pypi/v/pukpuk) ![pyversions](https://img.shields.io/pypi/pyversions/pukpuk) ![license](https://img.shields.io/pypi/l/pukpuk) ![status](https://img.shields.io/pypi/status/pukpuk)

# pukpuk

> HTTP discovery and change monitoring tool

## About

Pukpuk ("pook-pook") is a simple utility that stores screenshots and HTTP responses for a given network range or URLs. It does so by looking for open ports, parsing certificates and performing reverse DNS lookups.

## Requirements

* Python 3.9, 3.10
* `chromium` (for screen grabbing functionality)

## Basic Usage

### Scan network 10.0.0.0/24 using default ports

    $ pukpuk -N 10.0.0.0/24

### Scan network 10.0.0.0/24 and examine ports 80/http, 443/https and 8443/?

    $ pukpuk -N 10.0.0.0/24 -p 80/http 443/https 8443

### Skip discovery and load URLs from a file

    $ pukpuk -T hosts.txt

## Installation

### Using PyPI

    $ pip3 install pukpuk

## Troubleshooting

### libgcc_s.so.1 must be installed for pthread_cancel to work

    $ LD_PRELOAD=libgcc_s.so.1 pukpuk

### Doesn't discover ports that exist for sure

In case of larger scans and possibility of dealing with a firewall experiment with increasing `--socket-timeout`, using less `--workers`, splitting the scan into smaller parts using text file input or give randomization a chance.

## CLI

```
usage: pukpuk [-h] (-N NETWORK | -T TARGETS) [-p PORTS] [-b BROWSER] [-n NAMESERVER] [-r] [-o OUTPUT_DIR] [-x SOCKS_PROXY] [-u USER_AGENT] [-w WORKERS] [--process-timeout PROCESS_TIMEOUT] [--socket-timeout SOCKET_TIMEOUT] [-v] [-d | -q]

HTTP discovery and change monitoring tool

options:
  -h, --help            show this help message and exit
  -N NETWORK, --network NETWORK
                        Discovery mode, accepts network in CIDR notation, e.g. "10.0.0.0/24"
  -T TARGETS, --targets TARGETS
                        Skip discovery, load URLs from a file
  -p PORTS, --ports PORTS
                        Port list for HTTP service discovery [Default: 80/http, 443/https]
  -b BROWSER, --browser BROWSER
                        Chromium browser path for headless screen grabbing [Default: chromium]
  -n NAMESERVER, --nameserver NAMESERVER
                        DNS server [Default: system defaults]
  -r, --randomize       Randomize scanning order
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Path where results (text files, images) will be stored [Default: YYYYMMDD_HHMM.pukpuk]
  -x SOCKS_PROXY, --socks-proxy SOCKS_PROXY
                        Socks5 proxy, e.g. "127.0.0.1:1080"
  -u USER_AGENT, --user-agent USER_AGENT
                        Browser User-Agent header [Default: python-requests/2.28.1]
  -w WORKERS, --workers WORKERS
                        Number of concurrent workers [Default: 25]
  --process-timeout PROCESS_TIMEOUT
                        Process timeout in seconds [Default: 12]
  --socket-timeout SOCKET_TIMEOUT
                        Socket timeout in seconds [Default: 3]
  -v, --version         Print version
  -d, --debug
  -q, --quiet
```

## Changelog

### 3.0.0 (2022-07-22)

* Major refactoring and backward incompatible changes
* Improved test suite

### 2.0.6 (2022-06-22)

* Updated requirements

### 2.0.5 (2022-03-23)

* Updated requirements

### 2.0.4 (2022-01-13)

* Updated dependency (Pillow)
* Changed licensing

### 2.0.3 (2021-11-24)

* Updated dependency (Pillow)
* Minor refactoring

### 2.0.2 (2021-07-30)

* Updated dependency (Pillow)

### 2.0.1 (2021-03-31)

* Updated dependency (Pillow)

### 2.0.0 (2021-01-26)

* Major refactoring
* Updated requirements
* [NEW] Simplified CLI
* [NEW] Configuration file support
* [NEW] HTTP(S) can be omitted, falls back to protocol discovery
* [NEW] Randomization
* [NEW] Timeouts now in floats
* [NEW] Unit tests
* [FIXED] Grabbing screenshots with self-signed certificates
* [FIXED] Memory usage

### 1.1.1 (2020-11-26)

* Hotfix

### 1.1 (2020-11-26)

* Added support for SOCKS5 proxying

### 1.0 (2020-11-25)

* Updated Python requirements
* Removed timestamps from file names, no longer needed and makes it easier to diff and track with source versioning
* Strip whitespaces when loading CSV files
* Results now end up in separate subdirectories named after modules
* FIXED: Issue with loading from CSV files

### 0.5 (2020-09-20)

* CSV input and discovery phase skipping
* Minor improvements in logging and storing results

### 0.4 (2020-09-14)

* Simplified usage: removed option to launch selected modules since there are only two for now
* Creates directory for storing results by default
* Saves logging output by default
* Less detailed logging at info level
* Adjusted default timeouts
* Added usage examples

### 0.3 (2020-07-22)

* Graceful exit, cancelling steps
* Remove blank screenshots
* Added timestamp to default logging level

### 0.2 (2020-07-13)

* Initial commit