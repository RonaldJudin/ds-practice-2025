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
    books = {"Book A": 1000000, "Book B": 2000000}
    pending_transactions = {}

    def __init__(self, database_id, known_ids):
        self.database_id = database_id
        self.known_ids = known_ids

    def Read(self, request, context):
        return books_database.ReadResponse(stock=self.books[request.title])
    
    def Write(self, request, context):
        title = request.title
        stock = request.new_stock

        self.books[title] = stock
        return books_database.WriteResponse(success=True)

    def IncrementStock(self, request, context):
        title = request.title
        new_stock = request.new_stock

        self.books[title] += new_stock
        return books_database.WriteResponse(success=True)
    
    def DecrementStock(self, request, context):
        title = request.title
        new_stock = request.new_stock

        self.books[title] -= new_stock
        logger.info(f"BooksDatabaseService decremented stock for {title}: {new_stock}. In stock: {self.books[title]}")
        return books_database.WriteResponse(success=True)

    def Prepare(self, request, context):
        order_id = request.order_id
        title = request.title
        stock = request.stock

        if order_id in self.pending_transactions:
            return books_database.PrepareResponse(ready=False)

        self.pending_transactions[order_id] = (title, stock)
        logger.info(f"BooksDatabaseService prepared for order: {order_id}")
        return books_database.PrepareResponse(ready=True)
    
    def Commit(self, request, context):
        order_id = request.order_id

        if order_id not in self.pending_transactions:
            return books_database.CommitResponse(success=False)

        title, stock = self.pending_transactions[order_id]
        self.books[title] -= stock
        del self.pending_transactions[order_id]
        logger.info(f"BooksDatabaseService committed for order: {order_id}")
        return books_database.CommitResponse(success=True)
    
    def Abort(self, request, context):
        order_id = request.order_id

        if order_id in self.pending_transactions:
            del self.pending_transactions[order_id]
            logger.info(f"BooksDatabaseService aborted for order: {order_id}")
            return books_database.AbortResponse(aborted=True)
        
        return books_database.AbortResponse(aborted=False)


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())

    # Get the database ID and known IDs from environment variables
    database_id = int(os.getenv("DATABASE_ID"))
    known_ids = os.getenv("KNOWN_IDS").split(",")
    known_ids = [int(i) for i in known_ids]

    # Add DatabaseService to the server
    books_database_grpc.add_BooksDatabaseServiceServicer_to_server(
        BooksDatabaseService(database_id, known_ids), server
    )
    # Listen on designated port
    port = str(os.getenv("PORT"))
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print(f"Server started. Listening on port {port}.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
