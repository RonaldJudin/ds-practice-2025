import sys
import os
from concurrent import futures

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


def greet(name="you"):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.HelloServiceStub(channel)
        # Call the service through the stub object.
        response = stub.SayHello(fraud_detection.HelloRequest(name=name))
    return response.greeting

def detectfraud(items, user, credit_card, user_comment, billing_address, shipping_method, gift_wrapping, terms_accepted=False):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.FraudDetectionServiceStub(channel)
        # Call the service through the stub object.
        response = stub.DetectFraud(fraud_detection.FraudDetectionRequest(items=items, user=user, credit_card=credit_card, user_comment=user_comment, billing_address=billing_address, shipping_method=shipping_method, gift_wrapping=gift_wrapping, terms_accepted=terms_accepted))
    return response.response


# Import Flask.
# Flask is a web framework for Python.
# It allows you to build a web application quickly.
# For more information, see https://flask.palletsprojects.com/en/latest/
from flask import Flask, request
from flask_cors import CORS
import json

# Create a simple Flask app.
app = Flask(__name__)
# Enable CORS for the app.
CORS(app, resources={r"/*": {"origins": "*"}})


# Define a GET endpoint.
@app.route("/", methods=["GET"])
def index():
    """
    Responds with 'Hello, [name]' when a GET request is made to '/' endpoint.
    """
    # Test the fraud-detection gRPC service.
    response = greet(name="orchestrator")
    # Return the response.
    return response


@app.route("/checkout", methods=["POST"])
def checkout():
    """
    Responds with a JSON object containing the order ID, status, and suggested books.
    """
    print("We are checking out")
    # Get request object data to json
    request_data = json.loads(request.data)
    items = request_data.get("items")
    user = request_data.get("user")
    credit_card = request_data.get("creditCard")
    user_comment = request_data.get("userComment")
    billing_address = request_data.get("billingAddress")
    shipping_method = request_data.get("shippingMethod")
    gift_wrapping = request_data.get("giftWrapping")
    terms_accepted = request_data.get("termsAccepted")

    print("We will now create the threads.")
    with futures.ThreadPoolExecutor() as executor:
        # Submit tasks to the executor
        fraud_detection_future = executor.submit(detectfraud, items, user, credit_card, user_comment, billing_address, shipping_method, gift_wrapping, terms_accepted)
        #transaction_verification_future = executor.submit(call_transaction_verification_service, order_data)
        #suggestions_future = executor.submit(call_suggestions_service, order_data)

        # Wait for all futures to complete
        futures.wait([fraud_detection_future]) #, transaction_verification_future, suggestions_future])

        # Get results
        fraud_detection_result = fraud_detection_future.result()
        #transaction_verification_result = transaction_verification_future.result()
        #suggestions_result = suggestions_future.result()

    # Combine results and make a decision
    if fraud_detection_result.response: #or not transaction_verification_result.is_valid:
        order_status = "Order Rejected"
    else:
        order_status = "Order Approved"
    print(order_status + "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    # Dummy response following the provided YAML specification for the bookstore
    order_status_response = {
        "orderId": "12345",
        "status": order_status,
        "suggestedBooks": [
            {"bookId": "123", "title": "The Best Book", "author": "Author 1"},
            {"bookId": "456", "title": "The Second Best Book", "author": "Author 2"},
        ],
    }

    return order_status_response


if __name__ == "__main__":
    # Run the app in debug mode to enable hot reloading.
    # This is useful for development.
    # The default port is 5000.
    app.run(host="0.0.0.0")
