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
    
    def Exists(self, request, context):
        title = request.title
        exists = title in self.books.keys()
        # This is not meant to be a writing function, but the response has the same fields.
        return books_database.WriteResponse(success=exists)
    
    def Write(self, request, context):
        title = request.title
        stock = request.new_stock

        self.books[title] = stock
        logger.info(f"BooksDatabaseService ({self.database_id}) wrote {title}: {stock}. In stock: {self.books[title]}")
        return books_database.WriteResponse(success=True)

    def IncrementStock(self, request, context):
        title = request.title
        new_stock = request.new_stock

        self.books[title] += new_stock
        self.Replicate()
        return books_database.WriteResponse(success=True)
    
    def DecrementStock(self, request, context):
        title = request["title"]
        new_stock = request["new_stock"]

        self.books[title] -= new_stock
        logger.info(f"BooksDatabaseService ({self.database_id}) decremented stock for {title}: {new_stock}. In stock: {self.books[title]}")
        self.Replicate()
        return books_database.WriteResponse(success=True)
    
    def Replicate(self):
        # Sends the state of the database to the other databases
        for other_id in self.known_ids:
            if other_id != self.database_id:
                # The databases should run on ports 49664, 49665 and 49666.
                with grpc.insecure_channel(f"books_database_{other_id}:{49663+other_id}") as channel:
                    for title, stock in self.books.items():
                        # Send the WriteRequest to the other database
                        stub = books_database_grpc.BooksDatabaseServiceStub(channel)
                        stub.Write(books_database.WriteRequest(title=title, new_stock=stock))

    def Prepare(self, request, context):
        order_id = request.order_id
        title = request.title
        stock = request.stock

        # Check if the book is already part of the pending transaction for this order
        if order_id in self.pending_transactions:
            for existing_title, _ in self.pending_transactions[order_id]:
                if existing_title == title:
                    logger.error(f"Duplicate prepare request for order {order_id}, book {title}.")
                    return books_database.PrepareResponse(ready=False)

        # Add the book to the pending transaction
        if order_id not in self.pending_transactions:
            self.pending_transactions[order_id] = []
        self.pending_transactions[order_id].append((title, stock))

        # logger.info(f"BooksDatabaseService prepared for order: {order_id}, book: {title}")
        return books_database.PrepareResponse(ready=True)


    def Commit(self, request, context):
        order_id = request.order_id

        if order_id not in self.pending_transactions:
            logger.error(f"Commit failed: No pending transaction for order {order_id}.")
            return books_database.CommitResponse(success=False)

        # Commit all books in the pending transaction
        for title, stock in self.pending_transactions[order_id]:
            self.DecrementStock({"title": title, "new_stock": stock}, None)
            # logger.info(f"BooksDatabaseService committed for order {order_id}, book: {title}, stock decremented by {stock}.")

        # Remove the transaction from pending_transactions
        del self.pending_transactions[order_id]
        # logger.info(f"BooksDatabaseService committed for order: {order_id}")
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
