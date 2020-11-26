# pukpuk

    ░▒▓ pukpuk ▓▒░ HTTP services discovery toolkit

## About

Pukpuk ("pook-pook") is a tool for discovering and monitoring HTTP services. It simply grabs screens and responses, and stores them in a directory. It is especially useful in the initial phase of any assignment to find vulnerable Web applications, forgotten devices, directories listing source code or backups. Results are easily greppable. When monitoring, a good practice is to store the results in a repository so it is easier to track changes. Apart from port scanning `pukpuk` also does reverse DNS lookup and certificate parsing. Quite often certificates reveal extra virtual hosts or domain names.

## Requirements

* Python 3.x
* Chrome / Chromium for screen grabbing functionality

## Usage

### Default OS nameserver, using `chromium` and default ports (80/http, 443/https)

    pukpuk -c 10.0.0.0/24

### Custom nameserver and ports, using `chrome.exe`

    pukpuk -c 10.0.0.0/24 -r 84.200.69.80 -e chrome.exe -p 80/http 443/https 8000/http 8443/https

### Use IP list instead of CIDR notation

    pukpuk -l hosts.txt

### Or skip the discovery phase and provide a CSV file (format: 192.168.1.1,443,https)

    pukpuk -i targets.csv

## Installation

### From sources

    $ git clone https://github.com/tasooshi/pukpuk.git
    $ cd pukpuk
    $ pip3 install .

### Using PyPI

    $ pip3 install pukpuk

## Troubleshooting

### libgcc_s.so.1 must be installed for pthread_cancel to work

    $ LD_PRELOAD=libgcc_s.so.1 pukpuk

## Usage

```
usage: pukpuk [-h] (-c DISCOVERY_CIDR | -l DISCOVERY_LIST | -i INPUT_LIST) [-o OUTPUT_DIRECTORY] [-d] [-e EXECUTABLE] [-p PORTS [PORTS ...]] [-pt PROCESS_TIMEOUT] [-r RESOLVER] [-st SOCKET_TIMEOUT] [-x SOCKS5_PROXY] [-ua USER_AGENT] [-v] [-w WORKERS]

HTTP screen grabber and response dumper

optional arguments:
  -h, --help            show this help message and exit
  -c DISCOVERY_CIDR, --discovery-cidr DISCOVERY_CIDR
                        Discovery mode, accepts CIDR notation, e.g. "10.0.0.0/24"
  -l DISCOVERY_LIST, --discovery-list DISCOVERY_LIST
                        Discovery mode, accepts file input, one IP address per line
  -i INPUT_LIST, --input-list INPUT_LIST
                        Skips discovery, accepts file input, CSV format: [address],[port],[protocol], e.g. "192.168.1.1,443,https"
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Path where results (text files, images) will be stored (default: 20200101_2000.pukpuk)
  -d, --debug
  -e EXECUTABLE, --executable EXECUTABLE
                        Browser binary path for headless screen grabbing (default: chromium)
  -p PORTS [PORTS ...], --ports PORTS [PORTS ...]
                        Port list for HTTP service discovery (default: 80/http, 443/https)
  -pt PROCESS_TIMEOUT, --process-timeout PROCESS_TIMEOUT
                        Process timeout in seconds (default: 10)
  -r RESOLVER, --resolver RESOLVER
                        DNS server (default: 10.10.0.1)
  -st SOCKET_TIMEOUT, --socket-timeout SOCKET_TIMEOUT
                        Socket timeout in seconds (default: 3)
  -x SOCKS5_PROXY, --socks5-proxy SOCKS5_PROXY
                        Socks5 proxy, e.g. "127.0.0.1:1080
  -ua USER_AGENT, --user-agent USER_AGENT
                        Browser User-Agent header (default: python-requests/2.25.0)
  -v, --version         show program's version number and exit
  -w WORKERS, --workers WORKERS
                        Number of concurrent workers (default: 6)
```

## Changelog

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