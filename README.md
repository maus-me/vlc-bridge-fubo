# vlc-bridge-fubo

watch fubo.tv live stream in VLC
This takes FUBO programming and transforms it into a "live TV" experience with virtual linear channels that you can import into something like Jellyfin/Emby/Channels.

This was not made for pirating streams.  This is made for using your own credentials and haave a different presentation than the FUBO app currently provides.

### using

`$ docker run -d -p 7777:7777 --name vlc-bridge-distrotv registry.gitlab.com/miibeez/vlc-bridge-distrotv`

`$ vlc http://localhost:7777/distrotv/playlist.m3u`

### epg

`http://localhost:7777/distrotv/epg.xml`

# vlc-bridge-fubo



## Docker

```
docker run -d -e 'FUBO_USER=<username>' -e 'FUBO_PASS=<password>' -p 7777:7777 -v config_dir:/app/Config --name vlc-bridge-fubo registry.gitlab.com/Yankees4life/vlc-bridge-fubo
```

## Native

```
git clone https://gitlab.com/Yankees4life/vlc-bridge-fubo
cd vlc-bridge-fubo
pip3 install -r requirements.txt
python3 pywsgi.py
```