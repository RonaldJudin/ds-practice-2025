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
transaction_verification_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/transaction_verification")
)
sys.path.insert(0, transaction_verification_grpc_path)
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc

import grpc
from concurrent import futures
from textblob import TextBlob
import requests


# Request a kanye quote from KAAS (Kanye As A Service)
def get_kanye_quote():
    response = requests.get("https://api.kanye.rest/")
    if response.status_code == 200:
        return response.json().get("quote", "")
    return None


# Analyze the sentiment of the quote using the TextBlob library
def analyze_sentiment(quote):
    blob = TextBlob(quote)
    # Polarity ranges from -1 to 1
    sentiment_score = blob.sentiment.polarity
    return sentiment_score > -0.2


class TransactionVerificationService(
    transaction_verification_grpc.TransactionVerificationServiceServicer
):
    def VerifyTransaction(self, request, context):
        """
        Verifies a transaction based on the sentiment of a quote from the Kanye West API.

        This function handles the transaction verification process by fetching a random quote
        from the Kanye West API and analyzing its sentiment using the TextBlob NLP library. If the sentiment
        is positive, the transaction is marked as verified. If the sentiment is negative or if
        no quote is retrieved, the transaction is marked as unverified.

        Args:
            request: The transaction verification request object containing details about the transaction.
            context: The gRPC context for handling the request.

        Returns:
            transaction_verification.TransactionVerificationResponse: A response object indicating
            whether the transaction is verified (True) or unverified (False).

        Logs:
            - Logs the receipt of the request.
            - Logs if Kanye West refuses to provide a quote.
            - Logs if Kanye West approves or refuses the transaction based on sentiment analysis.
            - Logs the sending of the response.
        """
        logger.info("Transaction Verification Service: Request received.")

        # Create a TransactionVerificationResponse object
        response = transaction_verification.TransactionVerificationResponse()

        # Fetch a quote from the Kanye West API and use NLP library to analyze sentiment.
        # If negative sentiment, mark transaction as unverified (Kanye West does not approve).
        quote = get_kanye_quote()
        if not quote:
            logger.info(
                "Transaction Verification Service: Kanye West refused to give a quote."
            )
            response.is_verified = False
            return response

        is_positive_sentiment = analyze_sentiment(quote)
        if is_positive_sentiment:
            logger.info(
                "Transaction Verification Service: Kanye West approved the transaction."
            )
            response.is_verified = True
            return response

        response.is_verified = False
        logger.info(
            "Transaction Verification Service: Kanye West refused the transaction."
        )
        logger.info("Transaction Verification Service: Response sent.")
        return response


def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor())
    # Add TransactionVerificationService
    transaction_verification_grpc.add_TransactionVerificationServiceServicer_to_server(
        TransactionVerificationService(), server
    )
    # Listen on port 50053
    port = "50053"
    server.add_insecure_port("[::]:" + port)
    # Start the server
    server.start()
    print("Server started. Listening on port 50053.")
    # Keep thread alive
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
