# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: planetmintgo/asset/genesis.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from gogoproto import gogo_pb2 as gogoproto_dot_gogo__pb2
from planetmintgo.asset import params_pb2 as planetmintgo_dot_asset_dot_params__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n planetmintgo/asset/genesis.proto\x12\x12planetmintgo.asset\x1a\x14gogoproto/gogo.proto\x1a\x1fplanetmintgo/asset/params.proto\"@\n\x0cGenesisState\x12\x30\n\x06params\x18\x01 \x01(\x0b\x32\x1a.planetmintgo.asset.ParamsB\x04\xc8\xde\x1f\x00\x42\x33Z1github.com/planetmint/planetmint-go/x/asset/typesb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'planetmintgo.asset.genesis_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z1github.com/planetmint/planetmint-go/x/asset/types'
  _GENESISSTATE.fields_by_name['params']._options = None
  _GENESISSTATE.fields_by_name['params']._serialized_options = b'\310\336\037\000'
  _GENESISSTATE._serialized_start=111
  _GENESISSTATE._serialized_end=175
# @@protoc_insertion_point(module_scope)