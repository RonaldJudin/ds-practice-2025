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
fraud_detection_grpc_path = os.path.abspath(
    os.path.join(FILE, "../../../utils/pb/fraud_detection")
)
sys.path.insert(0, transaction_verification_grpc_path)
sys.path.insert(0, fraud_detection_grpc_path)
import transaction_verification_pb2 as transaction_verification
import transaction_verification_pb2_grpc as transaction_verification_grpc
import fraud_detection_pb2 as fraud_detection
import fraud_detection_pb2_grpc as fraud_detection_grpc

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

def handle_fraud_detection(order_id, vector_clock):
    """
    Process the fraud detection for the given order data.
    """
    with grpc.insecure_channel("fraud_detection:50051") as channel:
        stub = fraud_detection_grpc.FraudDetectionServiceStub(channel)

        # Build the gRPC request
        fraud_request = fraud_detection.FraudDetectionRequest(
            order_id=order_id,
            vector_clock=vector_clock
        )

        response = stub.CheckFraud(fraud_request)

    return response


class TransactionVerificationService(
    transaction_verification_grpc.TransactionVerificationServiceServicer
):
    orders = {}
    def InitOrder(self, request, context):
        """
        Initializes a new order in the transaction verification system.

        This function initializes a new order in the transaction verification system by storing the order
        details in a dictionary. The order details include the user, user comment, billing address,
        and credit card information.

        Args:
            request: The order initialization request object containing order details.
            context: The gRPC context for handling the request.

        Returns:
            transaction_verification.OrderInitResponse: A response object indicating the successful
            initialization of the order.
        """
        logger.info("Transaction Verification Service: Order initialization request received.")
        # Create an InitOrderResponse object
        response = transaction_verification.InitOrderResponse()
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
        logger.info("Transaction Verification Service: Order initialized.")
        return response
    
    def VerifyBookList(self, request, context):
        # Extract the book list from the request
        logger.info("Transaction Verification Service: Book list verification request received.")
        book_list = self.orders[request.order_id]["items"]
        # Create a CheckBookListResponse object
        response = transaction_verification.VerifyBookListResponse()
        # Increment the vector clock before embedded function call
        request.vector_clock["transaction_verification"] += 1
        print(request.vector_clock)
        response.vector_clock.clear()  # Clear the existing map
        response.vector_clock.update(request.vector_clock)  # Copy the vector clock
        # Check if the book list is empty
        response.is_verified = False
        if book_list:
            response.is_verified = True
            logger.info("Transaction Verification Service: Book list verified. Proceeding to user data verification.")
            # Proceed to verify user data
            return self.VerifyCreditCardFormat(request, context)
        logger.info("Transaction Verification Service: Book list is empty. Order not verified.")
        return response
    
    def VerifyUserData(self, request, context):
        logger.info("Transaction Verification Service: User data verification request received.")
        # Extract user data from the request
        user_data = self.orders[request.order_id]["user"]
        billing_address = self.orders[request.order_id]["billing_address"]
        credit_card = self.orders[request.order_id]["credit_card"]

        # Increment the vector clock
        # current_value = request.vector_clock.get("transaction_verification", 0)
        request.vector_clock["transaction_verification"] += 1
        print(request.vector_clock)
        # Check that no fields in these data are empty
        response = transaction_verification.VerifyUserDataResponse()

        response.vector_clock.clear()
        response.vector_clock.update(request.vector_clock)

        response.is_verified = True if user_data.name and user_data.email and billing_address.street and billing_address.city and billing_address.state and billing_address.zip and billing_address.country and credit_card.number and credit_card.expiration_date and credit_card.cvv else False
        if response.is_verified:
            logger.info("Transaction Verification Service: User data verified. Proceeding to fraud detection.")
            fraud_response = handle_fraud_detection(request.order_id, request.vector_clock)
            # If fraud_detection runs, add more up-to-date vector clock to response
            response.vector_clock.clear()  # Clear the existing map
            response.vector_clock.update(fraud_response.vector_clock)  # Copy the vector clock
            if fraud_response.is_fraudulent:
                response.is_verified = False
        logger.info("Transaction Verification Service: User data not verified. Rejecting order.")

        return response
    
    def VerifyCreditCardFormat(self, request, context):
        # Extract credit card data from the request
        credit_card_data = self.orders[request.order_id]["credit_card"]
        # Check if the credit card number is 16 digits, expiration date is in MM/YY format, and CVV is 3 digits
        response = transaction_verification.VerifyCreditCardFormatResponse()
        response.is_verified = len(credit_card_data.number) == 16 and len(credit_card_data.expiration_date) == 5 and len(credit_card_data.cvv) == 3
        if response.is_verified:
            logger.info("Transaction Verification Service: Credit card format verified.")
        else:
            logger.info("Transaction Verification Service: Credit card format wrong. Rejecting order.")
        # Increment the vector clock
        request.vector_clock["transaction_verification"] += 1
        print(request.vector_clock)
        response.vector_clock.clear()  # Clear the existing map
        response.vector_clock.update(request.vector_clock)  # Copy the vector clock
        return response
    
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
        logger.info("Transaction Verification Service: Kanye requested.")

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

        # Increment the vector clock
        request.vector_clock["transaction_verification"] += 1
        print(request.vector_clock)
        response.vector_clock.clear()  # Clear the existing map
        response.vector_clock.update(request.vector_clock)  # Copy the vector clock
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
