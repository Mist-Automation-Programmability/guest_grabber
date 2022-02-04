#!/bin/python3

########################################################################################################################
# Guest Grabber - Get all currently authorized guest accounts from a specified Mist site via API
#
# This work is licensed under the Mozilla Public License 2.0
########################################################################################################################
# Author: Ryan M. Adzima
# Copyright: Copyright 2021, Juniper Networks & Ryan M. Adzima
# License: MPL-2.0
# Version: 1.0.0
# Maintainer: Ryan M. Adzima
# Email: radzima@juniper.net
# Status: Best-effort
########################################################################################################################

import sys
from string import Template
import requests
from datetime import datetime, timezone
import csv

OUTPUT_PATH = "./guests.csv"                                    # Change this to the location to write the new CSV file (relative or absolute)
TIME_FORMAT = "%I:%M:%S %m-%d-%Y"                               # Datetime format, change to your preference

BASE_URL = Template("https://api.mist.com/api/v1/$endpoint")    # AWS, change accordingly if needed

# TODO: Create CLI flags and/or config file methods to avoid hard-coding tokens and UUIDs
API_TOKEN = "YOUR TOKEN HERE"                                   # https://api.mist.com/api/v1/self/apitokens
SITE_ID = "YOUR SITE ID HERE"                                   # Site ID to get guest logins from
ORG_ID = "YOUR ORG ID HERE"                                     # Org ID to get sites *** NOT IMPLEMENTED YET ***


### DON'T CHANGE THE VALUES BELOW UNLESS ABSOLUTELY NECCESSARY ###

DEVICE_ID_BASE = Template("00000000-0000-0000-1000-$mac")       # Hardcoded formatting laziness
HEADERS = {                                                     # HTTP headers for interacting with the Mist API
    "Authorization": f"Token {API_TOKEN}",                      # API token converted to an authorization header
    "Content-type": "application/json"                          # Specify the content type (JSON) just in case
}


def write_guests(guest_list: list, output: str):
    """
    Writes guest data to the file specified in the 'OUTPUT_PATH' variable

    :param str output: Location where the new CSV file should be written (relative or absolute)
    :param list guest_list: List containing the formatted guest data
    """
    cols = ["Name", "Email", "Auth Time", "Expire Time", "Client MAC", "SSID", "AP Name", "AP MAC"]
    try:
        with open(output, 'w') as guest_csv:
            writer = csv.DictWriter(guest_csv, fieldnames=cols, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(guest_list)
    except csv.Error as e:
        print(f"CSV library exception while attempting to write CSV file: {e}")
        raise e
    except (FileExistsError, FileNotFoundError, IOError) as e:
        print(f"Filesystem or IO exception while attempting to write CSV data to output file '{output}': {e}")
        raise e
    except (OSError, SystemError) as e:
        print(f"System exception while attempting to write CSV file: {e}")
        raise e
    except Exception as e:
        print(f"Unknown exception while attempting to write CSV file: {e}")
        raise e


def ap_name_from_mac(mac_address: str, site_id: str) -> str:
    """
    Retrieves the name of the AP based on the provided MAC address to make the CSV more human-readable

    :param str mac_address: AP MAC address
    :param str site_id: The ID of the site where the AP is configured
    :return str: The AP name as a string
    """
    device_id = DEVICE_ID_BASE.substitute(mac=mac_address)
    url = BASE_URL.substitute(endpoint=f"sites/{site_id}/devices/{device_id}")
    try:
        res = requests.get(url=url, headers=HEADERS)
        d = res.json()
    except Exception as e:
        print(f"Failed to get AP name from the Mist API: {e}")
        raise e
    return d['name']


def format_guests(guest_list: list, site_id: str) -> list:
    """
    Format the raw guest data into human-readable columns and dates

    :param list guest_list: A list of dicts containing the raw guest data from the Mist API
    :param str site_id: The ID of the site the guest and AP are located
    :return list: A formatted list of dicts to be written to CSV
    """
    formatted_guest_list = list()
    try:
        for guest in guest_list:
            try:
                g = {
                    "AP Name": ap_name_from_mac(mac_address=guest['ap_mac'], site_id=site_id),
                    "AP MAC": guest['ap_mac'],
                    "Auth Time": datetime.utcfromtimestamp(guest['authorized_time']).replace(tzinfo=timezone.utc).astimezone(tz=None).strftime(TIME_FORMAT),
                    "Expire Time": datetime.utcfromtimestamp(guest['authorized_expiring_time']).replace(tzinfo=timezone.utc).astimezone(tz=None).strftime(TIME_FORMAT),
                    "Name": guest.get('name', None),
                    "Email": guest.get('email', None),
                    "Client MAC": guest['mac'],
                    "SSID": guest['ssid']
                }
                formatted_guest_list.append(g)
            except KeyError as e:
                print(f"Missing key in guest data for MAC address '{guest['mac']}': {e}")
                print("Skipping item and continuing...")
                pass
            except ValueError as e:
                print(f"Error reading guest data for MAC address '{guest['mac']}': {e}")
                print("Skipping item and continuing...")
                pass
            except Exception as e:
                print(f"Unknown exception formatting guest data for MAC address '{guest['mac']}': {e}")
                print("Skipping item and continuing...")
                pass
    except Exception as e:
        print(f"Error formatting guest data: {e}")
        print("Raising exception and exiting...")
        raise e
    return formatted_guest_list


def get_guest_logins(site_id: str) -> list:
    """
    Get the authorized guest accounts from the Mist API

    :param str site_id: The ID of the site to get guest data from
    :return list: A list of dicts containing the raw guest data from the Mist API
    """
    url = BASE_URL.substitute(endpoint=f"sites/{site_id}/guests")
    try:
        res = requests.get(url=url, headers=HEADERS)
        g = res.json()
    except Exception as e:
        print(f"Failed to retrieve guest data from the Mist API: {e}")
        raise e
    return g


# TODO: Multi-site and entire organization based guest retrieval
def get_sites_from_org(org_id: str) -> list:
    """
    Retrieve a list of sites from the Mist API

    *** NOT YET IMPLEMENTED ***

    :param str org_id: The ID of the organization to pull a list of sites from
    :return list: A list of dicts containing the sites within a Mist organization
    """
    url = BASE_URL.substitute(endpoint=f"orgs/{org_id}/sites")
    try:
        res = requests.get(url=url, headers=HEADERS)
        s = res.json()
    except Exception as e:
        print(f"Failed to retrieve sites from the Mist API: {e}")
        raise e
    return s


def guest_grabber():
    """
    Main worker function for guest grabber script
    """
    # TODO: Create an option to start with an org_id and iterate each site to create an individual CSV for each
    try:
        # TODO: Be less ugly at providing feedback to the user
        print("Getting guests...")
        guests_data = get_guest_logins(site_id=SITE_ID)
        print(f"Got {len(guests_data)} records.")
        print("Formatting guest data...")
        guests_formatted = format_guests(guest_list=guests_data, site_id=SITE_ID)
        print(f"Formatted {len(guests_formatted)} records.")
        print(f"Writing data to CSV file {OUTPUT_PATH}...")
        write_guests(guest_list=guests_formatted, output=OUTPUT_PATH)
        print(f"Wrote CSV file to {OUTPUT_PATH}.")
    except KeyboardInterrupt:
        print("User cancelled, exiting.")
    print("Done.")
    sys.exit(0)


if __name__ == '__main__':
    guest_grabber()
