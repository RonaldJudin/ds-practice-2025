import sys
import os
import logging
import uuid

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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

# === OpenTelemetry Init ===
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

import os

# Set up resource attributes (service name is important for Grafana)
resource = Resource(attributes={
    "service.name": os.environ.get("SERVICE_NAME", "orchestrator")
})

# Set up tracer provider and exporter
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()
otlp_exporter = OTLPSpanExporter(endpoint="http://observability:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# Instrument gRPC
GrpcInstrumentorServer().instrument()
GrpcInstrumentorClient().instrument()

logger.info("OpenTelemetry initialized for service: %s", os.environ.get("SERVICE_NAME"))
# === OpenTelemetry End ===

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
order_queue_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/order_queue")
)
sys.path.insert(0, fraud_detection_grpc_path)
sys.path.insert(0, suggestions_grpc_path)
sys.path.insert(0, transaction_verification_grpc_path)
sys.path.insert(0, order_queue_grpc_path)
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc
import order_queue_pb2 as order_queue
import order_queue_pb2_grpc as order_queue_grpc
import grpc

# Easy way to merge vector clocks
def merge_vector_clocks(vc1, vc2):
    """
    Merge two vector clocks by taking the maximum value for each key.
    """
    merged_vc = vc1.copy()
    for key, value in vc2.items():
        merged_vc[key] = max(merged_vc.get(key, 0), value)
    return merged_vc


def greet(name="you"):
    # Establish a connection with the fraud-detection gRPC service.
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        # Create a stub object.
        stub = fraud_detection_grpc.HelloServiceStub(channel)
        # Call the service through the stub object.
        response = stub.SayHello(fraud_detection.HelloRequest(name=name))
    return response.greeting

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

def handle_init_order_fraud_detection(order_data):
    """
    Process the order initialization for the given order data.
    """
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        logger.info("Fraud Detection Service: Order initialization request sent.")
        stub = fraud_detection_grpc.FraudDetectionServiceStub(channel)

        #logger.info(order_data)
        #logger.info([fraud_detection.Book(name=item["name"], quantity=item["quantity"]) for item in order_data["items"]])
        #for data in order_data.values():
        #    logger.info(data)
        #    logger.info(type(data))

        # Build the gRPC request
        order_init_request = fraud_detection.InitOrderRequest(
            order_id=order_data["order_id"],
            items=[fraud_detection.Book(name=item["name"], quantity=item["quantity"]) for item in order_data["items"]],
            user=fraud_detection.User(
                name=order_data["user"]["name"], email=order_data["user"]["name"]
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
            shipping_method=order_data["shipping_method"],
            gift_wrapping=order_data["gift_wrapping"],
            terms_accepted=order_data["terms_accepted"],
        )

        response = stub.InitOrder(order_init_request)
    return response

def handle_init_order_suggestions(order_data):
    """
    Process the order initialization for the given order data.
    """
    with grpc.insecure_channel("suggestions:50052") as channel:
        logger.info("Suggestions Service: Order initialization request sent.")
        stub = suggestions_grpc.SuggestionsServiceStub(channel)

        #logger.info(order_data)
        #logger.info([fraud_detection.Book(name=item["name"], quantity=item["quantity"]) for item in order_data["items"]])
        #for data in order_data.values():
        #    logger.info(data)
        #    logger.info(type(data))

        # Build the gRPC request
        order_init_request = suggestions.InitOrderRequest(
            order_id=order_data["order_id"],
            items=[suggestions.BookOrder(name=item["name"], quantity=item["quantity"]) for item in order_data["items"]],
            user=suggestions.User(
                name=order_data["user"]["name"], email=order_data["user"]["name"]
            ),
            credit_card=suggestions.CreditCard(
                number=order_data["credit_card"]["number"],
                expiration_date=order_data["credit_card"]["expiration_date"],
                cvv=order_data["credit_card"]["cvv"],
            ),
            user_comment=order_data["user_comment"],
            billing_address=suggestions.Address(
                street=order_data["billing_address"]["street"],
                city=order_data["billing_address"]["city"],
                state=order_data["billing_address"]["state"],
                zip=order_data["billing_address"]["zip"],
                country=order_data["billing_address"]["country"],
            ),
            shipping_method=order_data["shipping_method"],
            gift_wrapping=order_data["gift_wrapping"],
            terms_accepted=order_data["terms_accepted"],
        )

        response = stub.InitOrder(order_init_request)
    return response

def handle_init_order_transaction_verification(order_data):
    """
    Process the order initialization for the given order data.
    """
    with grpc.insecure_channel("transaction_verification:50053") as channel:
        logger.info("Transaction Verification Service: Order initialization request sent.")
        stub = transaction_verification_grpc.TransactionVerificationServiceStub(channel)

        #logger.info(order_data)
        #logger.info([fraud_detection.Book(name=item["name"], quantity=item["quantity"]) for item in order_data["items"]])
        #for data in order_data.values():
        #    logger.info(data)
        #    logger.info(type(data))

        # Build the gRPC request
        order_init_request = transaction_verification.InitOrderRequest(
            order_id=order_data["order_id"],
            items=[transaction_verification.Book(name=item["name"], quantity=item["quantity"]) for item in order_data["items"]],
            user=transaction_verification.User(
                name=order_data["user"]["name"], email=order_data["user"]["name"]
            ),
            credit_card=transaction_verification.CreditCard(
                number=order_data["credit_card"]["number"],
                expiration_date=order_data["credit_card"]["expiration_date"],
                cvv=order_data["credit_card"]["cvv"],
            ),
            user_comment=order_data["user_comment"],
            billing_address=transaction_verification.Address(
                street=order_data["billing_address"]["street"],
                city=order_data["billing_address"]["city"],
                state=order_data["billing_address"]["state"],
                zip=order_data["billing_address"]["zip"],
                country=order_data["billing_address"]["country"],
            ),
            shipping_method=order_data["shipping_method"],
            gift_wrapping=order_data["gift_wrapping"],
            terms_accepted=order_data["terms_accepted"],
        )

        response = stub.InitOrder(order_init_request)
    return response

def handle_fraud_detection_cc(order_data):
    """
    Process the fraud detection for the given order data.
    """
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        stub = fraud_detection_grpc.FraudDetectionServiceStub(channel)

        # Build the gRPC request
        fraud_request = fraud_detection.FraudDetectionRequest(
            order_id=order_data["order_id"],
            vector_clock=order_data["vector_clock"],
        )

        response = stub.CheckCreditCard(fraud_request)

    return response

def handle_suggestions(user_data):
    """
    Process the suggestions for the given user data.
    """
    with grpc.insecure_channel("suggestions:50052") as channel:
        stub = suggestions_grpc.SuggestionsServiceStub(channel)

        # Build the gRPC request
        suggestions_request = suggestions.SuggestionsRequest(
            order_id=user_data["order_id"],
            vector_clock=user_data["vector_clock"],
        )

        response = stub.GetSuggestions(suggestions_request)

    return response


def handle_transaction_verification_a(transaction_data):
    """
    Process the transaction verification for the given transaction data.
    """
    with grpc.insecure_channel("transaction_verification:50053") as channel:
        stub = transaction_verification_grpc.TransactionVerificationServiceStub(channel)

        # Build the gRPC request
        transaction_verification_request = (
            transaction_verification.TVRequest(
                order_id=transaction_data["order_id"],
                vector_clock=transaction_data["vector_clock"],
                )
            )

        response = stub.VerifyBookList(transaction_verification_request)

    return response

def handle_transaction_verification_b(transaction_data):
    """
    Process the transaction verification for the given transaction data.
    """
    with grpc.insecure_channel("transaction_verification:50053") as channel:
        stub = transaction_verification_grpc.TransactionVerificationServiceStub(channel)

        # Build the gRPC request
        transaction_verification_request = (
            transaction_verification.TVRequest(
                order_id=transaction_data["order_id"],
                vector_clock=transaction_data["vector_clock"],
                )
            )

        response = stub.VerifyUserData(transaction_verification_request)

    return response

def handle_transaction_verification(transaction_data):
    """
    Process the transaction verification for the given transaction data.
    """
    with grpc.insecure_channel("transaction_verification:50053") as channel:
        stub = transaction_verification_grpc.TransactionVerificationServiceStub(channel)

        # Build the gRPC request
        transaction_verification_request = (
            transaction_verification.TVRequest(
                order_id=transaction_data["order_id"],
                vector_clock=transaction_data["vector_clock"],
                )
            )

        response = stub.VerifyTransaction(transaction_verification_request)

    return response

def handle_order_queue(order_data):
    """
    Insert the order into the order queue.
    """
    with grpc.insecure_channel("order_queue:50054") as channel:
        stub = order_queue_grpc.OrderQueueServiceStub(channel)

        # Build the gRPC request
        order_queue_request = order_queue.EnqueueRequest(
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

        response = stub.Enqueue(order_queue_request)

    return response

@app.route("/checkout", methods=["POST"])
def checkout():
    """
    Handles the checkout process for an order, including fraud detection, transaction verification,
    and book suggestions.

    This endpoint processes a POST request containing order details, performs fraud detection using
    the FBI Wanted API, verifies the transaction using a sentiment analysis of a Kanye West quote,
    and provides book suggestions from OpenLibrary. The response includes the order status and
    suggested books.

    Returns:
        tuple: A JSON response containing the order ID, status, and suggested books, along with
        an HTTP status code. If an error occurs, returns an appropriate error message and status code.

    Logs:
        - Logs the receipt of the request.
        - Logs the progress and results of fraud detection, transaction verification, and suggestions.
        - Logs errors if any occur during processing.
    """
    try:
        # Init vector clock (originally initialized as a class, but changed to a dict for simplicity)
        vc = {
            "orchestrator": 0,
            "fraud_detection": 0,
            "suggestions": 0,
            "transaction_verification": 0,
        }
        # Increment orchestrator vector clock
        vc["orchestrator"] += 1
        print(vc)
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

        order_id = str(uuid.uuid4())
        print(f"Order ID: {order_id}")

        order_data = {
            "order_id": order_id,
            "items": items,
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
            "shipping_method": shipping_method,
            "gift_wrapping": gift_wrapping,
            "terms_accepted": terms_accepted,
        }

        logger.info("Received submit order request")

        # Initialise the executor
        executor = futures.ThreadPoolExecutor(max_workers=3)

        # Temporarily commented out for checkpoints 3 and 4
        """ # Initialise the order in the microservices and increment each's vector clock by 1
        vc["fraud_detection"] += 1
        print(vc)
        fraud_detection_init_order = executor.submit(handle_init_order_fraud_detection, order_data)
        vc["suggestions"] += 1
        print(vc)
        suggestions_init_order = executor.submit(handle_init_order_suggestions, order_data)
        vc["transaction_verification"] += 1
        print(vc)
        transaction_verification_init_order = executor.submit(handle_init_order_transaction_verification, order_data)
        print(fraud_detection_init_order.result(), suggestions_init_order.result(), transaction_verification_init_order.result())

        # Increment orchestrator vector clock after initialising the order with the microservices
        vc["orchestrator"] += 1
        print(vc)

        order_id_request = {"order_id": order_id, "vector_clock": vc}

        # Events a and b: check if the book list is nonempty and if the user data is complete
        future_tv_booklist = executor.submit(
            handle_transaction_verification_a, order_id_request
            ) # Event c is also called inside
        future_tv_userdata = executor.submit(
            handle_transaction_verification_b, order_id_request
            ) # Event d is also called inside
        
        # Consolidate and merge vector clocks
        clock_ac = future_tv_booklist.result().vector_clock
        clock_bd = future_tv_userdata.result().vector_clock
        vc = merge_vector_clocks(vc, clock_ac)
        vc = merge_vector_clocks(vc, clock_bd)

        vc["orchestrator"] += 1
        print(vc)
        # Update the vector clock in the order_id_request
        order_id_request["vector_clock"] = vc

        # Events a, b, c and d: wait for the results of the book list and user data verification
        if not future_tv_booklist.result().is_verified:
            order_status_response = {
                "orderId": order_id_request["order_id"],
                "status": "Order Rejected - Nothing Ordered or Bad Credit Card Format",
                "suggestedBooks": [],
            }
            logger.info(
                "Transaction Verification Service: No books ordered or credit card data in wrong format. Rejecting order."
            )
            return json.dumps(order_status_response), 200
        
        if not future_tv_userdata.result().is_verified:
            order_status_response = {
                "orderId": order_id_request["order_id"],
                "status": "Order Rejected - User Data Incomplete or Fraud Detected",
                "suggestedBooks": [],
            }
            logger.info(
                "Transaction Verification Service: User data incomplete or fraud detected. Rejecting order."
            )
            return json.dumps(order_status_response), 200
        
        # Events k and e: ask Kanye and check credit card validity
        future_transaction_verification = executor.submit(
            handle_transaction_verification, order_id_request
        )
        future_fd_cc = executor.submit(
            handle_fraud_detection_cc, order_id_request
        )
        logger.info("Transaction Verification Service: Request sent.")

        # Consolidate and merge vector clocks
        clock_k = future_fd_cc.result().vector_clock
        clock_e = future_transaction_verification.result().vector_clock
        vc = merge_vector_clocks(vc, clock_k)
        vc = merge_vector_clocks(vc, clock_e)
        vc["orchestrator"] += 1
        print(vc)
        # Update the vector clock in the order_id_request
        order_id_request["vector_clock"] = vc

        # Events k and e: wait for Kanye's answer and credit card validation results
        if not future_fd_cc.result().is_verified:
            order_status_response = {
                "orderId": order_id_request["order_id"],
                "status": "Order Rejected - Credit Card Verification Failed",
                "suggestedBooks": [],
            }

            logger.info(
                "Fraud Detection Service: Credit Card doesn't work. Rejecting order."
            )
            return json.dumps(order_status_response), 200
        transaction_verification_result = future_transaction_verification.result()

        if not transaction_verification_result.is_verified:
            order_status_response = {
                "orderId": order_id_request["order_id"],
                "status": "Order Rejected - Kanye Said No",
                "suggestedBooks": [],
            }
            logger.info(
                "Transaction Verification Service: Could not verify transaction. Rejecting order."
            )
            return json.dumps(order_status_response), 200
        logger.info("Transaction Verification Service: Transaction verified.")

        # Event f: ask OpenLibrary for book suggestions
        future_suggestions = executor.submit(
            handle_suggestions, order_id_request
        )
        logger.info("Suggestions Service: Request sent.")
        suggestions_result = future_suggestions.result()
        logger.info("Suggestions Service: Recieved suggestions.")
        suggested_books = [
            {"bookId": book.bookId, "title": book.title, "author": book.author}
            for book in suggestions_result.suggested_books
        ]
        # Increment vector clock
        clock_f = suggestions_result.vector_clock
        vc = merge_vector_clocks(vc, clock_f)
        vc["orchestrator"] += 1
        print(vc)
        # Update the vector clock in the order_id_request
        order_id_request["vector_clock"] = vc """

        # THIS IS COPIED FROM ABOVE TO STOP SOME FRAUDULENT ORDERS
        vc["fraud_detection"] += 1
        fraud_detection_init_order = executor.submit(handle_init_order_fraud_detection, order_data)
        wewait = fraud_detection_init_order.result()
        order_id_request = {"order_id": order_id, "vector_clock": vc}
        future_fd_cc = executor.submit(
            handle_fraud_detection_cc, order_id_request
        )
        logger.info("Transaction Verification Service: Request sent.")
        if not future_fd_cc.result().is_verified:
            order_status_response = {
                "orderId": order_id_request["order_id"],
                "status": "Order Rejected - Credit Card Verification Failed",
                "suggestedBooks": [],
            }

            logger.info(
                "Fraud Detection Service: Credit Card doesn't work. Rejecting order."
            )
            return json.dumps(order_status_response), 200
        # THIS IS COPIED FROM ABOVE TO STOP SOME FRAUDULENT ORDERS IT IS TO BE DELETED

        # Queue the order
        future_order_queue = executor.submit(
            handle_order_queue, order_data
        )
        logger.info("Order Queue Service: Order queued.")

        # Final response with books following the provided YAML specification for the bookstore
        order_status_response = {
            "orderId": order_data["order_id"],
            "status": "Order Approved",
            "suggestedBooks": [{}] #suggested_books,
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
