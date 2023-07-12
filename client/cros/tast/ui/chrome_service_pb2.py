# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chrome_service.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='chrome_service.proto',
  package='tast.cros.browser',
  syntax='proto3',
  serialized_options=b'Z0go.chromium.org/tast-tests/cros/services/cros/ui',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x14\x63hrome_service.proto\x12\x11tast.cros.browser\x1a\x1bgoogle/protobuf/empty.proto\"\xda\x05\n\nNewRequest\x12\x30\n\nlogin_mode\x18\x01 \x01(\x0e\x32\x1c.tast.cros.browser.LoginMode\x12>\n\x0b\x63redentials\x18\x02 \x01(\x0b\x32).tast.cros.browser.NewRequest.Credentials\x12\x17\n\x0f\x65nable_features\x18\x03 \x03(\t\x12\x18\n\x10\x64isable_features\x18\x04 \x03(\t\x12\x12\n\nextra_args\x18\x05 \x03(\t\x12\x12\n\nkeep_state\x18\x06 \x01(\x08\x12\x19\n\x11try_reuse_session\x18\x07 \x01(\x08\x12\x1e\n\x16lacros_enable_features\x18\x08 \x03(\t\x12\x1f\n\x17lacros_disable_features\x18\t \x03(\t\x12\x19\n\x11lacros_extra_args\x18\n \x03(\t\x12)\n\x06lacros\x18\x0b \x01(\x0b\x32\x19.tast.cros.browser.Lacros\x12,\n\x08\x61rc_mode\x18\x0c \x01(\x0e\x32\x1a.tast.cros.browser.ArcMode\x12!\n\x19\x65nable_hid_screen_on_oobe\x18\r \x01(\x08\x12(\n signin_profile_test_extension_id\x18\x0e \x01(\t\x12\x1b\n\x13unpacked_extensions\x18\x0f \x03(\t\x12\"\n\x1alacros_unpacked_extensions\x18\x10 \x03(\t\x12\x19\n\x11lacros_keep_alive\x18\x11 \x01(\x08\x1a\x85\x01\n\x0b\x43redentials\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\x12\x0f\n\x07gaia_id\x18\x03 \x01(\t\x12\x0f\n\x07\x63ontact\x18\x04 \x01(\t\x12\x17\n\x0fparent_username\x18\x05 \x01(\t\x12\x17\n\x0fparent_password\x18\x06 \x01(\t\"\x99\x01\n\x06Lacros\x12\x36\n\tselection\x18\x02 \x01(\x0e\x32#.tast.cros.browser.Lacros.Selection\"Q\n\tSelection\x12\x19\n\x15SELECTION_UNSPECIFIED\x10\x00\x12\x14\n\x10SELECTION_ROOTFS\x10\x01\x12\x13\n\x0fSELECTION_OMAHA\x10\x02J\x04\x08\x01\x10\x02*\x92\x01\n\tLoginMode\x12\x1a\n\x16LOGIN_MODE_UNSPECIFIED\x10\x00\x12\x17\n\x13LOGIN_MODE_NO_LOGIN\x10\x01\x12\x19\n\x15LOGIN_MODE_FAKE_LOGIN\x10\x02\x12\x19\n\x15LOGIN_MODE_GAIA_LOGIN\x10\x03\x12\x1a\n\x16LOGIN_MODE_GUEST_LOGIN\x10\x04*h\n\x07\x41rcMode\x12\x18\n\x14\x41RC_MODE_UNSPECIFIED\x10\x00\x12\x15\n\x11\x41RC_MODE_DISABLED\x10\x01\x12\x14\n\x10\x41RC_MODE_ENABLED\x10\x02\x12\x16\n\x12\x41RC_MODE_SUPPORTED\x10\x03\x32\xc9\x01\n\rChromeService\x12>\n\x03New\x12\x1d.tast.cros.browser.NewRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x39\n\x05\x43lose\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x12=\n\tReconnect\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty\"\x00\x42\x32Z0go.chromium.org/tast-tests/cros/services/cros/uib\x06proto3'
  ,
  dependencies=[google_dot_protobuf_dot_empty__pb2.DESCRIPTOR,])

_LOGINMODE = _descriptor.EnumDescriptor(
  name='LoginMode',
  full_name='tast.cros.browser.LoginMode',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='LOGIN_MODE_UNSPECIFIED', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='LOGIN_MODE_NO_LOGIN', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='LOGIN_MODE_FAKE_LOGIN', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='LOGIN_MODE_GAIA_LOGIN', index=3, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='LOGIN_MODE_GUEST_LOGIN', index=4, number=4,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=962,
  serialized_end=1108,
)
_sym_db.RegisterEnumDescriptor(_LOGINMODE)

LoginMode = enum_type_wrapper.EnumTypeWrapper(_LOGINMODE)
_ARCMODE = _descriptor.EnumDescriptor(
  name='ArcMode',
  full_name='tast.cros.browser.ArcMode',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='ARC_MODE_UNSPECIFIED', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='ARC_MODE_DISABLED', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='ARC_MODE_ENABLED', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='ARC_MODE_SUPPORTED', index=3, number=3,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1110,
  serialized_end=1214,
)
_sym_db.RegisterEnumDescriptor(_ARCMODE)

ArcMode = enum_type_wrapper.EnumTypeWrapper(_ARCMODE)
LOGIN_MODE_UNSPECIFIED = 0
LOGIN_MODE_NO_LOGIN = 1
LOGIN_MODE_FAKE_LOGIN = 2
LOGIN_MODE_GAIA_LOGIN = 3
LOGIN_MODE_GUEST_LOGIN = 4
ARC_MODE_UNSPECIFIED = 0
ARC_MODE_DISABLED = 1
ARC_MODE_ENABLED = 2
ARC_MODE_SUPPORTED = 3


_LACROS_SELECTION = _descriptor.EnumDescriptor(
  name='Selection',
  full_name='tast.cros.browser.Lacros.Selection',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='SELECTION_UNSPECIFIED', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='SELECTION_ROOTFS', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='SELECTION_OMAHA', index=2, number=2,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=872,
  serialized_end=953,
)
_sym_db.RegisterEnumDescriptor(_LACROS_SELECTION)


_NEWREQUEST_CREDENTIALS = _descriptor.Descriptor(
  name='Credentials',
  full_name='tast.cros.browser.NewRequest.Credentials',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='username', full_name='tast.cros.browser.NewRequest.Credentials.username', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='password', full_name='tast.cros.browser.NewRequest.Credentials.password', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='gaia_id', full_name='tast.cros.browser.NewRequest.Credentials.gaia_id', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='contact', full_name='tast.cros.browser.NewRequest.Credentials.contact', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='parent_username', full_name='tast.cros.browser.NewRequest.Credentials.parent_username', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='parent_password', full_name='tast.cros.browser.NewRequest.Credentials.parent_password', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
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
  serialized_start=670,
  serialized_end=803,
)

_NEWREQUEST = _descriptor.Descriptor(
  name='NewRequest',
  full_name='tast.cros.browser.NewRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='login_mode', full_name='tast.cros.browser.NewRequest.login_mode', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='credentials', full_name='tast.cros.browser.NewRequest.credentials', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='enable_features', full_name='tast.cros.browser.NewRequest.enable_features', index=2,
      number=3, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='disable_features', full_name='tast.cros.browser.NewRequest.disable_features', index=3,
      number=4, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='extra_args', full_name='tast.cros.browser.NewRequest.extra_args', index=4,
      number=5, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='keep_state', full_name='tast.cros.browser.NewRequest.keep_state', index=5,
      number=6, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='try_reuse_session', full_name='tast.cros.browser.NewRequest.try_reuse_session', index=6,
      number=7, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lacros_enable_features', full_name='tast.cros.browser.NewRequest.lacros_enable_features', index=7,
      number=8, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lacros_disable_features', full_name='tast.cros.browser.NewRequest.lacros_disable_features', index=8,
      number=9, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lacros_extra_args', full_name='tast.cros.browser.NewRequest.lacros_extra_args', index=9,
      number=10, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lacros', full_name='tast.cros.browser.NewRequest.lacros', index=10,
      number=11, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='arc_mode', full_name='tast.cros.browser.NewRequest.arc_mode', index=11,
      number=12, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='enable_hid_screen_on_oobe', full_name='tast.cros.browser.NewRequest.enable_hid_screen_on_oobe', index=12,
      number=13, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='signin_profile_test_extension_id', full_name='tast.cros.browser.NewRequest.signin_profile_test_extension_id', index=13,
      number=14, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='unpacked_extensions', full_name='tast.cros.browser.NewRequest.unpacked_extensions', index=14,
      number=15, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lacros_unpacked_extensions', full_name='tast.cros.browser.NewRequest.lacros_unpacked_extensions', index=15,
      number=16, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lacros_keep_alive', full_name='tast.cros.browser.NewRequest.lacros_keep_alive', index=16,
      number=17, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_NEWREQUEST_CREDENTIALS, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=73,
  serialized_end=803,
)


_LACROS = _descriptor.Descriptor(
  name='Lacros',
  full_name='tast.cros.browser.Lacros',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='selection', full_name='tast.cros.browser.Lacros.selection', index=0,
      number=2, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _LACROS_SELECTION,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=806,
  serialized_end=959,
)

_NEWREQUEST_CREDENTIALS.containing_type = _NEWREQUEST
_NEWREQUEST.fields_by_name['login_mode'].enum_type = _LOGINMODE
_NEWREQUEST.fields_by_name['credentials'].message_type = _NEWREQUEST_CREDENTIALS
_NEWREQUEST.fields_by_name['lacros'].message_type = _LACROS
_NEWREQUEST.fields_by_name['arc_mode'].enum_type = _ARCMODE
_LACROS.fields_by_name['selection'].enum_type = _LACROS_SELECTION
_LACROS_SELECTION.containing_type = _LACROS
DESCRIPTOR.message_types_by_name['NewRequest'] = _NEWREQUEST
DESCRIPTOR.message_types_by_name['Lacros'] = _LACROS
DESCRIPTOR.enum_types_by_name['LoginMode'] = _LOGINMODE
DESCRIPTOR.enum_types_by_name['ArcMode'] = _ARCMODE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

NewRequest = _reflection.GeneratedProtocolMessageType('NewRequest', (_message.Message,), {

  'Credentials' : _reflection.GeneratedProtocolMessageType('Credentials', (_message.Message,), {
    'DESCRIPTOR' : _NEWREQUEST_CREDENTIALS,
    '__module__' : 'chrome_service_pb2'
    # @@protoc_insertion_point(class_scope:tast.cros.browser.NewRequest.Credentials)
    })
  ,
  'DESCRIPTOR' : _NEWREQUEST,
  '__module__' : 'chrome_service_pb2'
  # @@protoc_insertion_point(class_scope:tast.cros.browser.NewRequest)
  })
_sym_db.RegisterMessage(NewRequest)
_sym_db.RegisterMessage(NewRequest.Credentials)

Lacros = _reflection.GeneratedProtocolMessageType('Lacros', (_message.Message,), {
  'DESCRIPTOR' : _LACROS,
  '__module__' : 'chrome_service_pb2'
  # @@protoc_insertion_point(class_scope:tast.cros.browser.Lacros)
  })
_sym_db.RegisterMessage(Lacros)


DESCRIPTOR._options = None

_CHROMESERVICE = _descriptor.ServiceDescriptor(
  name='ChromeService',
  full_name='tast.cros.browser.ChromeService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=1217,
  serialized_end=1418,
  methods=[
  _descriptor.MethodDescriptor(
    name='New',
    full_name='tast.cros.browser.ChromeService.New',
    index=0,
    containing_service=None,
    input_type=_NEWREQUEST,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='Close',
    full_name='tast.cros.browser.ChromeService.Close',
    index=1,
    containing_service=None,
    input_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='Reconnect',
    full_name='tast.cros.browser.ChromeService.Reconnect',
    index=2,
    containing_service=None,
    input_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_CHROMESERVICE)

DESCRIPTOR.services_by_name['ChromeService'] = _CHROMESERVICE

# @@protoc_insertion_point(module_scope)
