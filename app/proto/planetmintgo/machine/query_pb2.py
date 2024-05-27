# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: planetmintgo/machine/query.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from gogoproto import gogo_pb2 as gogoproto_dot_gogo__pb2
from google.api import annotations_pb2 as google_dot_api_dot_annotations__pb2
from cosmos.base.query.v1beta1 import pagination_pb2 as cosmos_dot_base_dot_query_dot_v1beta1_dot_pagination__pb2
from planetmintgo.machine import params_pb2 as planetmintgo_dot_machine_dot_params__pb2
from planetmintgo.machine import machine_pb2 as planetmintgo_dot_machine_dot_machine__pb2
from planetmintgo.machine import liquid_asset_pb2 as planetmintgo_dot_machine_dot_liquid__asset__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n planetmintgo/machine/query.proto\x12\x14planetmintgo.machine\x1a\x14gogoproto/gogo.proto\x1a\x1cgoogle/api/annotations.proto\x1a*cosmos/base/query/v1beta1/pagination.proto\x1a!planetmintgo/machine/params.proto\x1a\"planetmintgo/machine/machine.proto\x1a\'planetmintgo/machine/liquid_asset.proto\"\x14\n\x12QueryParamsRequest\"I\n\x13QueryParamsResponse\x12\x32\n\x06params\x18\x01 \x01(\x0b\x32\x1c.planetmintgo.machine.ParamsB\x04\xc8\xde\x1f\x00\"6\n!QueryGetMachineByPublicKeyRequest\x12\x11\n\tpublicKey\x18\x01 \x01(\t\"T\n\"QueryGetMachineByPublicKeyResponse\x12.\n\x07machine\x18\x01 \x01(\x0b\x32\x1d.planetmintgo.machine.Machine\"5\n QueryGetTrustAnchorStatusRequest\x12\x11\n\tmachineid\x18\x01 \x01(\t\"K\n!QueryGetTrustAnchorStatusResponse\x12\x11\n\tmachineid\x18\x01 \x01(\t\x12\x13\n\x0bisactivated\x18\x02 \x01(\x08\"2\n\x1fQueryGetMachineByAddressRequest\x12\x0f\n\x07\x61\x64\x64ress\x18\x01 \x01(\t\"R\n QueryGetMachineByAddressResponse\x12.\n\x07machine\x18\x01 \x01(\x0b\x32\x1d.planetmintgo.machine.Machine\";\n&QueryGetLiquidAssetsByMachineidRequest\x12\x11\n\tmachineID\x18\x01 \x01(\t\"f\n\'QueryGetLiquidAssetsByMachineidResponse\x12;\n\x10liquidAssetEntry\x18\x01 \x01(\x0b\x32!.planetmintgo.machine.LiquidAsset2\x9c\x07\n\x05Query\x12\x81\x01\n\x06Params\x12(.planetmintgo.machine.QueryParamsRequest\x1a).planetmintgo.machine.QueryParamsResponse\"\"\x82\xd3\xe4\x93\x02\x1c\x12\x1a/planetmint/machine/params\x12\xbe\x01\n\x15GetMachineByPublicKey\x12\x37.planetmintgo.machine.QueryGetMachineByPublicKeyRequest\x1a\x38.planetmintgo.machine.QueryGetMachineByPublicKeyResponse\"2\x82\xd3\xe4\x93\x02,\x12*/planetmint/machine/public_key/{publicKey}\x12\xc4\x01\n\x14GetTrustAnchorStatus\x12\x36.planetmintgo.machine.QueryGetTrustAnchorStatusRequest\x1a\x37.planetmintgo.machine.QueryGetTrustAnchorStatusResponse\";\x82\xd3\xe4\x93\x02\x35\x12\x33/planetmint/machine/trust_anchor/status/{machineid}\x12\xb3\x01\n\x13GetMachineByAddress\x12\x35.planetmintgo.machine.QueryGetMachineByAddressRequest\x1a\x36.planetmintgo.machine.QueryGetMachineByAddressResponse\"-\x82\xd3\xe4\x93\x02\'\x12%/planetmint/machine/address/{address}\x12\xd0\x01\n\x1aGetLiquidAssetsByMachineid\x12<.planetmintgo.machine.QueryGetLiquidAssetsByMachineidRequest\x1a=.planetmintgo.machine.QueryGetLiquidAssetsByMachineidResponse\"5\x82\xd3\xe4\x93\x02/\x12-/planetmint/machine/liquid_assets/{machineID}B5Z3github.com/planetmint/planetmint-go/x/machine/typesb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'planetmintgo.machine.query_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'Z3github.com/planetmint/planetmint-go/x/machine/types'
  _QUERYPARAMSRESPONSE.fields_by_name['params']._options = None
  _QUERYPARAMSRESPONSE.fields_by_name['params']._serialized_options = b'\310\336\037\000'
  _QUERY.methods_by_name['Params']._options = None
  _QUERY.methods_by_name['Params']._serialized_options = b'\202\323\344\223\002\034\022\032/planetmint/machine/params'
  _QUERY.methods_by_name['GetMachineByPublicKey']._options = None
  _QUERY.methods_by_name['GetMachineByPublicKey']._serialized_options = b'\202\323\344\223\002,\022*/planetmint/machine/public_key/{publicKey}'
  _QUERY.methods_by_name['GetTrustAnchorStatus']._options = None
  _QUERY.methods_by_name['GetTrustAnchorStatus']._serialized_options = b'\202\323\344\223\0025\0223/planetmint/machine/trust_anchor/status/{machineid}'
  _QUERY.methods_by_name['GetMachineByAddress']._options = None
  _QUERY.methods_by_name['GetMachineByAddress']._serialized_options = b'\202\323\344\223\002\'\022%/planetmint/machine/address/{address}'
  _QUERY.methods_by_name['GetLiquidAssetsByMachineid']._options = None
  _QUERY.methods_by_name['GetLiquidAssetsByMachineid']._serialized_options = b'\202\323\344\223\002/\022-/planetmint/machine/liquid_assets/{machineID}'
  _QUERYPARAMSREQUEST._serialized_start=266
  _QUERYPARAMSREQUEST._serialized_end=286
  _QUERYPARAMSRESPONSE._serialized_start=288
  _QUERYPARAMSRESPONSE._serialized_end=361
  _QUERYGETMACHINEBYPUBLICKEYREQUEST._serialized_start=363
  _QUERYGETMACHINEBYPUBLICKEYREQUEST._serialized_end=417
  _QUERYGETMACHINEBYPUBLICKEYRESPONSE._serialized_start=419
  _QUERYGETMACHINEBYPUBLICKEYRESPONSE._serialized_end=503
  _QUERYGETTRUSTANCHORSTATUSREQUEST._serialized_start=505
  _QUERYGETTRUSTANCHORSTATUSREQUEST._serialized_end=558
  _QUERYGETTRUSTANCHORSTATUSRESPONSE._serialized_start=560
  _QUERYGETTRUSTANCHORSTATUSRESPONSE._serialized_end=635
  _QUERYGETMACHINEBYADDRESSREQUEST._serialized_start=637
  _QUERYGETMACHINEBYADDRESSREQUEST._serialized_end=687
  _QUERYGETMACHINEBYADDRESSRESPONSE._serialized_start=689
  _QUERYGETMACHINEBYADDRESSRESPONSE._serialized_end=771
  _QUERYGETLIQUIDASSETSBYMACHINEIDREQUEST._serialized_start=773
  _QUERYGETLIQUIDASSETSBYMACHINEIDREQUEST._serialized_end=832
  _QUERYGETLIQUIDASSETSBYMACHINEIDRESPONSE._serialized_start=834
  _QUERYGETLIQUIDASSETSBYMACHINEIDRESPONSE._serialized_end=936
  _QUERY._serialized_start=939
  _QUERY._serialized_end=1863
# @@protoc_insertion_point(module_scope)