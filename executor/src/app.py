import sys
import os

import requests
import json
import logging

import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
executor_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/executor")
)
order_queue_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/order_queue")
)
books_database_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/books_database")
)
sys.path.insert(0, executor_grpc_path)
sys.path.insert(0, order_queue_grpc_path)
sys.path.insert(0, books_database_grpc_path)
import executor_pb2 as executor
import executor_pb2_grpc as executor_grpc
import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc
import books_database_pb2 as books_database
import books_database_pb2_grpc as books_database_grpc

import grpc
from concurrent import futures
import threading

class ExecutorService(executor_grpc.ExecutorServiceServicer):
    ids_ports = {1: "executor_1:50055", 2: "executor_2:50056", 3: "executor_3:50057"}
    def __init__(self, executor_id, known_ids, queue_stub):
        # Initialize an empty queue and a lock for thread safety
        self.executor_id = executor_id
        self.known_ids = sorted(known_ids, reverse=True)
        self.queue_stub = queue_stub
        self.leader_id = None

    def ping(self, request, context):
        address = request.address
        with grpc.insecure_channel(self.ids_ports[address]) as channel:
            stub = executor_grpc.ExecutorServiceStub(channel)
            try:
                response = stub.answer(request, timeout=2)
            except grpc.RpcError as e:
                response = None
        return response

    def answer(self, request, context):
        response = executor.PingResponse()
        response.executor_id = self.executor_id
        return response

    def start_leader_election(self):
        # Start the leader election process
        for other in self.known_ids:
            if other > self.executor_id:
                with grpc.insecure_channel(self.ids_ports[other]) as channel:
                    stub = executor_grpc.ExecutorServiceStub(channel)
                    ping_request = executor.PingRequest(address=other)
                    try:
                        ping_response = stub.ping(ping_request, timeout=2)
                    except grpc.RpcError as e:
                        ping_response = None
                if ping_response is not None:
                    self.leader_id = other
                    return
            elif other == self.executor_id:
                self.habemus_papam()

    def new_leader(self, request, context):
        self.leader_id = request.leader_id
        return executor.NewLeaderResponse(acknowledged=True)

    def habemus_papam(self):
        # This method is called when a leader is elected
        all_acknowledged = True
        for other in self.known_ids:
            if other != self.executor_id:
                new_leader_request = executor.NewLeaderRequest(leader_id=self.executor_id)
                with grpc.insecure_channel(self.ids_ports[other]) as channel:
                    stub = executor_grpc.ExecutorServiceStub(channel)
                    try:
                        new_leader_response = stub.new_leader(new_leader_request, timeout=2)
                    except grpc.RpcError as e:
                        new_leader_response = None
                    all_acknowledged &= new_leader_response is None or new_leader_response.acknowledged
        
        if all_acknowledged:
            logger.info(f"Executor {self.executor_id} is the new leader.")
            # This is the only place where a node appoints itself leader
            self.leader_id = self.executor_id

    def handle_database_query(self, order_data):
        # This method is called when an order is dequeued
        with grpc.insecure_channel("books_database_1:49664") as channel:
            database_stub = books_database_grpc.BooksDatabaseServiceStub(channel)
            for book in order_data["items"]:
                # Decrement the stock of each book in the order
                decrement_request = books_database.WriteRequest(
                    title=book.name,
                    new_stock=book.quantity,
                )
                database_stub.DecrementStock(decrement_request)

    def run(self):
        while True:
            if self.executor_id == self.leader_id:
                # If this executor is the leader, it can dequeue
                dequeue_request = order_queue.DequeueRequest()
                with grpc.insecure_channel("order_queue:50054") as channel:
                    queue_stub = order_queue_grpc.OrderQueueServiceStub(channel)
                    dequeue_response = queue_stub.Dequeue(dequeue_request)
                    if dequeue_response.order_id:
                        logger.info(f"Executor {self.executor_id} dequeued order {dequeue_response.order_id}.")
                        order_data = {
                            "items": dequeue_response.items,
                        }
                        # Handle the order data (e.g., decrement stock in the database)
                        self.handle_database_query(order_data)

                    else:
                        time.sleep(1)  # Sleep for a while if the queue is empty
            else:
                if self.leader_id is None:
                    # If there is no leader, this executor can initiate a new leader election
                    logger.info(f"Executor {self.executor_id} is initiating a new leader election.")
                    self.start_leader_election()
                else:
                    ping_request = executor.PingRequest(address=self.leader_id)
                    if self.ping(ping_request, None) is None:
                        self.leader_id = None
                time.sleep(1)

def launch_executor(executor_id, known_ids):
    # Create a gRPC channel to the queue service
    channel = grpc.insecure_channel("order_queue:50054")
    queue_stub = order_queue_grpc.OrderQueueServiceStub(channel)

    # Create an instance of ExecutorService
    executor_service = ExecutorService(executor_id, known_ids, queue_stub)

    return executor_service

def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())

    # Get the executor ID and known IDs from environment variables
    executor_id = int(os.getenv("EXECUTOR_ID"))
    known_ids = os.getenv("KNOWN_IDS").split(",")
    known_ids = [int(i) for i in known_ids]
    # Create an instance of ExecutorService
    executor_service = launch_executor(executor_id, known_ids)

    # Add ExecutorService to the server
    executor_grpc.add_ExecutorServiceServicer_to_server(
        executor_service, server
    )

    # Listen on designated port
    port = str(os.getenv("PORT"))
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port " + port + ".")

    # Wait for other servers to start
    time.sleep(3)

    # Start the leader election process
    executor_service.start_leader_election()

    # Start the executor service
    executor_service.run()

    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
