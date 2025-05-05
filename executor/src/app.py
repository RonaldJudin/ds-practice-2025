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
payment_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/payment")
)
sys.path.insert(0, executor_grpc_path)
sys.path.insert(0, order_queue_grpc_path)
sys.path.insert(0, books_database_grpc_path)
sys.path.insert(0, payment_grpc_path)
import executor_pb2 as executor
import executor_pb2_grpc as executor_grpc
import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc
import books_database_pb2 as books_database
import books_database_pb2_grpc as books_database_grpc
import payment_pb2 as payment
import payment_pb2_grpc as payment_grpc

import grpc
from concurrent import futures
import threading

# 2PC (Phase Commit) logic
def two_phase_commit(order_id, order_data):
    """
    Perform a two-phase commit for the given order ID and order data.
    """
    logger.info(f"Starting two-phase commit for order {order_id}")

    # Phase 1: Prepare
    logger.info(f"Phase 1: Preparing Books Database for order {order_id}")
    if not retry_request(handle_database_prepare, order_id=order_id, order_data=order_data):
        logger.error(f"Preparation failed for Books Database. Aborting.")
        retry_request(handle_database_abort, order_id=order_id)
        retry_request(handle_payment_abort, order_id=order_id)
        return False

    logger.info(f"Phase 1: Preparing Payment Service for order {order_id}")
    if not retry_request(handle_payment_prepare, order_id=order_id):
        logger.error(f"Preparation failed for Payment Service. Aborting.")
        retry_request(handle_database_abort, order_id=order_id)
        retry_request(handle_payment_abort, order_id=order_id)
        return False

    # Phase 2: Commit
    logger.info(f"Phase 2: Committing Books Database for order {order_id}")
    retry_request(handle_database_commit, order_id=order_id)

    logger.info(f"Phase 2: Committing Payment Service for order {order_id}")
    retry_request(handle_payment_commit, order_id=order_id)

    return True

# Exponential backoff for retrying requests if the service is not available
# We implement infinite retries with a backoff factor of 2
def retry_request(func, max_retries=7, backoff_factor=2, *args, **kwargs):
    """
    Retry a request with exponential backoff.
    """
    retries = 0
    while True:
        logger.info(f"Attempt ({retries + 1}/{max_retries}) for {func.__name__}")
        try:
            return func(*args, **kwargs)
        except grpc.RpcError as e:
            retries += 1
            logger.error(f"Retry {retries}/{max_retries} failed: {e}")
            time.sleep(backoff_factor ** retries)
    
def handle_database_prepare(order_id, order_data):
    """
    Send a Prepare request to the Books Database Service for each book in the order.
    """
    with grpc.insecure_channel("books_database_1:49664") as channel:
        database_stub = books_database_grpc.BooksDatabaseServiceStub(channel)
        for book in order_data["items"]:
            prepare_request = books_database.PrepareRequest(
                order_id=order_id,
                title=book.name,
                stock=book.quantity,
            )
            try:
                response = database_stub.Prepare(prepare_request)
                if not response.ready:
                    logger.error(f"BooksDatabaseService not ready for order {order_id}, book {book.name}.")
                    return False
                logger.info(f"BooksDatabaseService prepared for order {order_id}, book {book.name}.")
            except grpc.RpcError as e:
                logger.error(f"Error preparing BooksDatabaseService for order {order_id}, book {book.name}: {e}")
                return False
    return True

def handle_database_commit(order_id):
    """
    Send a Commit request to the Books Database Service for the given order.
    """
    with grpc.insecure_channel("books_database_1:49664") as channel:
        database_stub = books_database_grpc.BooksDatabaseServiceStub(channel)
        commit_request = books_database.CommitRequest(order_id=order_id)
        try:
            response = database_stub.Commit(commit_request)
            if response.success:
                logger.info(f"BooksDatabaseService committed for order {order_id}.")
            else:
                logger.error(f"BooksDatabaseService failed to commit for order {order_id}.")
        except grpc.RpcError as e:
            logger.error(f"Error committing BooksDatabaseService for order {order_id}: {e}")

def handle_database_abort(order_id):
    """
    Send an Abort request to the Books Database Service for the given order.
    """
    with grpc.insecure_channel("books_database_1:49664") as channel:
        database_stub = books_database_grpc.BooksDatabaseServiceStub(channel)
        abort_request = books_database.AbortRequest(order_id=order_id)
        try:
            response = database_stub.Abort(abort_request)
            if response.aborted:
                logger.info(f"BooksDatabaseService aborted for order {order_id}.")
            else:
                logger.error(f"BooksDatabaseService failed to abort for order {order_id}.")
        except grpc.RpcError as e:
            logger.error(f"Error aborting BooksDatabaseService for order {order_id}: {e}")

def handle_payment_prepare(order_id):
    """
    Send a Prepare request to the Payment Service for the given order.
    """
    with grpc.insecure_channel("payment:50058") as channel:
        payment_stub = payment_grpc.PaymentServiceStub(channel)
        prepare_request = payment.PrepareRequest(order_id=order_id)
        try:
            response = payment_stub.Prepare(prepare_request)
            if response.ready:
                logger.info(f"PaymentService prepared for order {order_id}.")
                return True
            else:
                logger.error(f"PaymentService not ready for order {order_id}.")
                return False
        except grpc.RpcError as e:
            logger.error(f"Error preparing PaymentService for order {order_id}: {e}")
            return False

def handle_payment_commit(order_id):
    """
    Send a Commit request to the Payment Service for the given order.
    """
    with grpc.insecure_channel("payment:50058") as channel:
        payment_stub = payment_grpc.PaymentServiceStub(channel)
        commit_request = payment.CommitRequest(order_id=order_id)
        try:
            response = payment_stub.Commit(commit_request)
            if response.success:
                logger.info(f"PaymentService committed for order {order_id}.")
            else:
                logger.error(f"PaymentService failed to commit for order {order_id}.")
        except grpc.RpcError as e:
            logger.error(f"Error committing PaymentService for order {order_id}: {e}")
            

def handle_payment_abort(order_id):
    """
    Send an Abort request to the Payment Service for the given order.
    """
    with grpc.insecure_channel("payment:50058") as channel:
        payment_stub = payment_grpc.PaymentServiceStub(channel)
        abort_request = payment.AbortRequest(order_id=order_id)
        try:
            response = payment_stub.Abort(abort_request)
            if response.aborted:
                logger.info(f"PaymentService aborted for order {order_id}.")
            else:
                logger.error(f"PaymentService failed to abort for order {order_id}.")
        except grpc.RpcError as e:
            logger.error(f"Error aborting PaymentService for order {order_id}: {e}")
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

                        """ Example of order data:
                        order_data = {
                            "items": [{
                                "title": "Book Title",
                                "quantity": 1,
                            }, {
                                "title": "Another Book Title",
                                "quantity": 2,
                            }],
                        }
                        """
                        order_data = {
                            "items": dequeue_response.items,
                        }
                        # Handle the order data (e.g., decrement stock in the database)
                        # self.handle_database_query(order_data)
                        # Perform two-phase commit with the participants
                        if two_phase_commit(dequeue_response.order_id, order_data):
                            logger.info(f"Order {dequeue_response.order_id} committed successfully.")
                        else:
                            logger.error(f"Order {dequeue_response.order_id} failed to commit.")
                        
                        

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
