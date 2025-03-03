import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
