import os
import re
from typing import List
from bs4 import BeautifulSoup
import requests
import semver
from lib.db_models import CheckInfoElement, CheckResultElement
from lib.checker_base import CheckerBase
from urllib.parse import urlparse

class RevyOSChecker(CheckerBase):
    def check(self, data: CheckInfoElement) -> CheckResultElement:
        # keep for future use
        
        regex = re.compile(r'\d{8}')
        match = regex.search(data.check_path)
        if not match:
            return CheckResultElement(data.name, "", "", failed=True)
        current_version = match.group().replace("-", "")
        
        # Get the latest timestamp from the URL
        versions = self.get_timestamps(data.check_path)
        
        # Sort the versions in descending order
        versions.sort(reverse=True)
        
        # Get the latest version
        latest_version = versions[0]
        
        return CheckResultElement(data.name, latest_version, current_version, failed=False)
    
    @staticmethod
    def get_timestamps(url):
        # url is https://mirror.iscas.ac.cn/revyos/extra/images/sg2042/20241230/revyos-pioneer-20241230-212249.img.zst
        # truncate to https://mirror.iscas.ac.cn/revyos/extra/images/sg2042/

        parsed_url = urlparse(url)
    
        # Split the path and truncate to the desired section
        base_path = '/'.join(parsed_url.path.split('/')[:5])  # Keep first six segments of the path
    
        # Reconstruct the truncated URL
        request_uri = f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}/"

        response = requests.get(request_uri)
        html = response.text
        
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Select all table rows in the specified path
        trs = soup.select("body > pre a")
        
        # Initialize an empty list to store the timestamps
        timestamp_list = []
        
        # Process each row, skipping the first two rows
        for tr in trs[1:]:
            # Get the first column's anchor element and its title attribute
            file_name = tr.get("href", "null")
            
            # Extract timestamp from filename using regex
            regex = re.compile(r'\d{8}')
            match = regex.search(file_name)
            if match:
                timestamp_list.append(match.group())
        
        return timestamp_list

