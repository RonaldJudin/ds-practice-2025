"""
Order Queue Service with FFT-based Prioritization

A gRPC service that manages a priority queue of order UUIDs using Fast Fourier Transform (FFT)
analysis to determine processing priority. Orders with more complex/irregular UUID patterns
are given higher priority based on their frequency domain characteristics.

Key Features:
- Thread-safe priority queue implementation using heapq
- FFT-based priority scoring of UUID strings
- FIFO ordering for equal-priority orders
- gRPC interface for enqueue/dequeue operations

Service Methods:
- Enqueue: Adds an order to the priority queue
- Dequeue: Removes and returns the highest priority order

Dependencies:
- grpcio, protobuf: For gRPC communication
- numpy, scipy: For FFT calculations
- heapq: For priority queue operations
"""

import sys
import os
import logging
import numpy as np
from scipy.fft import fft
import grpc
from concurrent import futures
import threading
import heapq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# gRPC stubs setup
FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
order_queue_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/order_queue")
)
sys.path.insert(0, order_queue_grpc_path)
import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc

class OrderQueueService(order_queue_grpc.OrderQueueServiceServicer):
    """gRPC service implementing a priority queue with FFT-based ordering."""
    
    def __init__(self):
        """Initialize the priority queue service.
        
        Attributes:
            heap (list): Priority queue implemented as a min-heap
            counter (int): Incremental counter for FIFO ordering of equal priorities
            lock (threading.Lock): Thread synchronization primitive
        """
        self.heap = []  # Priority queue storage
        self.counter = 0  # Tie-breaker counter
        self.lock = threading.Lock()  # Thread safety

    def calculate_fft_priority(self, uuid_str):
        """Calculate priority score using FFT analysis of UUID string.
        
        Args:
            uuid_str (str): The order UUID string to analyze
            
        Returns:
            float: Priority score (higher values indicate higher priority)
            
        Notes:
            - Converts UUID characters to ASCII values
            - Computes FFT power spectrum
            - Returns normalized power as priority score
        """
        # Convert UUID to ASCII values
        ascii_values = [ord(c) for c in uuid_str]
        
        # Compute FFT magnitude spectrum
        spectrum = np.abs(fft(ascii_values))
        
        # Calculate normalized power (using first half due to symmetry)
        power = np.sum(spectrum[:len(spectrum)//2] ** 2) / (len(spectrum)//2)
        
        return power

    def Enqueue(self, request, context):
        """gRPC method to add an order to the priority queue.
        
        Args:
            request (order_queue_pb2.EnqueueRequest): Contains order_id
            context (grpc.ServicerContext): gRPC context
            
        Returns:
            order_queue_pb2.EnqueueResponse: Contains the enqueued order_id
        """
        response = order_queue.EnqueueResponse()
        order_id = request.order_id

        order_data = {
            "order_id": order_id,
            "items": request.items,
            "user": {"name": request.user.name, "email": request.user.email},
            "credit_card": {
                "number": request.credit_card.number,
                "expiration_date": request.credit_card.expiration_date,
                "cvv": request.credit_card.cvv,
            },
            "user_comment": request.user_comment,
            "billing_address": {
                "street": request.billing_address.street,
                "city": request.billing_address.city,
                "state": request.billing_address.state,
                "zip": request.billing_address.zip,
                "country": request.billing_address.country,
            },
            "shipping_method": request.shipping_method,
            "gift_wrapping": request.gift_wrapping,
            "terms_accepted": request.terms_accepted,
        }
        
        # Calculate priority score
        priority = self.calculate_fft_priority(order_id)
        
        # Thread-safe enqueue operation
        with self.lock:
            # Store as max-heap using negative priority
            heapq.heappush(self.heap, (-priority, self.counter, order_data))
            self.counter += 1
        
        logger.info(f"Order {order_id} enqueued with priority score {priority:.2f}")
        response.order_id = order_id
        return response
    
    def Dequeue(self, request, context):
        """gRPC method to remove and return the highest priority order.
        
        Args:
            request (order_queue_pb2.DequeueRequest): Empty request
            context (grpc.ServicerContext): gRPC context
            
        Returns:
            order_queue_pb2.DequeueResponse: Contains dequeued order_id or empty string
        """
        response = order_queue.DequeueResponse()
        
        # Thread-safe dequeue operation
        with self.lock:
            if self.heap:
                _, _, order_data = heapq.heappop(self.heap)
                order_id = order_data["order_id"]
                logger.info(f"Order {order_id} dequeued")
                response = order_queue.DequeueResponse(
                    order_id=order_data["order_id"],
                    items=order_data["items"],
                    user=order_data["user"],
                    credit_card=order_data["credit_card"],
                    user_comment=order_data["user_comment"],
                    billing_address=order_data["billing_address"],
                    shipping_method=order_data["shipping_method"],
                    gift_wrapping=order_data["gift_wrapping"],
                    terms_accepted=order_data["terms_accepted"],
            )
            else:
                response.order_id = ""
                # logger.info("Dequeue attempted but queue was empty")
                
        return response

def serve():
    """Start and run the gRPC server.
    
    Configures and launches the gRPC server on port 50054,
    adding the OrderQueueService implementation.
    """
    # Create gRPC server with thread pool
    server = grpc.server(futures.ThreadPoolExecutor())
    
    # Add service implementation
    order_queue_grpc.add_OrderQueueServiceServicer_to_server(
        OrderQueueService(), server
    )
    
    # Bind to port and start server
    port = "50054"
    server.add_insecure_port("[::]:" + port)
    server.start()
    
    logger.info(f"Server started. Listening on port {port}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()