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
books_database_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/books_database")
)
sys.path.insert(0, books_database_grpc_path)
import books_database_pb2 as books_database
import books_database_pb2_grpc as books_database_grpc

import grpc
from concurrent import futures


class BooksDatabaseService(books_database_grpc.BooksDatabaseServiceServicer):
    books = {"Book 1": 1, "Book 2": 1}

    def Read(self, request, context):
        title = request.title
        return self.books[title]

    def Write(self, request, context):
        title = request.title
        new_stock = request.new_stock

        self.books[title] += new_stock
        return True


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add SuggestionsService
    books_database_grpc.add_BooksDatabaseServiceServicer_to_server(
        BooksDatabaseService(), server
    )
    # Listen on port 50052
    port = str(os.getenv("PORT"))
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print(f"Server started. Listening on port {port}.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
