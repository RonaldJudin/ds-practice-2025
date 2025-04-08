import sys
import os

import requests
import json
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/order_queue")
)
sys.path.insert(0, order_queue_grpc_path)
import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc

import grpc
from concurrent import futures
import threading

class OrderQueueService(order_queue_grpc.OrderQueueServiceServicer):
    queue = []
    lock = threading.Lock()

    def Enqueue(self, request, context):
        response = order_queue.EnqueueResponse()
        # Put the order ID in the queue
        with self.lock:
            self.queue.append(request.order_id)
        response.order_id = request.order_id
        logger.info(f"Order {request.order_id} enqueued.")
        return response
    
    def Dequeue(self, request, context):
        response = order_queue.DequeueResponse()
        with self.lock:
            if self.queue:
                response.order_id = self.queue.pop(0)
            else:
                response.order_id = ""
        return response

def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add OrderQueueService to the server
    order_queue_grpc.add_OrderQueueServiceServicer_to_server(
        OrderQueueService(), server
    )
    # Listen on port 50054
    port = "50054"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50054.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
