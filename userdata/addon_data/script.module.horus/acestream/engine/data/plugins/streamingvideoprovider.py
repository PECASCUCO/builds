#-plugin-sig:NAfIQMT/jN5sEHhXcMP7Fi4YNZIblfVcr8/sEWVFVjiNdOYRIFvuSjvR5Z+lXsooI+T9dh0nzahncv0rsly77OyZfPl8MyczVXDKzBtXysGRuODQqbcjC70sorQbImLmKALyytr1jkoigudcMJCLGMg8/angW4+Xk7xHI7AEQPebfYOQYVzJFFjAf+VLrLmx/8PlYWOGxPu6yBcf427YCkY3HIuoSWUfmnooJCsPN4SMN/kOWUy8j5vC2TcE8/6D2+OMoW77vjjv7mQthUNclwQ7HjeKr37vjhSzv6RgEhJblUkLxMgP+hgoQ6284vYeOQsN/p+Dkl574OnKK7jj5A==
import re

from time import time

from ACEStream.PluginsContainer.livestreamer.plugin import Plugin, PluginError
from ACEStream.PluginsContainer.livestreamer.plugin.api import http, validate
from ACEStream.PluginsContainer.livestreamer.stream import RTMPStream, HLSStream

SWF_URL = "http://play.streamingvideoprovider.com/player2.swf"
API_URL = "http://player.webvideocore.net/index.php"

_url_re = re.compile(
    "http(s)?://(\w+\.)?streamingvideoprovider.co.uk/(?P<channel>[^/&?]+)"
)
_hls_re = re.compile("'(http://.+\.m3u8)'")

_rtmp_schema = validate.Schema(
    validate.xml_findtext("./info/url"),
    validate.url(scheme="rtmp")
)
_hls_schema = validate.Schema(
    validate.transform(_hls_re.search),
    validate.any(
        None,
        validate.all(
            validate.get(1),
            validate.url(
                scheme="http",
                path=validate.endswith("m3u8")
            )
        )
    )
)


class Streamingvideoprovider(Plugin):
    @classmethod
    def can_handle_url(self, url):
        return _url_re.match(url)

    def _get_hls_stream(self, channel_name):
        params = {
            "l": "info",
            "a": "ajax_video_info",
            "file": channel_name,
            "rid": time()
        }
        playlist_url = http.get(API_URL, params=params, schema=_hls_schema)
        if not playlist_url:
            return

        return HLSStream(self.session, playlist_url)

    def _get_rtmp_stream(self, channel_name):
        params = {
            "l": "info",
            "a": "xmlClipPath",
            "clip_id": channel_name,
            "rid": time()
        }
        res = http.get(API_URL, params=params)
        rtmp_url = http.xml(res, schema=_rtmp_schema)

        return RTMPStream(self.session, {
            "rtmp": rtmp_url,
            "swfVfy": SWF_URL,
            "live": True
        })

    def _get_streams(self):
        match = _url_re.match(self.url)
        channel_name = match.group("channel")

        try:
            stream = self._get_rtmp_stream(channel_name)
            yield "live", stream
        except PluginError as err:
            self.logger.error("Unable to extract RTMP stream: {0}", err)

        try:
            stream = self._get_hls_stream(channel_name)
            if stream:
                yield "live", stream
        except PluginError as err:
            self.logger.error("Unable to extract HLS stream: {0}", err)

__plugin__ = Streamingvideoprovider
