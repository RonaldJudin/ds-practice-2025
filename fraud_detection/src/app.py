import sys
import os

import requests
import json
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# === OpenTelemetry Init ===
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Set up resource attributes (service name is important for Grafana)
resource = Resource(attributes={
    "service.name": os.environ.get("SERVICE_NAME", "fraud_detection")
})

# Set up tracer provider and exporter
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()
otlp_exporter = OTLPSpanExporter(endpoint="http://observability:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Instrument gRPC
GrpcInstrumentorServer().instrument()
GrpcInstrumentorClient().instrument()
RequestsInstrumentor().instrument()

logger.info("OpenTelemetry initialized for service: %s", os.environ.get("SERVICE_NAME"))
# === OpenTelemetry End ===

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/fraud_detection")
)
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc

import grpc
from concurrent import futures


# Create a class to define the server functions, derived from
# fraud_detection_pb2_grpc.HelloServiceServicer
class HelloService(fraud_detection_grpc.HelloServiceServicer):
    # Create an RPC function to say hello
    def SayHello(self, request, context):
        # Create a HelloResponse object
        response = fraud_detection.HelloResponse()
        # Set the greeting field of the response object
        response.greeting = "Hello, " + request.name
        # Print the greeting message
        print(response.greeting)
        # Return the response object
        return response

class FraudDetectionService(fraud_detection_grpc.FraudDetectionServiceServicer):
    orders = {}
    def InitOrder(self, request, context):
        """
        Initializes a new order in the fraud detection system.

        This function initializes a new order in the fraud detection system by storing the order
        details in a dictionary. The order details include the user, user comment, billing address,
        and credit card information.

        Args:
            request: The order initialization request object containing order details.
            context: The gRPC context for handling the request.

        Returns:
            fraud_detection.OrderInitResponse: A response object indicating the successful
            initialization of the order.

        Logs:
            - Logs the receipt of the request.
            - Logs the successful initialization of the order.
        """
        # Store the order details in the orders dictionary
        self.orders[request.order_id] = {
            "items": request.items,
            "user": request.user,
            "user_comment": request.user_comment,
            "billing_address": request.billing_address,
            "credit_card": request.credit_card,
            "shipping_method": request.shipping_method,
            "gift_wrapping": request.gift_wrapping,
            "terms_accepted": request.terms_accepted,
        }
        # Create an InitOrderResponse object
        response = fraud_detection.InitOrderResponse()
        response.order_id = request.order_id
        logger.info("Fraud Detection Service: Order initialized successfully.")
        return response
    
    def CheckCreditCard(self, request, context):
        """
        Checks the validity of a credit card by querying the CreditCardValidator API.

        This function processes a credit card validation request by extracting the credit card number
        from the request. It then queries the CreditCardValidator API to determine if the credit card
        is valid. If the credit card is valid, the transaction is marked as verified.
        """
        logger.info("Fraud Detection Service: Credit card validation request received.")
        # Extract credit card data from the request
        credit_card_data = self.orders[request.order_id]["credit_card"]

        # Verify credit card if its number starts with 372
        is_verified = False
        if credit_card_data.number.startswith("372"):
            is_verified = True

        # Create a CreditCardResponse object
        response = fraud_detection.CreditCardResponse()
        response.is_verified = is_verified
        logger.info("Fraud Detection Service: Credit card validation response sent.")

        # Increment vector clock
        request.vector_clock["fraud_detection"] += 1
        print(request.vector_clock)
        response.vector_clock.clear()  # Clear the existing map
        response.vector_clock.update(request.vector_clock)  # Copy the vector clock
        return response

    def CheckFraud(self, request, context):
        """
        Detects potential fraud in a transaction by checking if the user is listed in the FBI Wanted API.

        This function processes a fraud detection request by extracting user and transaction details
        from the request. It then queries the FBI Wanted API to determine if the user is listed as
        wanted. If the user is found in the FBI Wanted list, the transaction is flagged as fraudulent.

        Args:
            request: The fraud detection request object containing user and transaction details.
            context: The gRPC context for handling the request.

        Returns:
            fraud_detection.FraudDetectionResponse: A response object indicating whether the
            transaction is flagged as fraudulent (True) or not (False).

        Logs:
            - Logs the receipt of the request.
            - Logs the sending of the response.
        """
        logger.info("Fraud Detection Service: Request recieved.")
        # Extract order data from the request
        fraud_data = {
            "user": self.orders[request.order_id]["user"],
            "user_comment": self.orders[request.order_id]["user_comment"],
            "billing_address": self.orders[request.order_id]["billing_address"],
        }

        # Query the FBI Wanted API to check if the user is wanted
        response = requests.get(
            "https://api.fbi.gov/wanted/v1/list",
            params={"title": fraud_data["user"].name.upper()},
        )
        wanted_data = json.loads(response.content)

        # If user is wanted, order is fraudulent
        is_fraudulent = False
        if wanted_data["total"] > 0:
            is_fraudulent = True
            logger.info("Fraud Detection Service: User is wanted. Order flagged as fraudulent.")
        else:
            logger.info("Fraud Detection Service: User is not wanted. Order is not flagged as fraudulent.")

        # Create a FraudDetectionResponse object
        response = fraud_detection.FraudDetectionResponse()
        response.is_fraudulent = is_fraudulent

        # Increment vector clock
        request.vector_clock["fraud_detection"] += 1
        print(request.vector_clock)
        response.vector_clock.clear()  # Clear the existing map
        response.vector_clock.update(request.vector_clock)  # Copy the vector clock
        logger.info("Fraud Detection Service: Response sent.")
        return response


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add HelloService
    fraud_detection_grpc.add_HelloServiceServicer_to_server(HelloService(), server)
    # Add FraudDetectionService
    fraud_detection_grpc.add_FraudDetectionServiceServicer_to_server(
        FraudDetectionService(), server
    )
    # Listen on port 50051
    port = "50051"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50051.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
