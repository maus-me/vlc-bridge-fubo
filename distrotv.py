import requests
import time
from datetime import datetime
from threading import Lock
from xmltv.models import xmltv
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

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

    def epg(self):
        self.load_feed()
        epg = xmltv.Tv(
            source_info_name="distrotv",
            generator_info_name="vlc-bridge"
        )
        ids = {}
        for ch in self.feed["shows"].values():
            ids[str(ch["seasons"][0]["episodes"][0]["id"])] = ch["name"]
            epg.channel.append(xmltv.Channel(
                id=ch["name"],
                display_name=[ch["title"].strip()]
            ))
        data = self.session.get("https://tv.jsrdn.com/epg/query.php?id="+ ",".join(ids.keys())).json()
        for id, name in ids.items():
            if (ch := data["epg"].get(id)) is not None and (slots := ch.get("slots")) is not None:
                for slot in slots:
                    epg.programme.append(xmltv.Programme(
                        channel=name,
                        title=slot["title"].strip(),
                        desc=(slot.get("description") or "").strip(),
                        icon=slot["img_thumbh"],
                        start=datetime.strptime(slot["start"], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M%S') + " +0000",
                        stop=datetime.strptime(slot["end"], '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M%S') + " +0000",
                    ))
        serializer = XmlSerializer(config=SerializerConfig(
            pretty_print=True,
            encoding="UTF-8",
            xml_version="1.1",
            xml_declaration=False,
            no_namespace_schema_location=None
        ))
        return serializer.render(epg)

