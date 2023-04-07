import sys
import os
import importlib
from flask import Flask, request, redirect
from gevent.pywsgi import WSGIServer

app = Flask("vlc-bridge")
name = os.environ['PROVIDER']
providers = {
    name: importlib.import_module(name).Client(),
}

@app.get('/')
def index():
    host = request.host
    ul = ""
    for p in providers:
        pl = f"http://{host}/{p}/playlist.m3u"
        ul += f"<li>{p.upper()}: <a href='{pl}'>{pl}</a></li>\n"

    return f"<h1>Playlist</h1>\n<ul>\n{ul}</ul>"

@app.get("/<provider>/playlist.m3u")
def playlist(provider):
    host = request.host
    stations, err = providers[provider].channels()
    if err is not None:
        return err, 500
    m3u = "#EXTM3U\n\n"
    for s in stations:
        m3u += f"#EXTINF:-1 channel-id=\"{s.get('id')}\""
        if guideId := s.get('guideId'):
            m3u += f" tvg-id=\"{guideId}\""
        if logo := s.get('logo'):
            m3u += f" tvg-logo=\"{logo}\""
        if description := s.get('description'):
            description = description.replace('\n', ' ')
            m3u += f" tvg-description=\"{description}\""
        if genre := s.get('genre'):
            m3u += f" group-title=\"{';'.join([x.strip().title() for x in genre.split(',')])}\""
        m3u += f",{s.get('name') or s.get('id')}\n"
        m3u += f"{s['url']}\n\n"
    return m3u

if __name__ == '__main__':
    sys.stdout.write("⇨ http server started on [::]:7777\n")
    try:
        WSGIServer(('', 7777), app, log=None).serve_forever()
    except OSError as e:
        print(str(e))
        sys.exit(1)
