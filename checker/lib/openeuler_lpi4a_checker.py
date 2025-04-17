import os
import re
from typing import List
from bs4 import BeautifulSoup
import requests
import semver
from lib.db_models import CheckInfoElement, CheckResultElement
from lib.checker_base import CheckerBase

class OpenEulerLpi4aChecker(CheckerBase):
    def check(self, data: CheckInfoElement) -> CheckResultElement:
        segments = data.check_path.split("/")
        filename = segments[-1]
        regex = re.compile(r'\d{8}-\d{6}')
        match = regex.search(filename)
        if not match:
            return CheckResultElement(data.name, "", failed=True)
        version = match.group().replace("-", "")
        if filename.startswith("boot-"):
            versions = self.get_timestamps(data.check_path, "boot-")
        elif filename.startswith("root-"):
            versions = self.get_timestamps(data.check_path, "root-")
        else:
            return CheckResultElement(data.name, "", failed=True)
        # Sort the versions in descending order
        versions.sort(reverse=True)
        # Get the latest version
        latest_version = versions[0]
        return CheckResultElement(data.name, latest_version, failed=False)

    @staticmethod
    def get_timestamps(url, filter):
        # Extract the directory from the URL and format it
        request_uri = os.path.dirname(url).replace("\\", "/") + "/"
        
        # Send HTTP request to get the webpage content
        response = requests.get(request_uri)
        html = response.text
        
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Select all table rows in the specified path
        trs = soup.select("body > table > tbody > tr")
        
        # Initialize an empty list to store the timestamps
        timestamp_list = []
        
        # Process each row, skipping the first two rows
        for tr in trs[2:]:
            # Get the first column's anchor element and its title attribute
            a_node = tr.select_one("td:first-child a")
            if not a_node:
                continue
                
            file_name = a_node.get("title", "null")
            
            # Skip if filename doesn't start with the filter
            if not file_name.startswith(filter):
                continue
            
            # Use regex to find timestamp pattern in filename
            regex = re.compile(r'\d{8}-\d{6}')
            match = regex.search(file_name)
            
            if match:
                # Convert matched timestamp (removing hyphen) to integer
                timestamp = int(match.group())
                timestamp_list.append(timestamp)
        
        return timestamp_list