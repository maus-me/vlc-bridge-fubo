# import flask module
import importlib
import os
import subprocess
import sys
from dotenv import load_dotenv
from flask import Flask, redirect, request, Response
from gevent import monkey
from gevent.pywsgi import WSGIServer

monkey.patch_all()

load_dotenv()

# instance of flask application
app = Flask(__name__)
provider = "fubo"
providers = {
    provider: importlib.import_module(provider).Client(),
}


def get_stream_url(url, key=None, stream_quality='1080p_alt,720p_alt,best'):
    # Set the STREAMLINK_HOME environment variable to handle user configurations
    os.environ['STREAMLINK_HOME'] = './streamlink_home'
    # Generate the stream link using Streamlink
    print(url)
    streamlink_command = f'streamlink "{url}" --default-stream {stream_quality} --stdout --hls-playlist-reload-time 0.1 --loglevel none'

    if key is not None:
        streamlink_command = f'{streamlink_command}" -decryption_key "{key}"'
    stream_process = subprocess.Popen(streamlink_command, shell=True, stdout=subprocess.PIPE)
    #stream_process = subprocess.Popen(streamlink_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return stream_process.stdout


@app.route("/")
def index():
    host = os.environ["HOST"]
    port = os.environ["PORT"]
    ul = ""
    pl = f"http://{host}:{port}/{provider}/playlist-mpeg.m3u"
    ul += f"<li>{provider.upper()} MPEG-TS: <a href='{pl}'>{pl}</a></li>\n"
    pl = f"http://{host}:{port}/{provider}/playlist-hls.m3u"
    ul += f"<li>{provider.upper()} HLS: <a href='{pl}'>{pl}</a></li>\n"

    url = f'<!DOCTYPE html>\
            <html>\
              <head>\
                <meta charset="utf-8">\
                <meta name="viewport" content="width=device-width, initial-scale=1">\
                <title>{provider.capitalize()} Playlist</title>\
                <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.1/css/bulma.min.css">\
                <style>\
                  ul{{\
                    margin-bottom: 10px;\
                  }}\
                </style>\
              </head>\
              <body>\
              <section class="section">\
                <div class="container">\
                  <h1 class="title">\
                    {provider.capitalize()} Playlist\
                    <span class="tag">v1.16</span>\
                  </h1>\
                  <p class="subtitle">\
                    Last Updated: Jan 4, 2024\
                  </p>\
                  <ul>'

    return f"{url}<ul>{ul}</ul></div></section></body></html>"


@app.get("/<provider>/playlist-<stream_type>.m3u")
def playlist(provider, stream_type):
    host = request.host
    stations, err = providers[provider].channels()

    if err is not None:
        return err, 500
    m3u = "#EXTM3U\r\n\r\n"
    for s in stations:
        m3u += f"#EXTINF:-1 channel-id=\"{s.get('id')}\""
        m3u += f" tvg-id=\"{s.get('call_sign')}\""
        group = s.get('group')
        if group is not None:
            m3u += f" group-title=\"{';'.join(map(str, group))}\""
        logo = s.get('logo')
        if logo is not None:
            m3u += f" tvg-logo=\"{logo}\""
        gracenoteid = s.get('gracenoteId')
        if gracenoteid is not None:
            if gracenoteid != "":
                m3u += f" tvc-guide-stationid=\"{gracenoteid}\""
        else:
            # print(f"Using Fubo ID {s.get('id')} as StationID for {s.get('name')}" )
            m3u += f" tvc-guide-stationid=\"{s.get('id')}\""

        timeShift = s.get('timeShift')
        if timeShift is not None:
            m3u += f" tvg-shift=\"{timeShift}\""
        m3u += f",{s.get('name') or s.get('call_sign')}\n"
        m3u += f"http://{host}/{provider}/watch-{stream_type}/{s.get('watchId') or s.get('id')}\n\n"

    response = Response(m3u, content_type='audio/x-mpegurl')
    return response


@app.route("/<provider>/watch-<stream_type>/<id>")
def watch(provider, stream_type, id):
    video_url, err = providers[provider].watch(id)
    if err is not None:
        return "Error", 500, {'X-Tuner-Error': err}
    # sys.stdout.write(f"{video_url}\n")
    if stream_type == 'mpeg':
        return get_stream_url(video_url)
    elif stream_type == 'hls':
        return redirect(video_url)
    else:
        return "Error", 500, {'X-Tuner-Error': f'Stream type {stream_type} not found'}


if __name__ == '__main__':
    sys.stdout.write("⇨ http server started on [::]:7777\n")
    try:
        WSGIServer(('0.0.0.0', 7777), app, log=None).serve_forever()
    except OSError as e:
        print(str(e))
