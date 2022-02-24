__all__ = ['RTTCodecList', 'RTTStream']

from sipsimple.streams.rtp import RTPStream
from sipsimple.streams import InvalidStreamError, UnknownStreamError
from sipsimple.core import RTTTransport
from sipsimple.configuration.settings import SIPSimpleSettings
from sipsimple.configuration.datatypes import CodecList

class RTTCodecList(CodecList):
    available_values = {'t140', 'red'}

class RTTStream(RTPStream):
    type = 'text'
    priority = 1

    @classmethod
    def new_from_sdp(cls, session, remote_sdp, stream_index):
        # TODO: actually validate the SDP
        settings = SIPSimpleSettings()
        remote_stream = remote_sdp.media[stream_index]
        if remote_stream.media != cls.type.encode():
            raise UnknownStreamError
        if remote_stream.transport not in (b'RTP/AVP', b'RTP/SAVP'):
            raise InvalidStreamError("expected RTP/AVP or RTP/SAVP transport in %s stream, got %s" % (cls.type, remote_stream.transport.decode()))
        local_encryption_policy = session.account.rtp.encryption.key_negotiation if session.account.rtp.encryption.enabled else None
        
        if local_encryption_policy == "sdes_mandatory" and not b'crypto' in remote_stream.attributes:
            raise InvalidStreamError("SRTP/SDES is locally mandatory but it's not remotely enabled")
        if remote_stream.transport == b'RTP/SAVP' and b'crypto' in remote_stream.attributes and local_encryption_policy not in ("opportunistic", "sdes_optional", "sdes_mandatory"):
            raise InvalidStreamError("SRTP/SDES is remotely mandatory but it's not locally enabled")
        account_preferred_codecs = getattr(session.account.rtp, '%s_codec_list' % cls.type)
        general_codecs = getattr(settings.rtp, '%s_codec_list' % cls.type)
        supported_codecs = account_preferred_codecs or general_codecs
        if not any(codec for codec in remote_stream.codec_list if codec in supported_codecs):
            if remote_stream.media != b'text':
                raise InvalidStreamError("no compatible codecs found")
        stream = cls()
        stream._incoming_remote_sdp = remote_sdp
        stream._incoming_stream_index = stream_index
        return stream

    def _create_transport(self, rtp_transport, remote_sdp=None, stream_index=None):
        return RTTTransport(rtp_transport, remote_sdp=remote_sdp, sdp_index=stream_index or 0)

    def _check_hold(self, direction, is_initial):
        print('TODO: _check_hold')

    def _pause(self):
        print('TODO: _pause')

    def _resume(self):
        print('TODO: _resume')

    def deactivate(self):
        print('TODO: deactivate')

    def end(self):
        print('TODO: end')

    def reset(self, stream_index):
        print('TODO: reset')

    def start(self, local_sdp, remote_sdp, stream_index):
        with self._lock:
            if self.state != "INITIALIZED":
                raise RuntimeError("RTTStream.start() may only be called in the INITIALIZED state")
            settings = SIPSimpleSettings()
            self._transport.start(local_sdp, remote_sdp, stream_index, timeout=settings.rtp.timeout)
            self._save_remote_sdp_rtp_info(remote_sdp, stream_index)
            self._check_hold(self._transport.direction.decode(), True)
            if self._try_ice and self._ice_state == "NULL":
                self.state = 'WAIT_ICE'
            else:
                self.state = 'ESTABLISHED'
                self.notification_center.post_notification('MediaStreamDidStart', sender=self)

    def update(self, local_sdp, remote_sdp, stream_index):
        print('TODO: update')

    def validate_update(self, remote_sdp, stream_index):
        print('TODO: validate_update')
