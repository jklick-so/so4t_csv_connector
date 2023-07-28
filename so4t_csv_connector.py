'''
This Python script is offered with no formal support from Stack Overflow. 
If you run into difficulties, reach out to the person who provided you with this script.
'''

# Standard Python libraries
import argparse
import csv
import datetime
import html
import time

# Third-party libraries
import requests
from bs4 import BeautifulSoup

CSV_NAME = 'so_graph.csv'


def main():

    args = get_args()
    api_data = get_api_data(args)
    csv_data = format_data_for_csv(api_data)
    write_csv(csv_data)

    # Future function for exporting CSV to SharePoint
    # post_csv_to_sharepoint()


def get_args():

    parser = argparse.ArgumentParser(
        prog='csv_connector.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Uses the Stack Overflow for Teams API to create a CSV file to import into '
                    'Microsoft Graph.',
        epilog = 'Example for Stack Overflow Business: \n'
                'python3 so4t_tag_report.py --url "https://stackoverflowteams.com/c/TEAM-NAME" '
                '--token "YOUR_TOKEN" \n\n'
                'Example for Stack Overflow Enterprise: \n'
                'python3 so4t_tag_report.py --url "https://SUBDOMAIN.stackenterprise.co" '
                '--key "YOUR_KEY"\n\n')
    parser.add_argument('--url', 
                        type=str,
                        help='Base URL for your Stack Overflow for Teams instance.')
    parser.add_argument('--token',
                        type=str,
                        help='API token value. Required if using a Basic or Business instance.')
    parser.add_argument('--key',
                        type=str,
                        help='API key value. Required if using an Enterprise instance.')
    return parser.parse_args()


def get_api_data(args):

    v2client = V2Client(args)
    api_data = {}

    # Get question and answer data
    filter_attributes = [
        'answer.body',
        'answer.link',
        'question.answers',
        'question.body',
    ]
    filter_string = v2client.create_filter(filter_attributes, 'default')
    api_data['questions'] = v2client.get_all_questions(filter_string=filter_string)
    
    # Get article data
    filter_attributes = [
        'article.body',
    ]
    filter_string = v2client.create_filter(filter_attributes, 'default')
    api_data['articles'] = v2client.get_all_articles(filter_string=filter_string)

    return api_data


class V2Client(object):

    def __init__(self, args):

        if not args.url:
            print("Missing required argument. Please provide a URL.")
            print("See --help for more information")
            raise SystemExit
        
        if "stackoverflowteams.com" in args.url:
            self.soe = False
            self.api_url = "https://api.stackoverflowteams.com/2.3"
            self.team_slug = args.url.split("https://stackoverflowteams.com/c/")[1]
            self.token = args.token
            self.api_key = None
            self.headers = {'X-API-Access-Token': self.token}
            if not self.token:
                print("Missing required argument. Please provide an API token.")
                print("See --help for more information")
                raise SystemExit
        else:
            self.soe = True
            self.api_url = args.url + "/api/2.3"
            self.team_slug = None
            self.token = None
            self.api_key = args.key
            self.headers = {'X-API-Key': self.api_key}
            if not self.api_key:
                print("Missing required argument. Please provide an API key.")
                print("See --help for more information")
                raise SystemExit

        self.ssl_verify = self.test_connection()


    def test_connection(self):

        url = self.api_url + "/tags"
        ssl_verify = True

        params = {}
        if self.token:
            headers = {'X-API-Access-Token': self.token}
            params['team'] = self.team_slug
        else:
            headers = {'X-API-Key': self.api_key}

        print("Testing API 2.3 connection...")
        try:
            response = requests.get(url, params=params, headers=headers)
        except requests.exceptions.SSLError:
            print("SSL error. Trying again without SSL verification...")
            response = requests.get(url, params=params, headers=headers, verify=False)
            ssl_verify = False
        
        if response.status_code == 200:
            print("API connection successful")
            return ssl_verify
        else:
            print("Unable to connect to API. Please check your URL and API key.")
            print(response.text)
            raise SystemExit


    def get_all_questions(self, filter_string=''):

        endpoint = "/questions"
        endpoint_url = self.api_url + endpoint

        params = {
            'page': 1,
            'pagesize': 100,
        }
        if filter_string:
            params['filter'] = filter_string
    
        return self.get_items(endpoint_url, params)


    def get_all_articles(self, filter_string=''):

        endpoint = "/articles"
        endpoint_url = self.api_url + endpoint

        params = {
            'page': 1,
            'pagesize': 100,
        }
        if filter_string:
            params['filter'] = filter_string

        return self.get_items(endpoint_url, params)
    

    def create_filter(self, filter_attributes='', base='default'):
        # filter_attributes should be a list variable containing strings of the attributes
        # base can be 'default', 'withbody', 'none', or 'total'

        endpoint = "/filters/create"
        endpoint_url = self.api_url + endpoint

        params = {
            'base': base,
            'include': filter_attributes,
            'unsafe': False,
        }

        if filter_attributes:
            # convert to semi-colon separated string
            params['include'] = ';'.join(filter_attributes)

        filter_string = self.get_items(endpoint_url, params)[0]['filter']
        print(f"Filter created: {filter_string}")

        return filter_string


    def get_items(self, endpoint_url, params={}):

        if not self.soe: # SO Basic and Business instances require a team slug in the params
            params['team'] = self.team_slug

        items = []
        while True: # Keep performing API calls until all items are received
            if params.get('page'):
                print(f"Getting page {params['page']} from {endpoint_url}")
            else:
                print(f"Getting API data from {endpoint_url}")
            response = requests.get(endpoint_url, headers=self.headers, params=params, 
                                    verify=self.ssl_verify)
            
            if response.status_code != 200:
                # Many API call failures result in an HTTP 400 status code (Bad Request)
                # To understand the reason for the 400 error, specific API error codes can be 
                # found here: https://api.stackoverflowteams.com/docs/error-handling
                print(f"/{endpoint_url} API call failed with status code: {response.status_code}.")
                print(response.text)
                print(f"Failed request URL and params: {response.request.url}")
                raise SystemExit

            items += response.json().get('items')
            if not response.json().get('has_more'): # If there are no more items, break the loop
                break

            # If the endpoint gets overloaded, it will send a backoff request in the response
            # Failure to backoff will result in a 502 error (throttle_violation)
            if response.json().get('backoff'):
                backoff_time = response.json().get('backoff') + 1
                print(f"API backoff request received. Waiting {backoff_time} seconds...")
                time.sleep(backoff_time)

            params['page'] += 1

        return items
    

def format_data_for_csv(api_data):

    csv_data = []

    # Format each content type for CSV
    for question in api_data['questions']:
        if question.get('answers'):
            for answer in question['answers']:
                answer['type'] = 'answer'
                answer['title'] = '[Answer] ' + question['title']
                answer['tags'] = question['tags']
                answer['view_count'] = question['view_count']
                csv_data.append(answer)
        
        question['type'] = 'question'
        question['title'] = '[Question] ' + question['title']

    for article in api_data['articles']:
        article['type'] = 'article'
        article['title'] = '[Article] ' + article['title']

    csv_data += api_data['questions'] + api_data['articles']

    # For all content types: clean up HTML tags, get author name, and convert timestamp to date
    for item in csv_data:
        item['body'] = remove_html_tags(item['body'])
        item['author'] = get_author(item)
        item['creation_date'] = convert_timestamp_to_date(item['creation_date'])
        item['tags'] = convert_tags_to_string(item['tags'])
        item['title'] = decode_html_encoding(item['title'])
        try:
            item['last_edit_date'] = convert_timestamp_to_date(item['last_edit_date'])
        except KeyError: # if the content was never edited, last_edit_date key will not exist
            item['last_edit_date'] = ''


    return csv_data


def convert_timestamp_to_date(timestamp):

    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')


def get_author(content):

    try:
        return decode_html_encoding(content['owner']['display_name'])
    except KeyError: # if user was deleted, owner key will not exist
        return 'Anonymous'


def remove_html_tags(text):

    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()


def convert_tags_to_string(tags):
    
        return '; '.join(tags)


def decode_html_encoding(text):

    return html.unescape(text)


def write_csv(csv_data):

    # MS Graph doesn't like underscore characters column headers
    csv_columns = ['type', 'title', 'body', 'tags', 'creation_date', 'last_edit_date', 'author',
                    'view_count', 'score', 'link']
    header_row = {column: column.replace('_', ' ') for column in csv_columns}

    with open(CSV_NAME, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns, extrasaction='ignore')
        writer.writerow(header_row)
        for data in csv_data:
            writer.writerow(data)

    print(f"CSV file written to {CSV_NAME}")


def post_csv_to_sharepoint():

    # write code to push CSV to SharePoint
    pass
    

if __name__ == '__main__':

    main()
