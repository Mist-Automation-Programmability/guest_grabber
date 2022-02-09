#!/bin/python3

########################################################################################################################
# Guest Grabber - Get historical authorized guests 0from a specified Mist org via API
#
# This work is licensed under the Mozilla Public License 2.0
########################################################################################################################
# Author: Ryan M. Adzima & Jake Snyder
# Copyright: Copyright 2021, Juniper Networks & Ryan M. Adzima
# License: MIT
# Version: 1.0.0
# Maintainer: Ryan M. Adzima & Jake Snyder
# Email: radzima@juniper.net
# Status: Best-effort
########################################################################################################################





import sys
from datetime import datetime, timezone
import csv
from pprint import pprint
import requests
import logging
import json

OUTPUT_PATH = "./guests.csv"                                    # Change this to the location to write the new CSV file (relative or absolute)
TIME_FORMAT = "%I:%M:%S %m-%d-%Y"                               # Datetime format, change to your preference

# TODO: Create CLI flags and/or config file methods to avoid hard-coding tokens and UUIDs
API_TOKEN = "YOUR API TOKEN HERE"          # https://api.mist.com/api/v1/self/apitokens
ORG_ID = "YOUR ORG_ID HERE"                                                                         # Org ID to get sites *** NOT IMPLEMENTED YET ***
ENV = "api.mist.com"


### DON'T CHANGE THE VALUES BELOW UNLESS ABSOLUTELY NECCESSARY ###

HEADERS = {                                                     # HTTP headers for interacting with the Mist API
    "Authorization": f"Token {API_TOKEN}",                      # API token converted to an authorization header
    "Content-type": "application/json"                          # Specify the content type (JSON) just in case
}


class MistCredentials(object):

    def __init__(self, org_id: str, apitoken: str, env: str = "api.mist.com"):
        self.org_id = org_id
        self.apitoken = apitoken
        self.env = env


class MistOrg(object):

    def __init__(self, creds: MistCredentials):
        import requests
        self.org_id = creds.org_id
        self.apitoken = creds.apitoken
        self.host = creds.env

    def check_authentication(self):
        import requests
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/self"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True
        else:
            logging.error(f"Auth Failed: {response.text}")
            return False

    def get_sites(self):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/orgs/{self.org_id}/sites"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.sites = response.json()
            return response.json()
        else:
            return None

    def search_site_switchports(self, site_id):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/stats/ports/search"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def search_site_guest_authorizations(self, site_id, duration="7d", limit=1000, wlan=False):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/guests/search?duration={duration}&limit={limit}"
        if wlan != False:
            url = url + f"&wlan={wlan}"
        results = []
        response = requests.get(url, headers=headers)
        results = results + response.json()['results']
        while "next" in response.json():
            url = f"https://{self.host}{response.json()['next']}"
            response = requests.get(url, headers=headers)
            results = results + response.json()['results']
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def get_org_inventory(self, device_type: str = ""):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/orgs/{self.org_id}/inventory?type={device_type}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.sites = response.json()
            return response.json()
        else:
            return None

    def get_org_stats(self):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/orgs/{self.org_id}/stats"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.sites = response.json()
            return response.json()
        else:
            return None

    def get_device_stats(self, device_id, site_id):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/stats/devices/{device_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.sites = response.json()
            return response.json()
        else:
            return None

    def get_site_webhooks(self, site_id: str):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/webhooks"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def get_site_insight_metric(self, site_id, scope, scope_id, metric):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/insights/{scope}/{scope_id}/{metric}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def get_device_switchport_stats(self, site_id, mac):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/stats/switch_ports/search?mac={mac}"
        results = []
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = results + response.json()['results']
            while "next" in response.json():
                url = f"https://{self.host}{response.json()['next']}"
                response = requests.get(url, headers=headers)
                results = results + response.json()['results']
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def search_device_switchport_search(self, site_id):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/stats/switch_ports/search"
        results = []
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = results + response.json()['results']
            while "next" in response.json():
                url = f"https://{self.host}{response.json()['next']}"
                response = requests.get(url, headers=headers)
                results = results + response.json()['results']
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def get_org_network_templates(self):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/orgs/{self.org_id}/networktemplates"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def get_site_setting(self, site_id):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/setting"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def get_site_info(self, site_id):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def get_site_maps(self, site_id):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/maps"
        response = requests.get(url, headers=headers)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def get_site_map(self, site_id, map_id):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/maps/{map_id}"
        response = requests.get(url, headers=headers)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def get_site_devices(self, site_id):
        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = f"https://{self.host}/api/v1/sites/{site_id}/devices"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def upload_site_map_image(self, site_id, map_id, filename):
        headers = {"Authorization": f"token {self.apitoken}", 'Accept': 'application/json'}
        url = f"https://{self.host}/api/v1/sites/{site_id}/maps/{map_id}/image"
        #payload = {'json': '{}'}
        files = [
            ('file', (str(filename),
                      open(filename, 'rb'), 'image/png'))
        ]
        response = requests.post(url, headers=headers, files=files)
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None

    def clone_site_map(self, site_id: str, map_data: dict):
        import copy
        import shutil

        headers = {"Content-Type": "application/json", "Authorization": f"token {self.apitoken}"}
        url = url = f"https://{self.host}/api/v1/sites/{site_id}/maps"
        data = copy.deepcopy(map_data)
        for item in ['id', 'site_id', 'org_id', 'created_time', 'modified_time', 'url', 'thumbnail_url']:
            data.pop(item)
        image_response = requests.get(map_data['url'], stream=True)
        image_response.raw.decode = True
        image_data = image_response.raw
        image_name = map_data['url'].split("/")[-1].split('?')[0]
        with open(image_name, 'wb') as f:
            shutil.copyfileobj(image_response.raw, f)
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            new_map_data = response.json()
            map_upload = self.upload_site_map_image(site_id, new_map_data['id'], image_name)
            if map_upload is not None:
                final_response = self.get_site_map(site_id, new_map_data['id'])
                return final_response
            else:
                print(f"URL: {url}")
                print(f"Response Code: {response.status_code}")
                print(response.text)
                return None
        else:
            print(f"URL: {url}")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            return None


def write_guests(guest_list: list, output: str):
    """
    Writes guest data to the file specified in the 'OUTPUT_PATH' variable

    :param str output: Location where the new CSV file should be written (relative or absolute)
    :param list guest_list: List containing the formatted guest data
    """
    cols = []
    for guest in guest_list:
        for key in guest.keys():
            if key not in cols:
                cols.append(key)
    #cols = ["Name", "Email", "Auth Time", "Expire Time", "Client MAC", "SSID", "AP Name", "AP MAC"]
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


def ap_name_from_mac(auth: dict, inventory: list) -> str:
    """
    Retrieves the name of the AP based on the provided MAC address to make the CSV more human-readable

    :param dict auth: guest authorization
    :param list inventory: Mist AP inventory output
    :return dict: authorization with ap_name added.
    """
    mac = auth.get('ap', None)
    devices = []
    if mac is not None:
        devices = [device['name'] for device in inventory if device['mac'] == mac]
    if len(devices) == 1:
        auth['ap_name'] = devices[0]
    return auth



def time_update(auth):
    auth["Auth Time"] = datetime.utcfromtimestamp(auth['authorized_time']).replace(tzinfo=timezone.utc).astimezone(
        tz=None).strftime(TIME_FORMAT)
    auth["Expire Time"] = datetime.utcfromtimestamp(auth['authorized_expiring_time']).replace(tzinfo=timezone.utc).astimezone(
        tz=None).strftime(TIME_FORMAT)
    return auth

def guest_grabber():
    """
    Main worker function for guest grabber script
    """
    my_creds = MistCredentials(org_id=ORG_ID, apitoken=API_TOKEN, env=ENV)
    my_org = MistOrg(my_creds)
    inventory = my_org.get_org_inventory()
    try:
        # TODO: Be less ugly at providing feedback to the user
        site_data = my_org.get_sites()
        guest_data = []
        for site in site_data:
            guest_auths = my_org.search_site_guest_authorizations(site['id'])['results']
            guest_data = guest_data + guest_auths

        guest_data = [ap_name_from_mac(auth, inventory) for auth in guest_data]
        guest_data = [time_update(auth) for auth in guest_data]

        print("Guest Data")
        pprint(guest_data)

        #guests_data = get_guest_logins(site_id=ORG_ID)
        #print(f"Got {len(guests_data)} records.")
        #print("Formatting guest data...")
        #guests_formatted = format_guests(guest_list=guests_data, site_id=SITE_ID)
        #print(f"Formatted {len(guests_formatted)} records.")
        #print(f"Writing data to CSV file {OUTPUT_PATH}...")
        write_guests(guest_list=guest_data, output=OUTPUT_PATH)
        #print(f"Wrote CSV file to {OUTPUT_PATH}.")
    except KeyboardInterrupt:
        print("User cancelled, exiting.")
    print("Done.")
    sys.exit(0)


if __name__ == '__main__':
    guest_grabber()
