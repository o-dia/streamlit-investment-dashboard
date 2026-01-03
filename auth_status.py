# This file runs a HTTP get request to ensure authentication with the IB Gateway is working correctly,
# the main purpose is to ensure the app is authenticated, connected and backend server looks healthy

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def confirmStatus():
    base_url = "https://localhost:5001/v1/api/"
    endpoint = "iserver/auth/status"

    auth_req = requests.get(url=base_url+endpoint, verify=False) 
    #this builds the request, a http GET request, to be specific. 
    #False means you don't need an SSL verification on the request
    print(auth_req)
    print(auth_req.text)

if __name__ == "__main__":
    confirmStatus()

