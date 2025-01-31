![version](https://img.shields.io/pypi/v/pukpuk) ![pyversions](https://img.shields.io/pypi/pyversions/pukpuk) ![license](https://img.shields.io/pypi/l/pukpuk) ![status](https://img.shields.io/pypi/status/pukpuk)

# pukpuk

> HTTP discovery and change monitoring tool

## About

Pukpuk ("pook-pook") is a simple utility that stores screenshots and HTTP responses for a given network range or URLs. It does so by looking for open ports, parsing certificates and performing reverse DNS lookups.

## Requirements

* Python 3.11, 3.12
* `chromium` (for screen grabbing functionality)

## Basic Usage

### Scan CIDR network using default ports

    $ pukpuk -N 10.0.0.0/24

### Scan IP range and examine ports 80/http, 443/https and 8443 (auto-detect)

    $ pukpuk -N 10.0.1.1-10.0.2.15 -p 80/http,443/https,8443

### Skip discovery and load URLs from a file

    $ pukpuk -U urls.txt

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
usage: pukpuk [-h] [-N NETWORK] [-H HOSTS] [-U URLS] [-p PORTS] [-b BROWSER] [-r] [-o OUTPUT_DIR] [-u USER_AGENT] [-w WORKERS] [--process-timeout PROCESS_TIMEOUT] [--socket-timeout SOCKET_TIMEOUT] [--skip-screens] [--grabbing-attempts GRABBING_ATTEMPTS] [-v] [-d | -q]

HTTP discovery and change monitoring tool

options:
  -h, --help            show this help message and exit
  -N NETWORK, --network NETWORK
                        Accepts network in CIDR notation or an IP range and performs discovery using ports in `-p`, e.g. "10.0.0.0/24", "10.0.1.1-10.2.1.1"
  -H HOSTS, --hosts HOSTS
                        Loads hosts from a file and performs discovery using ports in `-p`
  -U URLS, --urls URLS  Loads specific URLs from a file, skips discovery and ignores the `-p` argument for these
  -p PORTS, --ports PORTS
                        Comma separated port list for HTTP service discovery [Default: 80/http, 443/https]
  -b BROWSER, --browser BROWSER
                        Chromium browser path for headless screen grabbing [Default: chromium]
  -r, --randomize       Randomize scanning order
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Path where results (text files, images) will be stored [Default: YYYYMMDD_HHMM.pukpuk]
  -u USER_AGENT, --user-agent USER_AGENT
                        Browser User-Agent header [Default: python-requests/2.28.1]
  -w WORKERS, --workers WORKERS
                        Number of concurrent workers [Default: 15]
  --process-timeout PROCESS_TIMEOUT
                        Process timeout in seconds [Default: 20]
  --socket-timeout SOCKET_TIMEOUT
                        Socket timeout in seconds [Default: 3]
  --skip-screens        Skip screen grabbing
  --grabbing-attempts GRABBING_ATTEMPTS
                        Number of screen grabbing attempts [Default: 3]
  -v, --version         Print version
  -d, --debug
  -q, --quiet
```

## Changelog

### 3.2.1 (2025-01-31)

* Switched to modern packaging.
* Updated dependencies.
* Print help when no arguments.
* Tests and minor fixes.

### 3.2.0 (2022-08-05)

* Improved screen capturing.
* [NEW] CLI arguments changed, it is now possible to use multiple sources for targets, i.e. mix network range, list of URLs, hosts in a file.
* [NEW] Several screen grabbing attempts (added argument) and a longer process timeout by default. Works better.
* [NEW] If paths are provided in the URLs file, they will be hashed with md5 when saving output.
* [NEW] HTTP request headers included with each individual file.

### 3.1.1 (2022-07-23)

* Fixed regression
* Tested with Python 3.8

### 3.1.0 (2022-07-23)

* Removed unreliable proxy support
* Removed misleading `nameserver` option
* Better error handling
* Logging to file
* [NEW] Added option for skipping screenshots
* [NEW] Saving targeted URLs
* [NEW] Support for IP ranges

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
