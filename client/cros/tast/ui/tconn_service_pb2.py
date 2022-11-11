# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: tconn_service.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13tconn_service.proto\x12\x0ctast.cros.ui\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1cgoogle/protobuf/struct.proto\"\x1b\n\x0b\x45valRequest\x12\x0c\n\x04\x65xpr\x18\x01 \x01(\t\"?\n\x0b\x43\x61llRequest\x12\n\n\x02\x66n\x18\x01 \x01(\t\x12$\n\x04\x61rgs\x18\x02 \x03(\x0b\x32\x16.google.protobuf.Value\"M\n\x12WaitForExprRequest\x12\x0c\n\x04\x65xpr\x18\x01 \x01(\t\x12\x14\n\x0ctimeout_secs\x18\x02 \x01(\r\x12\x13\n\x0b\x66\x61il_on_err\x18\x03 \x01(\x08\x32\x98\x02\n\x0cTconnService\x12;\n\x04\x45val\x12\x19.tast.cros.ui.EvalRequest\x1a\x16.google.protobuf.Value\"\x00\x12;\n\x04\x43\x61ll\x12\x19.tast.cros.ui.CallRequest\x1a\x16.google.protobuf.Value\"\x00\x12I\n\x0bWaitForExpr\x12 .tast.cros.ui.WaitForExprRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x43\n\x0fResetAutomation\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x42\"Z chromiumos/tast/services/cros/uib\x06proto3')



_EVALREQUEST = DESCRIPTOR.message_types_by_name['EvalRequest']
_CALLREQUEST = DESCRIPTOR.message_types_by_name['CallRequest']
_WAITFOREXPRREQUEST = DESCRIPTOR.message_types_by_name['WaitForExprRequest']
EvalRequest = _reflection.GeneratedProtocolMessageType('EvalRequest', (_message.Message,), {
  'DESCRIPTOR' : _EVALREQUEST,
  '__module__' : 'tconn_service_pb2'
  # @@protoc_insertion_point(class_scope:tast.cros.ui.EvalRequest)
  })
_sym_db.RegisterMessage(EvalRequest)

CallRequest = _reflection.GeneratedProtocolMessageType('CallRequest', (_message.Message,), {
  'DESCRIPTOR' : _CALLREQUEST,
  '__module__' : 'tconn_service_pb2'
  # @@protoc_insertion_point(class_scope:tast.cros.ui.CallRequest)
  })
_sym_db.RegisterMessage(CallRequest)

WaitForExprRequest = _reflection.GeneratedProtocolMessageType('WaitForExprRequest', (_message.Message,), {
  'DESCRIPTOR' : _WAITFOREXPRREQUEST,
  '__module__' : 'tconn_service_pb2'
  # @@protoc_insertion_point(class_scope:tast.cros.ui.WaitForExprRequest)
  })
_sym_db.RegisterMessage(WaitForExprRequest)

_TCONNSERVICE = DESCRIPTOR.services_by_name['TconnService']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z chromiumos/tast/services/cros/ui'
  _EVALREQUEST._serialized_start=96
  _EVALREQUEST._serialized_end=123
  _CALLREQUEST._serialized_start=125
  _CALLREQUEST._serialized_end=188
  _WAITFOREXPRREQUEST._serialized_start=190
  _WAITFOREXPRREQUEST._serialized_end=267
  _TCONNSERVICE._serialized_start=270
  _TCONNSERVICE._serialized_end=550
# @@protoc_insertion_point(module_scope)