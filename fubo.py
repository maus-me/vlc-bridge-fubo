import json
import os
import requests
import secrets
import shutil
import sys
import time
from threading import Lock

user = os.environ.get("FUBO_USER")
passwd = os.environ.get("FUBO_PASS")

if user is None or passwd is None:
    sys.stderr.write("FUBO_USER and FUBO_PASS need to be set\n")
    sys.stderr.write(f'FUBO_USER = {user}\n')
    sys.stderr.write(f'FUBO_PASS = {passwd}\n')

    sys.exit(1)


class Client:
    def __init__(self):
        self.user = os.environ["FUBO_USER"]
        self.passwd = os.environ["FUBO_PASS"]
        self.device = None

        self.loggedIn = False
        self.sessionID = ""
        self.sessionAt = 0
        self.stations = []

        self.mutex = Lock()
        self.session = requests.Session()
        self.load_device()

        self.headers = {
            'authority': 'api.fubo.tv',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.fubo.tv',
            'referer': 'https://www.fubo.tv/',
            'x-client-version': '4.75.0',
            'x-device-app': 'android_tv',
            'x-device-group': 'tenfoot',
            'x-device-id': self.device,
            'x-device-model': 'onn. 4K Streaming Box',
            'x-device-platform': 'android_tv',
            'x-device-type': 'puck',
            'x-player-version': 'v1.34.0',
            'x-preferred-language': 'en-US',
            'x-supported-hdrmodes-list': 'hdr10,hlg',
            'x-supported-streaming-protocols': 'hls',
            'x-supported-codecs-list': 'vp9,avc,hevc',
            'x-timezone-offset': '-420',
            'user-agent': 'fuboTV/4.75.0 (Linux;Android 12; onn. 4K Streaming Box Build/SGZ1.221127.063.A1.9885170) FuboPlayer/v1.34.0',
        }

    @staticmethod
    def load_gracenote():
        source = "./fubo-gracenote-default.json"
        destination = "./Config/fubo-gracenote.json"

        if not os.path.exists(destination):
            # Create the destination directory if it does not exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copyfile(source, destination)

        try:
            with open("./Config/fubo-gracenote.json", "r") as f:
                gracenoteID_list = json.load(f)
        except:
            print('No gracenoteID_list')
            gracenoteID_list = {}
        return (gracenoteID_list)

    def checkDRM(self, id):
        # print(f"CheckDRM {id}")
        token, error = self.token()
        if error:
            return None, error
        # print(f"Calling for Stream with {id}: {token}")
        stream, error = self.api(f"v3/kgraph/v3/networks/{id}/stream")
        if error:
            return None, error
        return stream.get('streamUrls')[0].get('drmProtected'), None

    def add_stations(self, call_sign, station_id, displayName, networkLogo, network_type, group):
        filter_list = list(filter(lambda d: d.get('id') == station_id, self.stations))
        if len(filter_list):
            # print(f'{displayName} in Channel list')
            for elem in self.stations:
                if elem.get('id') == station_id:
                    elem_group = elem.get('group')
                    elem_group.append(group)
                    # print(elem_group)
                    elem.update({'group': elem_group})
        else:
            self.stations.append({'call_sign': call_sign,
                                  'id': station_id,
                                  'name': displayName,
                                  'logo': networkLogo,
                                  'network_type': network_type,
                                  'group': [group],
                                  })
        return ()

    def add_package_channels(self, package, purchased_package):
        for add_on in purchased_package:
            fubo_extra = list(filter(lambda d: add_on == d.get('slug', None), package))
            # print(f"{add_on} part of add-on package")
            print(f"{add_on} is {len(fubo_extra)}")
            for extras in fubo_extra:
                slug = extras.get('slug', None)
                # print(f"    {slug}")
                fubo_extra_channels = extras.get('channels')
                # print(f"    Number of channels in add-on package {slug} is {len(fubo_extra_channels)}")
                for ch in fubo_extra_channels:
                    if ((ch.get('source') == 'Disney') or
                            (ch.get('call_sign') == 'MXEF') or
                            (ch.get('source') == 'Starz') or
                            (ch.get('source') == 'Showtime')):
                        # print (f"Channel {ch.get('meta').get('displayName')} has been removed due to DRM")
                        continue
                    else:
                        self.add_stations(ch.get('call_sign'),
                                          ch.get('station_id'),
                                          ch.get('meta').get('networkName'),
                                          ch.get('meta').get('networkLogoOnWhiteUrl'),
                                          ch.get('meta').get('network_type'),
                                          slug)

    def channels(self):
        with self.mutex:
            gracenoteID = self.load_gracenote()
            resp, error = self.api("v3/plan-manager/plans")
            if error:
                return None, error
            resp_user, error = self.api("user")
            if error:
                return None, error
            self.stations = []

            plan_data = resp.get('data')
            user_data = resp_user.get('data')

            # print(json.dumps(plan_data, indent=2))
            # print(json.dumps(user_data, indent=2))

            for elem in user_data.get('recurly').get('purchased_packages'):
                # print(elem)
                match_filter_list = [element for element in plan_data if
                                     element.get("default_package", {}).get("slug") == elem]
                if len(match_filter_list):
                    # print(f'{elem} In Group')
                    # print(len(match_filter_list))
                    for item in match_filter_list:
                        default_package = item.get('default_package').get('channels')
                        # print(f"Number of default Channels {len(default_package)}")
                        for ch in default_package:
                            if ((ch.get('source') == 'Disney') or
                                    (ch.get('call_sign') == 'MXEF') or
                                    (ch.get('source') == 'Starz') or
                                    (ch.get('source') == 'Showtime')):
                                print(f"Channel {ch.get('meta').get('displayName')} has been removed due to DRM")
                                continue
                            else:
                                self.add_stations(ch.get('call_sign'),
                                                  ch.get('station_id'),
                                                  ch.get('meta').get('networkName').replace(',', ''),
                                                  ch.get('meta').get('networkLogoOnWhiteUrl'),
                                                  ch.get('meta').get('network_type'),
                                                  elem)

                        self.add_package_channels(item.get('add_on_packages'),
                                                  user_data.get('recurly').get('purchased_packages'))
                        self.add_package_channels(item.get('expired_packages'),
                                                  user_data.get('recurly').get('purchased_packages'))

            for j in self.stations:
                id = j.get('id', '')
                gracenote = gracenoteID.get(str(id), {})
                gracenoteId = gracenote.get("StationID", None)
                timeShift = gracenote.get("TimeShift", None)
                if gracenoteId is not None:
                    # print(f"GracenoteID for {j.get('name')} manually mapped to {gracenoteId}" )
                    j.update({'gracenoteId': gracenoteId})
                if timeShift is not None:
                    # print(f"TimeShift Added for {j.get('name')} by {timeShift}" )
                    j.update({'timeShift': timeShift})

            ch_list = self.stations
            for elem in ch_list:
                grp = elem.get("group")
                elem.update({"group": list(sorted(grp))})
            sorted_ch_list = sorted(ch_list, key=lambda x: (
                0 if x['group'] and x['group'][0] == 'fubotv-basic' else 1,
                x['group'][0] if x['group'] else '',  # Use an empty string if group is empty
                0 if x['network_type'] == 'OTA' else (1 if x['network_type'] == 'RSN' else 2),
                x['name']
            ))
            # (0 if x['group'][0] == 'fubotv-basic' else 1, x['group'][0], x['name']))
            # print(json.dumps(sorted_ch_list, indent=2))
            # print(len(self.stations))
            return sorted_ch_list, None

    def watch(self, id):
        with self.mutex:
            token, error = self.token()
            if error:
                return None, error

            stream, error = self.api(f"vapi/asset/v1?channelId={id}&type=live")
            if error:
                return None, error

            url = stream.get('stream').get('url')
            # print(url)
            if stream.get('stream').get('drmProtected') is True:
                DRM_Station = list(filter(lambda d: str(d.get('id')) == id, self.stations))
                if not DRM_Station:
                    print(f"Stream {id} is DRM Protected")
                else:
                    print(
                        f"Stream {id} is DRM Protected ({DRM_Station[0].get('call_sign', '')}: {DRM_Station[0].get('name', '')})")
                    # print(f"{url}")

                return None, "Stream is DRM Protected"
            return url, None

    def load_device(self):
        with self.mutex:
            try:
                with open("fubo-device.json", "r") as f:
                    self.device = json.load(f)
            except FileNotFoundError:
                self.device = secrets.token_hex(8)
                with open("fubo-device.json", "w") as f:
                    json.dump(self.device, f)

    def token(self):
        if self.sessionID != "" and (time.time() - self.sessionAt) < 4 * 60 * 60:
            return self.sessionID, None

        data = {"email": self.user, "password": self.passwd}
        # print('Call for sign-in')
        try:
            response = self.session.put('https://api.fubo.tv/signin', json=data, headers=self.headers)
        except requests.ConnectionError as e:
            print("Connection Error.")
            print(str(e))
            return None, f"Connection Error. {str(e)}"
        # print('Return for sign-in')
        if response.status_code != 200:
            return None, f"HTTP failure {response.status_code}: {response.text}"
        else:
            resp = response.json()

        token = resp.get('access_token', None)
        # print(token)
        self.sessionID = token
        self.sessionAt = time.time()
        return token, None

    def api(self, cmd, data=None):
        token, error = self.token()
        if error:
            return None, error

        if token is not None:
            self.headers.update({'authorization': f'Bearer {token}'})
        # print(headers)
        url = f"https://api.fubo.tv/{cmd}"
        if data:
            response = self.session.put(url, data=data, headers=self.headers)
        else:
            response = self.session.get(url, headers=self.headers)
        if response.status_code != 200:
            return None, f"HTTP failure {response.status_code}: {response.text}"
        # print(response.text)
        return response.json(), None
