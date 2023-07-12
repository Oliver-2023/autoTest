# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import chrome_service_pb2 as chrome__service__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


class ChromeServiceStub(object):
    """ChromeService provides functions for managing chrome lifecycle, like
    creating and closing chrome sessions.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.New = channel.unary_unary(
                '/tast.cros.browser.ChromeService/New',
                request_serializer=chrome__service__pb2.NewRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.Close = channel.unary_unary(
                '/tast.cros.browser.ChromeService/Close',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.Reconnect = channel.unary_unary(
                '/tast.cros.browser.ChromeService/Reconnect',
                request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )


class ChromeServiceServicer(object):
    """ChromeService provides functions for managing chrome lifecycle, like
    creating and closing chrome sessions.
    """

    def New(self, request, context):
        """New enables testing for Chrome and logs into a Chrome session.
        When try_reuse_session is set to true, service tries to reuse existing
        chrome session if the reuse criteria is met.
        Close must be called later to clean up the associated resources.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Close(self, request, context):
        """Close releases the chrome session obtained by New.
        When there is no chrome session, calling Close returns an error.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Reconnect(self, request, context):
        """Reconnect reconnects to the current browser session.

        This method is called when connection need to be re-established, e.g. after suspend/resume.
        After the session is reconnected, all existing connections associated with chrome.Chrome instance also
        needs to be re-established. For example, chrome.TestAPIConn(), chrome.NewConn().

        Note that this method cannot be used to recover Chrome after crashes since the devtools port may change.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ChromeServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'New': grpc.unary_unary_rpc_method_handler(
                    servicer.New,
                    request_deserializer=chrome__service__pb2.NewRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'Close': grpc.unary_unary_rpc_method_handler(
                    servicer.Close,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'Reconnect': grpc.unary_unary_rpc_method_handler(
                    servicer.Reconnect,
                    request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'tast.cros.browser.ChromeService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class ChromeService(object):
    """ChromeService provides functions for managing chrome lifecycle, like
    creating and closing chrome sessions.
    """

    @staticmethod
    def New(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/tast.cros.browser.ChromeService/New',
            chrome__service__pb2.NewRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Close(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/tast.cros.browser.ChromeService/Close',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Reconnect(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/tast.cros.browser.ChromeService/Reconnect',
            google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
