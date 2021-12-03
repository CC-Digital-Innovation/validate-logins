# Automated Login Valitdation

This program automatically validates ServiceNow CMDB stored credentials based on the type of access method used. This can be further automated on a weekly (or however long) basis using [Ofelia](https://github.com/mcuadros/ofelia).

## Table of Contents
* [The Details](#the-details)
* [Getting Started](#getting-started)
    * [ServiceNow Requirements](#servicenow-requirements)
    * [Local Requirements](#local-requirements)
    * [Installation](#installation)
    * [Usage](#usage)
* [TODOs](#todos)
* [Author](#author)
* [License](#license)

## The Details

The program collects all active devices from a company in ServiceNow via API and attempts to verify the credentials depending on the primary/secondary access method used. A custom REST API is used to decrypt the passwords. A report will be sent via email of all the validation results.

* SSH
    * Package [paramiko](https://github.com/paramiko/paramiko) is used with a simple connect method to validate.
* RDP
    * Package [pywinrm](https://github.com/diyan/pywinrm) is used to validate credentials. WinRM is required on Window hosts for the validation to work. Check out the requirements below.

## Getting Started

### ServiceNow Requirements

Records and the fields required:

* Devices(cmdb_ci) - Company`[R]`, Status(install_status), Primary Access Method(u_primary_acces_method), Secondary Access Method(u_secondary_access_method), Username, Password(u_fs_password), Port(u_port)
    * _`core_company` a referenced field used for filtering_
    * _`install_status` is a type used to filter installed/active devices_
    * _`u_fs_password` is a password2 type field that can be decrypted_
    * _`u_port` is used for custom ports for the specified primary access method. If none, default port is used, i.e. SSH:22, RDP:3389...
 
 In order to check credentials, an API to decrypt u_fs_password is required.

### Local Requirements

* WinRM Setup
    * For validating RDP, Window hosts (not the machine running this program) must have WinRM set up with at least the quick configuration for HTTP. Check notes [here](https://www.evernote.com/shard/s3/client/snv?noteGuid=737221c7-57fc-6052-0de4-c903fbe9db48&noteKey=375d96c1dc6e4f92fc9a2bea3d485bd6&sn=https%3A%2F%2Fwww.evernote.com%2Fshard%2Fs3%2Fsh%2F737221c7-57fc-6052-0de4-c903fbe9db48%2F375d96c1dc6e4f92fc9a2bea3d485bd6&title=Windows%2BService%2Band%2BAuth%2BValidation).

* Docker
    * _Note: Developed using Docker version 20.10.8, but was not tested with any other version._

If docker is not desired, the program can be run standalone but will require python and the required modules. Note the container uses Python 3.8.12 but was not tested with any other version.

### Installation

Download code from GitHub:

```bash
git clone https://github.com/CC-Digital-Innovation/reconcile-snow-prtg.git
```

* or download the [zip](https://github.com/CC-Digital-Innovation/reconcile-snow-prtg/archive/refs/heads/main.zip)

### Usage

_The code snippets assume you are user in docker group which does not require sudo. If you are not, each command will require sudo prefixed._

* Edit the config.ini.example file and rename (remove .example).
* Build the image:
```bash
docker build -t validate-login .
```
* Start the container:
```bash
docker run --name test-login validate-login
```
* To have a recurring check, [Ofelia](https://github.com/mcuadros/ofelia) can be used to schedule the job.

## TODOs
* Validate HTTP/HTTPS
* Create incident for each invalid credential and add incident link to report.

## Author
* Jonny Le <<jonny.le@computacenter.com>>

## License
MIT License

Copyright (c) 2021 Computacenter Digital Innovation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.