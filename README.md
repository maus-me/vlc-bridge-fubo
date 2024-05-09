# vlc-bridge-fubo

This is the code repository for vlc-bridge-fubo, a Fubo TV bridge for VLC. Taking FUBO programming and transforms it into a "live TV" experience with virtual linear channels that you can use in most live TV players such as VLC.

This is made for using your own credentials. This leverages FUBO's API to get the channel list and stream URLs. This is not a replacement for FUBO, you still need a FUBO subscription to use this.

## Docker

```
docker run -d -e 'FUBO_USER=<username>' -e 'FUBO_PASS=<password>' -p 7777:7777 -v config_dir:/app/Config --name vlc-bridge-fubo ghcr.io/maus-me/vlc-bridge-fubo:master
```

## Native

```
git clone https://github.com/maus-me/vlc-bridge-fubo
cd vlc-bridge-fubo
pip3 install -r requirements.txt
python3 server.py
```