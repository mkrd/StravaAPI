import os
import time
import json
import urllib
import requests
import multiprocessing as mp

from .StravaWebHandler import StravaWebHandler
from .StravaAuthHandler import _serve_async


__version__ = "0.1.1"


class StravaAPI:
    # Initialize the Strava API. This also starts a Strava session on the website for authorization and downloads.
    def __init__(self, client_id, client_secret):
        print("StravaAPI: Initialize")
        self.client_secret = client_secret
        self.client_id = client_id
        self.authData = None

        # Load stored auth data
        auth_data_path = "./.strava_api_auth_data.json"

        if os.path.exists(auth_data_path):
            with open(auth_data_path, "r") as f:
                self.authData = json.loads(f.read())
            now = time.time()
            if now >= self.authData["expires_at"]:
                # Get new token with refresh_token
                print("StravaAPI: Token expired. Get new one with refresh_token")
                refresh_auth_data = requests.post("https://www.strava.com/api/v3/oauth/token", params={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.authData["refresh_token"]
                })
                self.authData = refresh_auth_data.json()
                with open(auth_data_path, "w") as f:
                    f.write(json.dumps(self.authData))
            else:
                print(f"StravaAPI token still good for {(self.authData['expires_at'] - now) / 3600.0:.2f}h")
        else:
            # If token does not exist, authorize
            print("StravaAPI: Logign and authorize application")
            self.StravaWebHandler = StravaWebHandler()
            strava_email = input("Enter your Strava email: ")
            strava_password = input("Enter your Strava password: ")
            self.StravaWebHandler.login(strava_email, strava_password)
            self.authorize()
            # Write authData to path to reuse the access token
            with open(auth_data_path, "w+") as f:
                f.write(json.dumps(self.authData))


    # Authorize with the Strava API. This is required to make calls to the API.
    def authorize(self):
        authorize_base_url = "https://www.strava.com/oauth/authorize?"
        params = {
            "redirect_uri": "http://localhost:5000/authorized",
            "client_id": self.client_id,
            "response_type": "code",
            "scope": "activity:read"
        }
        authorize_url = authorize_base_url + urllib.parse.urlencode(params)
 
        mp.set_start_method("fork")
        pool = mp.Pool(1)
        serve_result = pool.apply_async(_serve_async)
        # Give the server time to set up
        time.sleep(1)
        self.StravaWebHandler.authorize(authorize_url)
        pool.close()
        pool.join()
        self.authData = serve_result.get()
        print(f"{self.authData=}")
        print("Authorization success!")


    ############################################################################
    # Strava API calls
    ############################################################################


    def get(self, sub_url=None, params=None):
        headers = {"Authorization": "Bearer " + self.authData["access_token"]}
        response = requests.get(
            "https://www.strava.com/api/v3/" + sub_url,
            params=params, headers=headers)
        print(response.url)
        return response.json()


    # first page is 1
    def listAthleteActivities(self, page, per_page):
        params = {"page": page, "per_page": per_page}
        return self.get(sub_url="athlete/activities", params=params)


    def listAhtleteStarredSegments(self, page, per_page):
        params = {"page": page, "per_page": per_page}
        return self.get(sub_url="segments/starred", params=params)


    def exploreSegments(self, southwest_lat, southwest_lng, northeast_lat, northeast_lng):
        params = {
            "activity_type": "riding",
            "bounds": f"{southwest_lat},{southwest_lng},{northeast_lat},{northeast_lng}"
        }
        return self.get(sub_url="segments/explore", params=params)


    def segment(self, id):
        return self.get(sub_url=f"segments/{id}", params={})


    def getLeaderboardBySegmentId(self, id, date_range):
        params = {
            "date_range": date_range,
            "per_page": 100
        }
        return self.get(sub_url=f"segments/{id}/leaderboard", params=params)


    ############################################################################
    # Strava Website calls
    ############################################################################


    def download(self, acitvity_id, file_path):
        self.StravaWebHandler.download(acitvity_id, file_path)