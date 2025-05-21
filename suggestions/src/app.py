import sys
import os
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
    "service.name": os.environ.get("SERVICE_NAME", "suggestions")
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

import requests
from bs4 import BeautifulSoup
import random

# This set of lines are needed to import the gRPC stubs.
# The path of the stubs is relative to the current file, or absolute inside the container.
# Change these lines only if strictly needed.
FILE = __file__ if "__file__" in globals() else os.getenv("PYTHONFILE", "")
suggestions_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/suggestions")
)
sys.path.insert(0, suggestions_grpc_path)
import suggestions_pb2 as suggestions
import suggestions_pb2_grpc as suggestions_grpc

import grpc
from concurrent import futures


def get_random_book():
    url = "https://openlibrary.org/random"
    response = requests.get(url, allow_redirects=True)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title_tag = soup.find("h1", class_="work-title")
        title = title_tag.text.strip() if title_tag else "Unknown Title"

        # Extract author
        author_tag = soup.select_one("h2.edition-byline a")
        author = author_tag.text.strip() if author_tag else "Unknown Author"

        return title, author

    return None, None


class SuggestionsService(suggestions_grpc.SuggestionsServiceServicer):
    orders = {}

    def InitOrder(self, request, context):
        """
        Initializes a new order in the suggestions system.

        This function initializes a new order in the suggestions system by storing the order
        details in a dictionary. The order details include the user, user comment, billing address,
        and credit card information.

        Args:
            request: The order initialization request object containing order details.
            context: The gRPC context for handling the request.

        Returns:
            suggestions.OrderInitResponse: A response object indicating the successful
            initialization of the order.

        Logs:
            - Logs the receipt of the request.
            - Logs the successful initialization of the order.
            - Logs the sending of the response.
        """
        logger.info("Suggestions Service: Order initialization request received.")
        # Create an InitOrderResponse object
        response = suggestions.InitOrderResponse()
        # Store the order details in the dictionary
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
        response.order_id = request.order_id
        return response

    def GetSuggestions(self, request, context):
        """
        Provides book suggestions by scraping random books from the OpenLibrary website.

        This function generates a list of suggested books by calling the `get_random_book`
        function twice. Each book's title and author are scraped from OpenLibrary, and a unique
        book ID is generated. The suggested books are added to the response object, which is
        then returned to the client.

        Args:
            request: The suggestions request object (unused in this implementation).
            context: The gRPC context for handling the request.

        Returns:
            suggestions.SuggestionsResponse: A response object containing a list of suggested books.

        Logs:
            - Logs the receipt of the request.
            - Logs an error if a book cannot be scraped.
            - Logs the successful retrieval of suggested books.
            - Logs the sending of the response.
        """
        logger.info("Suggestions Service: Request received.")

        # Create a SuggestionsResponse object
        response = suggestions.SuggestionsResponse()
        suggested_books = []
        for _ in range(2):
            # Scrape random book from OpenLibrary
            title, author = get_random_book()
            if title and author:
                book = suggestions.Book(
                    bookId=str(random.randint(10000, 99999)), title=title, author=author
                )
                suggested_books.append(book)
            else:
                logger.error("Suggestions Service: Failed to scrape a book.")

        logger.info("Suggestions Service: Found suggested books.")
        response.suggested_books.extend(suggested_books)
        logger.info("Suggestions Service: Response sent.")

        # Increment vector clock
        request.vector_clock["suggestions"] += 1
        print(request.vector_clock)
        response.vector_clock.clear()  # Clear the existing map
        response.vector_clock.update(request.vector_clock)  # Copy the vector clock

        return response


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add SuggestionsService
    suggestions_grpc.add_SuggestionsServiceServicer_to_server(
        SuggestionsService(), server
    )
    # Listen on port 50052
    port = "50052"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50052.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
