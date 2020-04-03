import urllib
import requests
import http.server


def _serve_async():
    httpd = http.server.HTTPServer(("localhost", 5000), AuthHandler)
    while not AuthHandler.all_done:
        print("Wait for authorization ...")
        httpd.handle_request()
    print("Async server closed.", AuthHandler.auth_data)
    return AuthHandler.auth_data


class AuthHandler(http.server.BaseHTTPRequestHandler):
    all_done = False
    auth_data = {}

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        code = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)["code"][0]
        params = {
            "client_id": "33022",
            "client_secret": "66565bfa5ccbcf7e10c323f1add1f23b958a7572",
            "code": code,
            "grant_type": "authorization_code"
        }
        response = requests.post(
            "https://www.strava.com/oauth/token",
            params=params
        )
        AuthHandler.auth_data = response.json()
        AuthHandler.all_done = True