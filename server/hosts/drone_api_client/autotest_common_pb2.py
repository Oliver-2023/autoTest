# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: autotest_common.proto

from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='autotest_common.proto',
  package='chromiumos.config.api.test.tls',
  syntax='proto3',
  serialized_options=b'Z1go.chromium.org/chromiumos/config/go/api/test/tls',
  serialized_pb=b'\n\x15\x61utotest_common.proto\x12\x1e\x63hromiumos.config.api.test.tls\"\xc3\x01\n\x15\x45xecDutCommandRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07\x63ommand\x18\x02 \x01(\t\x12\x0c\n\x04\x61rgs\x18\x03 \x03(\t\x12\r\n\x05stdin\x18\x04 \x01(\x0c\x12\x36\n\x06stdout\x18\x05 \x01(\x0e\x32&.chromiumos.config.api.test.tls.Output\x12\x36\n\x06stderr\x18\x06 \x01(\x0e\x32&.chromiumos.config.api.test.tls.Output\"\xe2\x01\n\x16\x45xecDutCommandResponse\x12R\n\texit_info\x18\x01 \x01(\x0b\x32?.chromiumos.config.api.test.tls.ExecDutCommandResponse.ExitInfo\x12\x0e\n\x06stdout\x18\x02 \x01(\x0c\x12\x0e\n\x06stderr\x18\x03 \x01(\x0c\x1aT\n\x08\x45xitInfo\x12\x0e\n\x06status\x18\x01 \x01(\x05\x12\x10\n\x08signaled\x18\x02 \x01(\x08\x12\x0f\n\x07started\x18\x03 \x01(\x08\x12\x15\n\rerror_message\x18\x04 \x01(\t*,\n\x06Output\x12\x0f\n\x0bOUTPUT_PIPE\x10\x00\x12\x11\n\rOUTPUT_STDOUT\x10\x01\x32\x8c\x01\n\x06\x43ommon\x12\x81\x01\n\x0e\x45xecDutCommand\x12\x35.chromiumos.config.api.test.tls.ExecDutCommandRequest\x1a\x36.chromiumos.config.api.test.tls.ExecDutCommandResponse0\x01\x42\x33Z1go.chromium.org/chromiumos/config/go/api/test/tlsb\x06proto3'
)

_OUTPUT = _descriptor.EnumDescriptor(
  name='Output',
  full_name='chromiumos.config.api.test.tls.Output',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='OUTPUT_PIPE', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='OUTPUT_STDOUT', index=1, number=1,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=484,
  serialized_end=528,
)
_sym_db.RegisterEnumDescriptor(_OUTPUT)

Output = enum_type_wrapper.EnumTypeWrapper(_OUTPUT)
OUTPUT_PIPE = 0
OUTPUT_STDOUT = 1



_EXECDUTCOMMANDREQUEST = _descriptor.Descriptor(
  name='ExecDutCommandRequest',
  full_name='chromiumos.config.api.test.tls.ExecDutCommandRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='chromiumos.config.api.test.tls.ExecDutCommandRequest.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='command', full_name='chromiumos.config.api.test.tls.ExecDutCommandRequest.command', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='args', full_name='chromiumos.config.api.test.tls.ExecDutCommandRequest.args', index=2,
      number=3, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='stdin', full_name='chromiumos.config.api.test.tls.ExecDutCommandRequest.stdin', index=3,
      number=4, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='stdout', full_name='chromiumos.config.api.test.tls.ExecDutCommandRequest.stdout', index=4,
      number=5, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='stderr', full_name='chromiumos.config.api.test.tls.ExecDutCommandRequest.stderr', index=5,
      number=6, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=58,
  serialized_end=253,
)


_EXECDUTCOMMANDRESPONSE_EXITINFO = _descriptor.Descriptor(
  name='ExitInfo',
  full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse.ExitInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='status', full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse.ExitInfo.status', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='signaled', full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse.ExitInfo.signaled', index=1,
      number=2, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='started', full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse.ExitInfo.started', index=2,
      number=3, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='error_message', full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse.ExitInfo.error_message', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
  serialized_start=398,
  serialized_end=482,
)

_EXECDUTCOMMANDRESPONSE = _descriptor.Descriptor(
  name='ExecDutCommandResponse',
  full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='exit_info', full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse.exit_info', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='stdout', full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse.stdout', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='stderr', full_name='chromiumos.config.api.test.tls.ExecDutCommandResponse.stderr', index=2,
      number=3, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_EXECDUTCOMMANDRESPONSE_EXITINFO, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=256,
  serialized_end=482,
)

_EXECDUTCOMMANDREQUEST.fields_by_name['stdout'].enum_type = _OUTPUT
_EXECDUTCOMMANDREQUEST.fields_by_name['stderr'].enum_type = _OUTPUT
_EXECDUTCOMMANDRESPONSE_EXITINFO.containing_type = _EXECDUTCOMMANDRESPONSE
_EXECDUTCOMMANDRESPONSE.fields_by_name['exit_info'].message_type = _EXECDUTCOMMANDRESPONSE_EXITINFO
DESCRIPTOR.message_types_by_name['ExecDutCommandRequest'] = _EXECDUTCOMMANDREQUEST
DESCRIPTOR.message_types_by_name['ExecDutCommandResponse'] = _EXECDUTCOMMANDRESPONSE
DESCRIPTOR.enum_types_by_name['Output'] = _OUTPUT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ExecDutCommandRequest = _reflection.GeneratedProtocolMessageType('ExecDutCommandRequest', (_message.Message,), {
  'DESCRIPTOR' : _EXECDUTCOMMANDREQUEST,
  '__module__' : 'autotest_common_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.config.api.test.tls.ExecDutCommandRequest)
  })
_sym_db.RegisterMessage(ExecDutCommandRequest)

ExecDutCommandResponse = _reflection.GeneratedProtocolMessageType('ExecDutCommandResponse', (_message.Message,), {

  'ExitInfo' : _reflection.GeneratedProtocolMessageType('ExitInfo', (_message.Message,), {
    'DESCRIPTOR' : _EXECDUTCOMMANDRESPONSE_EXITINFO,
    '__module__' : 'autotest_common_pb2'
    # @@protoc_insertion_point(class_scope:chromiumos.config.api.test.tls.ExecDutCommandResponse.ExitInfo)
    })
  ,
  'DESCRIPTOR' : _EXECDUTCOMMANDRESPONSE,
  '__module__' : 'autotest_common_pb2'
  # @@protoc_insertion_point(class_scope:chromiumos.config.api.test.tls.ExecDutCommandResponse)
  })
_sym_db.RegisterMessage(ExecDutCommandResponse)
_sym_db.RegisterMessage(ExecDutCommandResponse.ExitInfo)


DESCRIPTOR._options = None

_COMMON = _descriptor.ServiceDescriptor(
  name='Common',
  full_name='chromiumos.config.api.test.tls.Common',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=531,
  serialized_end=671,
  methods=[
  _descriptor.MethodDescriptor(
    name='ExecDutCommand',
    full_name='chromiumos.config.api.test.tls.Common.ExecDutCommand',
    index=0,
    containing_service=None,
    input_type=_EXECDUTCOMMANDREQUEST,
    output_type=_EXECDUTCOMMANDRESPONSE,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_COMMON)

DESCRIPTOR.services_by_name['Common'] = _COMMON

# @@protoc_insertion_point(module_scope)