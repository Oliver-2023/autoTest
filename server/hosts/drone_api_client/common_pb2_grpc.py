# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

import common_pb2 as common__pb2


class CommonStub(object):
  """Common lab services implemented on top of the wiring APIs.

  The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
  NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
  "OPTIONAL" in this document are to be interpreted as described in
  RFC 2119.

  All clients SHOULD pass the gRPC metadata key request_trace_id with one
  value. The value is a unique string that is associated with the method call
  in metrics. Clients that do not pass request_trace_id MAY be rejected so that
  they can be fixed.
  """

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.ExecDutCommand = channel.unary_stream(
        '/chromiumos.config.api.test.tls.Common/ExecDutCommand',
        request_serializer=common__pb2.ExecDutCommandRequest.SerializeToString,
        response_deserializer=common__pb2.ExecDutCommandResponse.FromString,
        )


class CommonServicer(object):
  """Common lab services implemented on top of the wiring APIs.

  The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
  NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
  "OPTIONAL" in this document are to be interpreted as described in
  RFC 2119.

  All clients SHOULD pass the gRPC metadata key request_trace_id with one
  value. The value is a unique string that is associated with the method call
  in metrics. Clients that do not pass request_trace_id MAY be rejected so that
  they can be fixed.
  """

  def ExecDutCommand(self, request, context):
    """ExecDutCommand runs a command on a DUT.

    The working directory is /.
    A tty is not spawned for the command.
    The user and group is root.
    All signals have their default dispositions and are not masked.
    The umask is set to 0.

    The environment contains:

    TERM=dumb
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/bin
    LANG=en_US.UTF-8
    USER=root
    HOME=/root

    The environment MAY also contain SSH client variables.
    The environment SHALL NOT contain variables not mentioned above.

    If the stream is interrupted, the implementation MAY attempt to
    stop the command by sending SIGINT, SIGHUP, SIGTERM, or SIGKILL.
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_CommonServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'ExecDutCommand': grpc.unary_stream_rpc_method_handler(
          servicer.ExecDutCommand,
          request_deserializer=common__pb2.ExecDutCommandRequest.FromString,
          response_serializer=common__pb2.ExecDutCommandResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'chromiumos.config.api.test.tls.Common', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
