# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import fraud_detection_pb2 as fraud__detection__pb2


class HelloServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SayHello = channel.unary_unary(
                '/fraud_detection.HelloService/SayHello',
                request_serializer=fraud__detection__pb2.HelloRequest.SerializeToString,
                response_deserializer=fraud__detection__pb2.HelloResponse.FromString,
                )


class HelloServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SayHello(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_HelloServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SayHello': grpc.unary_unary_rpc_method_handler(
                    servicer.SayHello,
                    request_deserializer=fraud__detection__pb2.HelloRequest.FromString,
                    response_serializer=fraud__detection__pb2.HelloResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'fraud_detection.HelloService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class HelloService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SayHello(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/fraud_detection.HelloService/SayHello',
            fraud__detection__pb2.HelloRequest.SerializeToString,
            fraud__detection__pb2.HelloResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class FraudDetectionServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CheckFraud = channel.unary_unary(
                '/fraud_detection.FraudDetectionService/CheckFraud',
                request_serializer=fraud__detection__pb2.FraudDetectionRequest.SerializeToString,
                response_deserializer=fraud__detection__pb2.FraudDetectionResponse.FromString,
                )


class FraudDetectionServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CheckFraud(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_FraudDetectionServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CheckFraud': grpc.unary_unary_rpc_method_handler(
                    servicer.CheckFraud,
                    request_deserializer=fraud__detection__pb2.FraudDetectionRequest.FromString,
                    response_serializer=fraud__detection__pb2.FraudDetectionResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'fraud_detection.FraudDetectionService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class FraudDetectionService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CheckFraud(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/fraud_detection.FraudDetectionService/CheckFraud',
            fraud__detection__pb2.FraudDetectionRequest.SerializeToString,
            fraud__detection__pb2.FraudDetectionResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
