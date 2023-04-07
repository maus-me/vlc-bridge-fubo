# vlc-bridge-distrotv

watch distro.tv live stream in VLC

### using

`$ docker run -d -p 7777:7777 --name vlc-bridge-distrotv registry.gitlab.com/miibeez/vlc-bridge-distrotv`

`$ vlc http://localhost:7777/distrotv/playlist.m3u`

### epg

`http://localhost:7777/distrotv/epg.xml`
