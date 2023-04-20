# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from app.proto.MeterConnectorProto import meter_connector_pb2 as MeterConnectorProto_dot_meter__connector__pb2


class MeterConnectorStub(object):
    """The greeting service definition."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.readMeter = channel.unary_unary(
            "/MeterConnectorProto.MeterConnector/readMeter",
            request_serializer=MeterConnectorProto_dot_meter__connector__pb2.SMDataRequest.SerializeToString,
            response_deserializer=MeterConnectorProto_dot_meter__connector__pb2.SMDataReply.FromString,
        )


class MeterConnectorServicer(object):
    """The greeting service definition."""

    def readMeter(self, request, context):
        """Sends a greeting"""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_MeterConnectorServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "readMeter": grpc.unary_unary_rpc_method_handler(
            servicer.readMeter,
            request_deserializer=MeterConnectorProto_dot_meter__connector__pb2.SMDataRequest.FromString,
            response_serializer=MeterConnectorProto_dot_meter__connector__pb2.SMDataReply.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler("MeterConnectorProto.MeterConnector", rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class MeterConnector(object):
    """The greeting service definition."""

    @staticmethod
    def readMeter(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/MeterConnectorProto.MeterConnector/readMeter",
            MeterConnectorProto_dot_meter__connector__pb2.SMDataRequest.SerializeToString,
            MeterConnectorProto_dot_meter__connector__pb2.SMDataReply.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )
