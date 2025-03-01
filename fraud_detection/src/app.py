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
    def CheckFraud(self, request, context):
        """
        Cross-check Interpol Red Notice DB with the user's data to determine if the order is fraudulent.
        """
        logger.info("Fraud Detection Service: Request recieved.")
        # Extract order data from the request
        fraud_data = {
            "user": request.user,
            "user_comment": request.user_comment,
            "billing_address": request.billing_address,
            "credit_card": request.credit_card,
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

        # Create a FraudDetectionResponse object
        response = fraud_detection.FraudDetectionResponse()
        response.is_fraudulent = is_fraudulent
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

