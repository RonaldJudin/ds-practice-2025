import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
payment_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/payment")
)
sys.path.insert(0, payment_grpc_path)
import payment_pb2 as payment
import payment_pb2_grpc as payment_grpc

import grpc
from concurrent import futures


class PaymentService(payment_grpc.PaymentServiceServicer):
    # Dummy functionality for now
    def __init__(self):
        self.prepared = False

    def Prepare(self, request, context):
        self.prepared = True
        # logger.info(f"PaymentService prepared for order: {request.order_id}")
        return payment.PrepareResponse(ready=True)
    
    def Commit(self, request, context):
        if self.prepared:
            # logger.info(f"PaymentService committed for order: {request.order_id}")
            return payment.CommitResponse(success=True)

    def Abort(self, request, context):
        self.prepared = False
        # logger.info(f"PaymentService aborted for order: {request.order_id}")
        return payment.AbortResponse(aborted=True)
     

def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add SuggestionsService
    payment_grpc.add_PaymentServiceServicer_to_server(
        PaymentService(), server
    )
    # Listen on port 
    # Listen on port 50058
    port = "50058"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print(f"Server started. Listening on port {port}.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
