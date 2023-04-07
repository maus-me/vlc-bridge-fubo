import requests
import time
from threading import Lock

class Client:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; AFTT Build/STT9.221129.002) GTV/AFTT DistroTV/2.0.9'
        })
        self.lock = Lock()
        self.feed = None
        self.feedTime = 0

    def load_feed(self):
        with self.lock:
            if self.feed is not None and time.time() - self.feedTime < 3600*12:
                return
            data = self.session.get("https://tv.jsrdn.com/tv_v5/getfeed.php").json()
            self.feed = {
                "topics": [t for t in data["topics"] if t["type"] == "live"],
                "shows": {k:v for k, v in data["shows"].items() if v["type"] == "live"},
            }
            self.feedTime = time.time()

    def channels(self):
        self.load_feed()
        stations = []
        for ch in self.feed["shows"].values():
            stations.append({
                "id": ch["name"],
                "guideId": ch["name"],
                "logo": ch["img_logo"],
                "genre": ch["genre"] + "," + ch["keywords"],
                "description": ch["description"].strip(),
                "name": ch["title"].strip(),
                "url": ch["seasons"][0]["episodes"][0]["content"]["url"].split('?', 1)[0],
            })
        return stations, None

