# Guest Grabber

Get all currently authorized guest accounts from a specified Mist site via API

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square)](https://www.python.org/)

## Installation

This script was tested using Python 3.9.0 but _should_ run just fine on 3.6.x. You should update just in case.

Clone this repo and then install the dependencies listed in the `requirements.txt` file using package manager [pip](https://pip.pypa.io/en/stable/).

```bash
pip install -r requirements.txt
```

Then set the required configuration values in `guest_grabber.py`.

The required values are:
- `API_TOKEN` - Create API token from /api/v1/self/apitokens or /api/v1/orgs/:org_id/apitokens to generate a token if you do not already have one
- `ORG_ID` - The Organization ID for the org 



## Usage

From a terminal, simply run the script by entering the command below.
```bash
python guest_grabber.py
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

