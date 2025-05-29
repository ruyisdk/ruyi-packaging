from typing import List
from bs4 import BeautifulSoup
import requests
import semver
from lib.db_models import CheckInfoElement, CheckResultElement
from lib.checker_base import CheckerBase

class OpenWrtChecker(CheckerBase):
    @staticmethod
    def get_openwrt_versions() -> List[semver.VersionInfo]:
    # Send HTTP request to get the webpage content
      response = requests.get("https://mirrors.tuna.tsinghua.edu.cn/openwrt/releases/")
      html = response.text
      
      # Parse the HTML
      soup = BeautifulSoup(html, 'html.parser')
      
      # Select all table rows in the specified path
      trs = soup.select("body > div:nth-child(2) > div:nth-child(2) > div > div > table > tbody > tr")
      
      # Initialize an empty list to store the versions
      version_list = []
      
      # Process each row
      for tr in trs:
          # Get the first column's anchor element
          a_node = tr.select_one("td:first-child a")
          if a_node:
              # Get the title attribute (or "null" if not found)
              file_name = a_node.get("title", "null")
              
              # Try to parse the file name as a semantic version
              try:
                  ver = semver.VersionInfo.parse(file_name)
                  # append non-prerelease versions
                  if ver.prerelease is None or len(ver.prerelease) == 0:
                    version_list.append(ver)
              except ValueError:
                  # Skip if not a valid semantic version
                  pass
      
      return version_list
    def check(self, data: CheckInfoElement) -> CheckResultElement:
        try:
            # Get the list of OpenWrt versions
            version_list = OpenWrtChecker.get_openwrt_versions()
            # Sort the versions in descending order
            version_list.sort(reverse=True)
            
            # Get the latest version
            latest_version = version_list[0]

            # data.check_path is https://mirrors.tuna.tsinghua.edu.cn/openwrt/releases/23.05.2/targets/sifiveu/generic/openwrt-23.05.2-sifiveu-generic-sifive_unmatched-ext4-sdcard.img.gz
            # extract 23.05.2 from the path

            segments = data.check_path.split("/")
            current_version_str = segments[5]
            
            return CheckResultElement(data.name, str(latest_version), current_version_str, failed=False)
        except Exception as e:
            return CheckResultElement(data.name, "", failed=True)
    