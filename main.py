import csv
import os
import sys
from argparse import ArgumentParser

import requests
import validators
from tqdm import tqdm


# Add arguments to script
ap = ArgumentParser()

ap.add_argument('-f', '--file', required=True, help='Path to CSV File')
ap.add_argument('-n', '--name', required=True,
                help='Name of GitHub Organization')
ap.add_argument('-t', '--token', required=True, help='Github Access Token')

# Create dictionary from args
args = vars(ap.parse_args())

# Define Constants
GITHUB_USERNAME_INDEX = 14
ORG_NAME = args['name']
FILE = args['file']
ACCESS_TOKEN = args['token']
AUTH_HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
BASE_API_ENDPOINT = 'https://api.github.com'

# Ensure file path is valid
if not os.path.exists(FILE):
    print(f'Invalid File Path: {FILE}')
    sys.exit(1)

# Ensure organization exists
try:
    res = requests.get(
        f'{BASE_API_ENDPOINT}/orgs/{ORG_NAME}', headers=AUTH_HEADERS)

    if res.status_code == 404:
        print(f'Invalid Org Name: {ORG_NAME}')
        sys.exit(1)

except requests.exceptions.HTTPError as e:
    print('Something Went Wrong')
    sys.exit(1)

# Ensure token is valid
try:
    res = requests.get(
        f'{BASE_API_ENDPOINT}/orgs/{ORG_NAME}/invitations', headers=AUTH_HEADERS)

    if res.status_code == 401:
        print(f'Invalid Access Token: {ACCESS_TOKEN}')
        sys.exit(1)

except requests.exceptions.HTTPError as e:
    print('Something Went Wrong')
    sys.exit(1)

# Parse CSV file
with open(FILE) as f:

    reader = csv.reader(f, quotechar='"', delimiter=',')

    # Skip headers
    next(reader)

    # Gather unique usernames to consider resubmissions and clean data
    usernames = set()

    for row in reader:
        username = row[GITHUB_USERNAME_INDEX].strip()

        if validators.url(username):
            username = username.split('/')[-1]

        elif username.startswith('@'):
            username = username[1:]

        usernames.add(username)

    unknown_usernames = []
    user_ids = []

    print('Retrieving User Ids...')
    for username in tqdm(usernames):
        res = requests.get(
            f'{BASE_API_ENDPOINT}/users/{username}', headers=AUTH_HEADERS)
        if res.status_code == 404:
            unknown_usernames.append(username)
        else:
            json_data = res.json()
            user_id = json_data['id']
            user_ids.append(user_id)

    if len(unknown_usernames) > 0:
        print(f'Ivalid Username(s):', unknown_usernames)
        sys.exit(1)

    print('Sending Invitations...')
    for user_id in tqdm(user_ids):
        payload = {'invitee_id': user_id, "role": "direct_member"}
        # POST to GitHub API
        res = requests.post(
            f'{BASE_API_ENDPOINT}/orgs/{ORG_NAME}/invitations', headers=AUTH_HEADERS, json=payload)

print('All done! :)')
