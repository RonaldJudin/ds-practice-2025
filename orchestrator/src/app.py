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
fraud_detection_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/fraud_detection")
)
suggestions_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/suggestions")
)
transaction_verification_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/transaction_verification")
)
sys.path.insert(0, fraud_detection_grpc_path)
sys.path.insert(0, suggestions_grpc_path)
sys.path.insert(0, transaction_verification_grpc_path)
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc
import grpc


def greet(name="you"):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel("fraud_detection:50051") as channel:
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


def handle_fraud_detection(order_data):
    """
    Process the fraud detection for the given order data.
    """
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        stub = fraud_detection_grpc.FraudDetectionServiceStub(channel)

        # Build the gRPC request
        fraud_request = fraud_detection.FraudDetectionRequest(
            user=fraud_detection.User(
                name=order_data["user"]["name"], email=order_data["user"]["email"]
            ),
            credit_card=fraud_detection.CreditCard(
                number=order_data["credit_card"]["number"],
                expiration_date=order_data["credit_card"]["expiration_date"],
                cvv=order_data["credit_card"]["cvv"],
            ),
            user_comment=order_data["user_comment"],
            billing_address=fraud_detection.Address(
                street=order_data["billing_address"]["street"],
                city=order_data["billing_address"]["city"],
                state=order_data["billing_address"]["state"],
                zip=order_data["billing_address"]["zip"],
                country=order_data["billing_address"]["country"],
            ),
        )

        response = stub.CheckFraud(fraud_request)

    return response


def handle_suggestions(user_data):
    """
    Process the suggestions for the given user data.
    """
    with grpc.insecure_channel("suggestions:50052") as channel:
        stub = suggestions_grpc.SuggestionsServiceStub(channel)

        # Build the gRPC request
        suggestions_request = suggestions.SuggestionsRequest(
            user=suggestions.User(name=user_data["name"], email=user_data["email"])
        )

        response = stub.GetSuggestions(suggestions_request)

    return response


def handle_transaction_verification(transaction_data):
    """
    Process the transaction verification for the given transaction data.
    """
    with grpc.insecure_channel("transaction_verification:50053") as channel:
        stub = transaction_verification_grpc.TransactionVerificationServiceStub(channel)

        # Build the gRPC request
        transaction_verification_request = (
            transaction_verification.TransactionVerificationRequest(
                user=transaction_verification.User(
                    name=transaction_data["user"]["name"],
                    email=transaction_data["user"]["email"],
                ),
                credit_card=transaction_verification.CreditCard(
                    number=transaction_data["credit_card"]["number"],
                    expiration_date=transaction_data["credit_card"]["expiration_date"],
                    cvv=transaction_data["credit_card"]["cvv"],
                ),
                billing_address=transaction_verification.Address(
                    street=transaction_data["billing_address"]["street"],
                    city=transaction_data["billing_address"]["city"],
                    state=transaction_data["billing_address"]["state"],
                    zip=transaction_data["billing_address"]["zip"],
                    country=transaction_data["billing_address"]["country"],
                ),
            )
        )

        response = stub.VerifyTransaction(transaction_verification_request)

    return response


@app.route("/checkout", methods=["POST"])
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
            "user": {"name": user.get("name"), "email": user.get("contact")},
            "credit_card": {
                "number": credit_card.get("number"),
                "expiration_date": credit_card.get("expirationDate"),
                "cvv": credit_card.get("cvv"),
            },
            "user_comment": user_comment,
            "billing_address": {
                "street": billing_address.get("street"),
                "city": billing_address.get("city"),
                "state": billing_address.get("state"),
                "zip": billing_address.get("zip"),
                "country": billing_address.get("country"),
            },
        }

        logger.info("Received submit order request")

        # Concurrency executor
        with futures.ThreadPoolExecutor() as executor:
            # Dispatch the order data to the fraud detection service
            future_fraud_detection = executor.submit(
                handle_fraud_detection, fraud_detection_request_data
            )
            logger.info("Fraud Detection Service: Request sent.")
            # Wait for the results
            fraud_detection_result = future_fraud_detection.result()

        if fraud_detection_result.is_fraudulent:
            order_status_response = {
                "orderId": "12345",
                "status": "Order Rejected - Fraud Detected",
                "suggestedBooks": [],
            }

            logger.info(
                "Fraud Detection Service: User in FBI wanted database. Rejecting order."
            )
            return json.dumps(order_status_response), 200
        logger.info("Fraud Detection Service: Passed fraud check.")

        # No fraud detected, continue
        # Begin transaction verification workflow
        transaction_verification_request_data = {
            "user": {"name": user.get("name"), "email": user.get("contact")},
            "credit_card": {
                "number": credit_card.get("number"),
                "expiration_date": credit_card.get("expirationDate"),
                "cvv": credit_card.get("cvv"),
            },
            "billing_address": {
                "street": billing_address.get("street"),
                "city": billing_address.get("city"),
                "state": billing_address.get("state"),
                "zip": billing_address.get("zip"),
                "country": billing_address.get("country"),
            },
        }

        with futures.ThreadPoolExecutor() as executor:
            future_transaction_verification = executor.submit(
                handle_transaction_verification, transaction_verification_request_data
            )
            logger.info("Transaction Verification Service: Request sent.")
            transaction_verification_result = future_transaction_verification.result()

        if not transaction_verification_result.is_verified:
            order_status_response = {
                "orderId": "12345",
                "status": "Order Rejected - Transaction Verification Failed",
                "suggestedBooks": [],
            }
            logger.info(
                "Transaction Verification Service: Could not verify transaction. Rejecting order."
            )
            return json.dumps(order_status_response), 200
        logger.info("Transaction Verification Service: Transaction verified.")

        # Begin suggestions workflow
        suggestions_request_data = {
            "name": user.get("name"),
            "email": user.get("contact"),
        }

        with futures.ThreadPoolExecutor() as executor:
            future_suggestions = executor.submit(
                handle_suggestions, suggestions_request_data
            )
            logger.info("Suggestions Service: Request sent.")
            suggestions_result = future_suggestions.result()
        logger.info("Suggestions Service: Recieved suggestions.")
        suggested_books = [
            {"bookId": book.bookId, "title": book.title, "author": book.author}
            for book in suggestions_result.suggested_books
        ]

        # Dummy response following the provided YAML specification for the bookstore
        order_status_response = {
            "orderId": "12345",
            "status": "Order Approved",
            "suggestedBooks": suggested_books,
        }

        return json.dumps(order_status_response), 200

    except KeyError as e:
        error_response = {"error": {"code": "400", "message": f"Missing key: {str(e)}"}}
        logger.error(f"KeyError: {str(e)}")
        return json.dumps(error_response), 400

    except Exception as e:
        error_response = {
            "error": {"code": "500", "message": f"Internal server error: {str(e)}"}
        }
        logger.error(f"Exception: {str(e)}")
        return json.dumps(error_response), 500


if __name__ == "__main__":
    # Run the app in debug mode to enable hot reloading.
    # This is useful for development.
    # The default port is 5000.
    app.run(host="0.0.0.0")
