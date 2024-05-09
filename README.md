# vlc-bridge-fubo

watch fubo.tv live stream in VLC
This takes FUBO programming and transforms it into a "live TV" experience with virtual linear channels that you can import into something like Jellyfin/Emby/Channels.

This was not made for pirating streams.  This is made for using your own credentials and have a different presentation than the FUBO app currently provides.

## Docker

```
docker run -d -e 'FUBO_USER=<username>' -e 'FUBO_PASS=<password>' -p 7777:7777 -v config_dir:/app/Config --name vlc-bridge-fubo registry.gitlab.com/Yankees4life/vlc-bridge-fubo
```

## Native

```
git clone https://github.com/maus-me/vlc-bridge-fubo
cd vlc-bridge-fubo
pip3 install -r requirements.txt
python3 server.py
```