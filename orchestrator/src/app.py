import sys
import os

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if '__file__' in globals() else os.getenv("PYTHONFILE", "")
fraud_detection_grpc_path = os.path.abspath(os.path.join(FILE, '../../../utils/pb/fraud_detection'))
sys.path.insert(0, fraud_detection_grpc_path)
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc

import grpc

def greet(name='you'):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel('fraud_detection:50051') as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.HelloServiceStub(channel)
        # Call the service through the stub object.
        response = stub.SayHello(fraud_detection.HelloRequest(name=name))
    return response.greeting

# Import Flask.
# Flask is a web framework for Python.
# It allows you to build a web application quickly.
# For more information, see https://flask.palletsprojects.com/en/latest/
from flask import Flask, request
from flask_cors import CORS
import json
# Import utils for concurrent procesing
from concurrent import futures

# Create a simple Flask app.
app = Flask(__name__)
# Enable CORS for the app.
CORS(app, resources={r'/*': {'origins': '*'}})

# Define a GET endpoint.
@app.route('/', methods=['GET'])
def index():
    """
    Responds with 'Hello, [name]' when a GET request is made to '/' endpoint.
    """
    # Test the fraud-detection gRPC service.
    response = greet(name='orchestrator')
    # Return the response.
    return response

def handle_fraud_detection(order_data):
    """
    Process the fraud detection for the given order data.
    """
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        stub = fraud_detection_grpc.FraudDetectionServiceStub(channel)

        # Build the gRPC request properly
        fraud_request = fraud_detection.FraudDetectionRequest(
            user=fraud_detection.User(
                name=order_data["user"]["name"],
                email=order_data["user"]["email"]
            ),
            credit_card=fraud_detection.CreditCard(
                number=order_data["credit_card"]["number"],
                expiration_date=order_data["credit_card"]["expiration_date"],
                cvv=order_data["credit_card"]["cvv"]
            ),
            user_comment=order_data["user_comment"],
            billing_address=fraud_detection.Address(
                street=order_data["billing_address"]["street"],
                city=order_data["billing_address"]["city"],
                state=order_data["billing_address"]["state"],
                zip=order_data["billing_address"]["zip"],
                country=order_data["billing_address"]["country"]
            )
        )

        response = stub.CheckFraud(fraud_request)
    
    return response

@app.route('/checkout', methods=['POST'])

def checkout():
    """
    Responds with a JSON object containing the order ID, status, and suggested books.
    """
    try:
        # Get request object data to json
        request_data = json.loads(request.data)
        # Print request object data
        items = request_data.get("items")
        user = request_data.get("user")
        credit_card = request_data.get("creditCard")
        user_comment = request_data.get("userComment")
        billing_address = request_data.get("billingAddress")
        shipping_method = request_data.get("shippingMethod")
        gift_wrapping = request_data.get("giftWrapping")
        terms_accepted = request_data.get("termsAccepted")

        fraud_detection_request_data = {
            "user": {
                "name": user.get("name"),
                "email": user.get("contact")
            },
            "credit_card": {
                "number": credit_card.get("number"),
                "expiration_date": credit_card.get("expirationDate"),
                "cvv": credit_card.get("cvv")
            },
            "user_comment": user_comment,
            "billing_address": {
                "street": billing_address.get("street"),
                "city": billing_address.get("city"),
                "state": billing_address.get("state"),
                "zip": billing_address.get("zip"),
                "country": billing_address.get("country")
            }
        }

        print("Fraud Detection Request Data", fraud_detection_request_data)

        # Concurrency executor
        with futures.ThreadPoolExecutor() as executor:
            # Dispatch the order data to the fraud detection service
            future_fraud_detection = executor.submit(handle_fraud_detection, fraud_detection_request_data)
            # Wait for the results
            fraud_detection_result = future_fraud_detection.result()

        print(fraud_detection_result)
        # Check if FraudDetectionService found fraud
        if fraud_detection_result.is_fraudulent:
            order_status_response = {
                'orderId': '12345',
                'status': 'Order Rejected - Fraud Detected',
                'suggestedBooks': []
            }
            return json.dumps(order_status_response), 200
        else:
            # No fraud detected, continue evaluation
            # Dummy response following the provided YAML specification for the bookstore
            order_status_response = {
                'orderId': '12345',
                'status': 'Order Approved',
                'suggestedBooks': [
                    {'bookId': '123', 'title': 'The Best Book', 'author': 'Author 1'},
                    {'bookId': '456', 'title': 'The Second Best Book', 'author': 'Author 2'}
                ]
            }

        return json.dumps(order_status_response), 200

    except KeyError as e:
        error_response = {
            'error': {
                'code': '400',
                'message': f'Missing key: {str(e)}'
            }
        }
        return json.dumps(error_response), 400

    except Exception as e:
        error_response = {
            'error': {
                'code': '500',
                'message': f'Internal server error: {str(e)}'
            }
        }
        return json.dumps(error_response), 500


if __name__ == '__main__':
    # Run the app in debug mode to enable hot reloading.
    # This is useful for development.
    # The default port is 5000.
    app.run(host='0.0.0.0')
