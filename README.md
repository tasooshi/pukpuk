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

## Changelog

### 1.1

* Added support for SOCKS5 proxying

### 1.0

* Updated Python requirements
* Removed timestamps from file names, no longer needed and makes it easier to diff and track with source versioning
* Strip whitespaces when loading CSV files
* Results now end up in separate subdirectories named after modules
* FIXED: Issue with loading from CSV files

### 0.5

* CSV input and discovery phase skipping
* Minor improvements in logging and storing results

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