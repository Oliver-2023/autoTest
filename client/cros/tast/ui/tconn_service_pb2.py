# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: tconn_service.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='tconn_service.proto',
  package='tast.cros.ui',
  syntax='proto3',
  serialized_options=b'Z chromiumos/tast/services/cros/ui',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x13tconn_service.proto\x12\x0ctast.cros.ui\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1cgoogle/protobuf/struct.proto\"3\n\x0b\x45valRequest\x12\x0c\n\x04\x65xpr\x18\x01 \x01(\t\x12\x16\n\x0e\x63\x61ll_on_lacros\x18\x02 \x01(\x08\"W\n\x0b\x43\x61llRequest\x12\n\n\x02\x66n\x18\x01 \x01(\t\x12$\n\x04\x61rgs\x18\x02 \x03(\x0b\x32\x16.google.protobuf.Value\x12\x16\n\x0e\x63\x61ll_on_lacros\x18\x03 \x01(\x08\"e\n\x12WaitForExprRequest\x12\x0c\n\x04\x65xpr\x18\x01 \x01(\t\x12\x14\n\x0ctimeout_secs\x18\x02 \x01(\r\x12\x13\n\x0b\x66\x61il_on_err\x18\x03 \x01(\x08\x12\x16\n\x0e\x63\x61ll_on_lacros\x18\x04 \x01(\x08\x32\x98\x02\n\x0cTconnService\x12;\n\x04\x45val\x12\x19.tast.cros.ui.EvalRequest\x1a\x16.google.protobuf.Value\"\x00\x12;\n\x04\x43\x61ll\x12\x19.tast.cros.ui.CallRequest\x1a\x16.google.protobuf.Value\"\x00\x12I\n\x0bWaitForExpr\x12 .tast.cros.ui.WaitForExprRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x43\n\x0fResetAutomation\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x42\"Z chromiumos/tast/services/cros/uib\x06proto3'
  ,
  dependencies=[google_dot_protobuf_dot_empty__pb2.DESCRIPTOR,google_dot_protobuf_dot_struct__pb2.DESCRIPTOR,])




_EVALREQUEST = _descriptor.Descriptor(
  name='EvalRequest',
  full_name='tast.cros.ui.EvalRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='expr', full_name='tast.cros.ui.EvalRequest.expr', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='call_on_lacros', full_name='tast.cros.ui.EvalRequest.call_on_lacros', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=96,
  serialized_end=147,
)


_CALLREQUEST = _descriptor.Descriptor(
  name='CallRequest',
  full_name='tast.cros.ui.CallRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='fn', full_name='tast.cros.ui.CallRequest.fn', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='args', full_name='tast.cros.ui.CallRequest.args', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='call_on_lacros', full_name='tast.cros.ui.CallRequest.call_on_lacros', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=149,
  serialized_end=236,
)


_WAITFOREXPRREQUEST = _descriptor.Descriptor(
  name='WaitForExprRequest',
  full_name='tast.cros.ui.WaitForExprRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='expr', full_name='tast.cros.ui.WaitForExprRequest.expr', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='timeout_secs', full_name='tast.cros.ui.WaitForExprRequest.timeout_secs', index=1,
      number=2, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='fail_on_err', full_name='tast.cros.ui.WaitForExprRequest.fail_on_err', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='call_on_lacros', full_name='tast.cros.ui.WaitForExprRequest.call_on_lacros', index=3,
      number=4, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=238,
  serialized_end=339,
)

_CALLREQUEST.fields_by_name['args'].message_type = google_dot_protobuf_dot_struct__pb2._VALUE
DESCRIPTOR.message_types_by_name['EvalRequest'] = _EVALREQUEST
DESCRIPTOR.message_types_by_name['CallRequest'] = _CALLREQUEST
DESCRIPTOR.message_types_by_name['WaitForExprRequest'] = _WAITFOREXPRREQUEST
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

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


DESCRIPTOR._options = None

_TCONNSERVICE = _descriptor.ServiceDescriptor(
  name='TconnService',
  full_name='tast.cros.ui.TconnService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=342,
  serialized_end=622,
  methods=[
  _descriptor.MethodDescriptor(
    name='Eval',
    full_name='tast.cros.ui.TconnService.Eval',
    index=0,
    containing_service=None,
    input_type=_EVALREQUEST,
    output_type=google_dot_protobuf_dot_struct__pb2._VALUE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='Call',
    full_name='tast.cros.ui.TconnService.Call',
    index=1,
    containing_service=None,
    input_type=_CALLREQUEST,
    output_type=google_dot_protobuf_dot_struct__pb2._VALUE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='WaitForExpr',
    full_name='tast.cros.ui.TconnService.WaitForExpr',
    index=2,
    containing_service=None,
    input_type=_WAITFOREXPRREQUEST,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='ResetAutomation',
    full_name='tast.cros.ui.TconnService.ResetAutomation',
    index=3,
    containing_service=None,
    input_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_TCONNSERVICE)

DESCRIPTOR.services_by_name['TconnService'] = _TCONNSERVICE

# @@protoc_insertion_point(module_scope)