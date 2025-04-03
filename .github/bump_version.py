import re
import subprocess

import requests

pypi_rss_url = "https://pypi.org/rss/project/unifyai/releases.xml"

if __name__ == "__main__":
    # Get the latest version from the RSS feed
    response = requests.get(pypi_rss_url)
    version = re.findall(r"\d+\.\d+\.\d+", response.text)[0]
    if not version:
        raise Exception("Failed parsing version")

    # Bump patch version
    subprocess.run(["poetry", "version", version])
    subprocess.run(["poetry", "version", "patch"])
