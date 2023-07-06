# Stack Overflow for Teams CSV Connector for Microsoft Graph
An API script for Stack Overflow for Teams that creates a CSV file to be imported into Microsoft Graph. You can see an example of what the output looks like in the Examples directory ([here](https://github.com/jklick-so/so4t_csv_connector/blob/main/Examples/so_graph.csv)).

All data obtained via the API is handled locally on the device from which the script is run. The script does not transmit data to other parties, such as Stack Overflow. All of the API calls performed are read only, so there is no risk of editing or adding content on your Stack Overflow for Teams instance.

This script is offered with no formal support from Stack Overflow. If you run into issues using the script, please [open an issue](https://github.com/jklick-so/so4t_csv_connector/issues) and/or reach out to the person who provided it to you. You are also welcome to edit the script to suit your needs.

## Requirements
* A Stack Overflow for Teams instance (Basic, Business, or Enterprise)
* Python 3.x ([download](https://www.python.org/downloads/))
* Operating system: Linux, MacOS, or Windows

## Setup

[Download](https://github.com/jklick-so/so4t_csv_connector/archive/refs/heads/main.zip) and unpack the contents of this repository

**Installing Dependencies**

* Open a terminal window (or, for Windows, a command prompt)
* Navigate to the directory where you unpacked the files
* Install the dependencies: `pip3 install -r requirements.txt`

**API Authentication**

For the Basic and Business tiers, you'll need an API token. For Enterprise, you'll need to an API key. In both cases, only read permissions are needed for the key/token.

* For Basic or Business, instructions for creating a personal access token (PAT) can be found in [this KB article](https://stackoverflow.help/en/articles/4385859-stack-overflow-for-teams-api).
* For Enteprise, documentation for creating the key can be found within your instance, at this url: `https://[your_site]/api/docs/authentication`

## Usage
In a terminal window, navigate to the directory where you unpacked the script. 
Run the script using the following format, replacing the URL, token, and/or key with your own:
* Example for Basic and Business: `python3 so4t_csv_connector.py --url "https://stackoverflowteams.com/c/TEAM-NAME" --token "YOUR_TOKEN"`
* Examplme for Enterprise: `python3 so4t_csv_connector.py --url "https://SUBDOMAIN.stackenterprise.co" --key "YOUR_KEY"`

The script can take a few minutes to run, particularly as it gathers data via the API. As it runs, it will continue to update the terminal window with the tasks it's performing. When the script completes, it will indicate the the CSV has been exported, along with the name of file. You can see an example of what the output looks like [here](https://github.com/jklick-so/so4t_tag_report/blob/main/Examples/tag_metrics.csv).

## Setting up the CSV as a data source for MS Graph
To set up the CSV as a data source, follow [Microsoft's documentation](https://learn.microsoft.com/en-us/microsoftsearch/csv-connector) for setting up a CSV connector. 
