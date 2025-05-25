import os, shutil, sys, requests, json, secrets, time
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

    def load_gracenote(self):
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
        filter_list = list(filter(lambda d: d.get('stationId') == station_id, self.stations))
        if len(filter_list):
            # print(f'{displayName} in Channel list')
            for elem in self.stations:
                if elem.get('stationId') == station_id:
                    elem_group = elem.get('group')
                    elem_group.append(group)
                    # print(elem_group)
                    # elem.update({'group': elem_group})
        else:
            self.stations.append({'callSign': call_sign,
                                'stationId': station_id,
                                'name': displayName,
                                'logoOnWhite': networkLogo,
                                'networkType': network_type,
                                'group': [group],
                               })
        return ()

    data_channels = []
    addon_channels = []
    addon_rate_plan_codes = []


    def channels(self):
        with self.mutex:
            gracenoteID = self.load_gracenote()
            resp_source, error = self.api("v3/plan-manager/plans")
            if error:
                 return None, error
            resp, error = self.api("subscriptions/products?tags=subscribed&subscribed=true")
            if error:
                return None, error
            resp_user, error = self.api("subscriptions")
            if error:
                return None, error
            self.stations = []

            main_rate_plan_codes = []
            all_rate_plan_codes = []
            source_channels = []

            for main_plan in resp_user:
                main_rate_plan_code = main_plan.get("ratePlanCode")
                main_rate_plan_codes.append(main_rate_plan_code)
            for addon_plan in main_plan.get('addons', []):
                addon_rate_plan_code = addon_plan.get("ratePlanCode")
                self.addon_rate_plan_codes.append(addon_rate_plan_code)
            # print(self.addon_rate_plan_codes)

            for data_channels_list in resp.get('products', []):
                    for data_rate_plans in data_channels_list.get('ratePlans', []):
                        if data_rate_plans.get('code') in main_rate_plan_codes:
                            self.data_channels.append(data_channels_list)

            for addon_channels_list in resp.get('addons', []):
                for addon_channels_rate_plans in addon_channels_list.get('ratePlans', []):
                    if addon_channels_rate_plans.get('code') in self.addon_rate_plan_codes:
                        self.addon_channels.append(addon_channels_list)

            for source in resp_source.get('data', []):
                for source_channels_list in source.get('default_package', []).get('channels', []):
                    source_channels.append(source_channels_list)
                for addons_channels_list in source.get('add_on_packages', []):
                    for addons_channels_channels in addons_channels_list.get('channels', []):
                        source_channels.append(addons_channels_channels)

            # print(json.dumps(source_channels, indent=2))

            combine_channels = self.addon_channels + self.data_channels
            combined_rate_plans = main_rate_plan_codes + self.addon_rate_plan_codes

            # Create mapping of station_id to source
            source_mapping = {}
            for source_channel in source_channels:
                if 'station_id' in source_channel:
                    source_mapping[source_channel['station_id']] = source_channel.get('source')

            # Update combine_channels with source values
            for channel_group in combine_channels:
                for channel in channel_group.get('channels', []):
                    if 'stationId' in channel:
                        station_id = channel['stationId']
                        if station_id in source_mapping:
                            channel['source'] = source_mapping[station_id]
            # print(json.dumps(combine_channels, indent=2))

            for elem in combined_rate_plans:
                match_filter_list = list(
                    filter(lambda d: any(rp.get('code') == elem for rp in d.get('ratePlans', [])), combine_channels))
                # print(match_filter_list)
                if len(match_filter_list):
                    for item in match_filter_list:
                        channels_list = item.get('channels', [])
                        # print(f"Number of default Channels {len(channels_list)}")
                        # print(channels_list)
                        for ch in channels_list:
                            if ((ch.get('source') == 'Disney') or
                                    (ch.get('callSign') == 'MXEF') or
                                    (ch.get('callSign') == 'ESPNUHD') or
                                    (ch.get('callSign') == 'ESPNEWS') or
                                    (ch.get('callSign') == 'ACCDN') or
                                    (ch.get('callSign') == 'NGWIHD') or
                                    (ch.get('callSign') == 'HALLHDDRM') or
                                    (ch.get('callSign') == 'HMMHDDRM') or
                                    (ch.get('callSign') == 'HALLDRDRM') or
                                    (ch.get('callSign') == 'MDL') or #channel no longer available
                                    (ch.get('callSign') == 'KNBC') or #NBC Los Angeles
                                    (ch.get('callSign') == 'WNBC') or #NBC New York
                                    (ch.get('callSign') == 'KCOP') or #MyNetwork Los Angeles
                                    (ch.get('callSign') == 'WWORDT') or #MyNetwork New York
                                    (ch.get('callSign') == 'GETCMDY') or #Get Comedy
                                    (ch.get('source') == 'Starz') or
                                    (ch.get('source') == 'Showtime')):
                                continue
                            else:
                                self.add_stations(ch.get('callSign'),
                                                  ch.get('stationId'),
                                                  ch.get('name', '').replace(',', ''),
                                                  ch.get('logoOnWhite'),
                                                  ch.get('networkType'),
                                                  elem)
            for j in self.stations:
                id = j.get('stationId', '')
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
        #        0 if x['group'] and x['group'][0] == main_rate_plan_codes else 1,
        #        x['group'][0] if x['group'] else '',  # Use an empty string if group is empty
                0 if x['networkType'] == 'OTA' else (1 if x['networkType'] == 'RSN' else 2),
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
