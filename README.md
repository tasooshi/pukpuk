# pukpuk

> HTTP discovery and change monitoring tool

## About

Pukpuk ("pook-pook") is a tool for discovering and monitoring HTTP services. It simply grabs screens and responses, and stores them in a directory (new features may be added in the future). It is especially useful in the initial phase of any assignment to find vulnerable Web applications, forgotten devices, directories listing source code or backups. Results are easily greppable. When monitoring, a good practice is to store the results in a repository so it is easier to track changes. Apart from port scanning `pukpuk` also does reverse DNS lookup and certificate parsing. Quite often certificates reveal extra virtual hosts or domain names.

## Requirements

* Python 3.x
* Chrome / Chromium for screen grabbing functionality

## Usage

### Default OS nameserver, using `chromium` and default ports (80/http, 443/https)

    $ pukpuk -n 10.0.0.0/24

### Custom nameserver and ports, using `chrome.exe`

    $ pukpuk -n 10.0.0.0/24 -d 84.200.69.80 -b chrome.exe -p 80/http 443/https 8000 8443

### Use IP list instead of CIDR notation

    $ pukpuk -l hosts.txt

### Or skip the discovery phase and provide a CSV file (format: 192.168.1.1,443,https)

    $ pukpuk -t targets.csv

### Combined with nmap ping sweep to speed up host discovery

    $ nmap -n -sn 10.0.1.0/24 -oG hosts.gnmap

    $ cat hosts.gnmap | grep Status | cut -d" " -f2 > hosts.txt

    $ pukpuk -c pukpuk.conf -l hosts.txt

## Installation

### Using PyPI

    $ pip3 install pukpuk

### From sources

    $ git clone https://github.com/tasooshi/pukpuk.git
    $ cd pukpuk
    $ pip3 install .

## Configuration file example

`pukpuk.conf`

```
[DEFAULT]
browser = chrome
modules = pukpuk.mods.response,pukpuk.mods.grabber
output_directory = pukpuk-tmp
ports = 8000,8080,8443/https,9443/https
process_timeout = 15
nameserver = 192.168.100.1
socket_timeout = 2
user_agent = Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
workers = 8
```

`pukpuk-fast.conf`

```
[DEFAULT]
workers = 8
socket_timeout = 0.8
process_timeout = 10
ports = 80,81,82,443,4443,8000,8001,8002,8008,8080,8088,8888,8443,9443
```

## Troubleshooting

### libgcc_s.so.1 must be installed for pthread_cancel to work

    $ LD_PRELOAD=libgcc_s.so.1 pukpuk

### Doesn't discover ports that exist for sure

In case of larger scans and possibility of dealing with a firewall experiment with increasing `socket_timeout`, using less `workers`, splitting the scan into smaller parts using text file input or give randomization a chance.

## CLI

```
usage: pukpuk [-h] (-n NETWORK | -l HOSTS | -t TARGETS) [-c CONFIG] [-o OUTPUT_DIRECTORY] [-b BROWSER] [-p PORTS [PORTS ...]] [-m MODULES [MODULES ...]] [-d NAMESERVER] [-x SOCKS5_PROXY] [-u USER_AGENT] [-v] [-w WORKERS]
              [--process-timeout PROCESS_TIMEOUT] [--socket-timeout SOCKET_TIMEOUT] [-d]

HTTP discovery and change monitoring tool

optional arguments:
  -h, --help            show this help message and exit
  -n NETWORK, --network NETWORK
                        Discovery mode, accepts network in CIDR notation, e.g. "10.0.0.0/24"
  -l HOSTS, --hosts HOSTS
                        Discovery mode, accepts hosts list as a file, one IP address per line
  -t TARGETS, --targets TARGETS
                        Skips discovery, accepts targets as a file, CSV format: [address],[port],[?protocol], e.g. "192.168.1.1,443,https" or "192.168.1.1,443,"
  -c CONFIG, --config CONFIG
                        Configuration file path, overrides command line arguments and defaults (default: pukpuk.conf)
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Path where results (text files, images) will be stored (default: 20200101_2000.pukpuk)
  -b BROWSER, --browser BROWSER
                        Browser binary path for headless screen grabbing (default: chromium)
  -p PORTS [PORTS ...], --ports PORTS [PORTS ...]
                        Port list for HTTP service discovery (default: 80/http, 8000/http, 8080/http, 443/https, 8443/https)
  -m MODULES [MODULES ...], --modules MODULES [MODULES ...]
                        List of modules to be executed (default: pukpuk.mods.response, pukpuk.mods.grabber)
  -d NAMESERVER, --nameserver NAMESERVER
                        DNS server (default: 127.0.0.1)
  -x SOCKS5_PROXY, --socks5-proxy SOCKS5_PROXY
                        Socks5 proxy, e.g. "127.0.0.1:1080
  -u USER_AGENT, --user-agent USER_AGENT
                        Browser User-Agent header (default: python-requests/2.25.0)
  -v, --version         show program's version number and exit
  -w WORKERS, --workers WORKERS
                        Number of concurrent workers (default: 6)
  -r, --randomize       Randomize scanning order
  --process-timeout PROCESS_TIMEOUT
                        Process timeout in seconds (default: 12.5)
  --socket-timeout SOCKET_TIMEOUT
                        Socket timeout in seconds (default: 2.5)
  -d, --debug
```

## Changelog

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