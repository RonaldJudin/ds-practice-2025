from locust import HttpUser, task, between
import random
import json

# Single non-fraudulent order: Demonstrate a test scenario where a single non-fraudulent order is created from the frontend and verified for correctness.
# This can be done manually or with Locust, but the corresponding Locust class would conflict with the other two scenarios realised with it.

# Multiple non-fraudulent non-conflicting orders: Create automated tests to handle scenarios involving multiple simultaneous non-fraudulent orders that do not conflict with each other. Non-conflicting means, for instance, that the orders attempt to purchase different books. Eventually, you may add some delays in specific components, to simulate shorter or longer execution times for different orders.
# This cannot be done manually, and Locust is also unable to do this because Locust users behave independently and randomly.

# Multiple mixed orders: Automate test scenarios that involve a mixture of fraudulent and non-fraudulent orders, ensuring proper handling and validation.
# For this, we have the Buyer class. It must be called with one Locust user for this scenario.

# Conflicting orders: Define and automate test scenarios for orders that contain conflicting requests, such as attempting to purchase the same book simultaneously.
# The Buyer class can also be used for this. It must be called with multiple Locust users for this scenario.

# The results for the last two scenarios look the same, as they should if the system handles them correctly.

class Buyer(HttpUser):
    host = "http://localhost:8081"
    wait_time = between(0.1, 1)
    @task
    def buy_book_correctly(self):
        payload = {
                'user': {
                    'name': 'krõll',
                    'contact': 'vanaema@vana.ee',
                },
                'creditCard': {
                    'number': '3721111111111111',
                    'expirationDate': '12/25',
                    'cvv': '123',
                },
                'userComment': 'Please handle with care.',
                'items': [
                    { 'name': "Book A", 'quantity': 1 },
                    { 'name': "Book B", 'quantity': 2 }
                ],
                'billingAddress': {
                    'street': '123 Main St',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip': '62701',
                    'country': 'USA',
                },
                'shippingMethod': 'Standard',
                'giftWrapping': True,
                'termsAccepted': True,
            }
        headers = {'content-type': 'application/json'}
        self.client.post("/checkout", data=json.dumps(payload), headers=headers)


    @task
    def buy_book_fraudulently(self):
        payload = {
                'user': {
                    'name': 'krõll',
                    'contact': 'vanaema@vana.ee',
                },
                'creditCard': {
                    'number': '411111111111111', # Invalid card number
                    'expirationDate': '12/25',
                    'cvv': '123',
                },
                'userComment': 'Please handle with care.',
                'items': [
                    { 'name': "Book A", 'quantity': 1 },
                    { 'name': "Book B", 'quantity': 2 }
                ],
                'billingAddress': {
                    'street': '123 Main St',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip': '62701',
                    'country': 'USA',
                },
                'shippingMethod': 'Standard',
                'giftWrapping': True,
                'termsAccepted': True,
            }
        headers = {'content-type': 'application/json'}
        self.client.post("/checkout", data=json.dumps(payload), headers=headers)

a="""
class SingleBuyer(HttpUser):
    host = "http://localhost:8081"
    wait_time = between(1, 2)
    @task
    def buy_a_book(self):
        payload = {
                'user': {
                    'name': 'krõll',
                    'contact': 'vanaema@vana.ee',
                },
                'creditCard': {
                    'number': '3721111111111111',
                    'expirationDate': '12/25',
                    'cvv': '123',
                },
                'userComment': 'Please handle with care.',
                'items': [
                    { 'name': "Book A", 'quantity': 1 },
                    { 'name': "Book B", 'quantity': 2 }
                ],
                'billingAddress': {
                    'street': '123 Main St',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip': '62701',
                    'country': 'USA',
                },
                'shippingMethod': 'Standard',
                'giftWrapping': True,
                'termsAccepted': True,
            }
        headers = {'content-type': 'application/json'}
        self.client.post("/checkout", data=json.dumps(payload), headers=headers)

class MultipleBuyers(HttpUser):
    host = "http://localhost:8081"
    wait_time = between(1, 2)
    @task
    def buy_book_a(self):
        payload = {
                'user': {
                    'name': 'krõll',
                    'contact': 'vanaema@vana.ee',
                },
                'creditCard': {
                    'number': '3721111111111111',
                    'expirationDate': '12/25',
                    'cvv': '123',
                },
                'userComment': 'Please handle with care.',
                'items': [
                    { 'name': "Book A", 'quantity': 1 }
                ],
                'billingAddress': {
                    'street': '123 Main St',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip': '62701',
                    'country': 'USA',
                },
                'shippingMethod': 'Standard',
                'giftWrapping': True,
                'termsAccepted': True,
            }
        headers = {'content-type': 'application/json'}
        self.client.post("/checkout", data=json.dumps(payload), headers=headers)

    @task
    def buy_book_b(self):
        payload = {
                'user': {
                    'name': 'krõll',
                    'contact': 'vanaema@vana.ee',
                },
                'creditCard': {
                    'number': '3721111111111111',
                    'expirationDate': '12/25',
                    'cvv': '123',
                },
                'userComment': 'Please handle with care.',
                'items': [
                    { 'name': "Book B", 'quantity': 1 }
                ],
                'billingAddress': {
                    'street': '123 Main St',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip': '62701',
                    'country': 'USA',
                },
                'shippingMethod': 'Standard',
                'giftWrapping': True,
                'termsAccepted': True,
            }
        headers = {'content-type': 'application/json'}
        self.client.post("/checkout", data=json.dumps(payload), headers=headers)

class MixedBuyers(HttpUser):
    host = "http://localhost:8081"
    wait_time = between(1, 2)
    @task
    def buy_book_correctly(self):
        payload = {
                'user': {
                    'name': 'krõll',
                    'contact': 'vanaema@vana.ee',
                },
                'creditCard': {
                    'number': '3721111111111111',
                    'expirationDate': '12/25',
                    'cvv': '123',
                },
                'userComment': 'Please handle with care.',
                'items': [
                    { 'name': "Book A", 'quantity': 1 }
                ],
                'billingAddress': {
                    'street': '123 Main St',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip': '62701',
                    'country': 'USA',
                },
                'shippingMethod': 'Standard',
                'giftWrapping': True,
                'termsAccepted': True,
            }
        headers = {'content-type': 'application/json'}
        self.client.post("/checkout", data=json.dumps(payload), headers=headers)


    @task
    def buy_book_fraudulently(self):
        payload = {
                'user': {
                    'name': 'krõll',
                    'contact': 'vanaema@vana.ee',
                },
                'creditCard': {
                    'number': '411111111111111', # Invalid card number
                    'expirationDate': '12/25',
                    'cvv': '123',
                },
                'userComment': 'Please handle with care.',
                'items': [
                    { 'name': "Book B", 'quantity': 2 }
                ],
                'billingAddress': {
                    'street': '123 Main St',
                    'city': 'Springfield',
                    'state': 'IL',
                    'zip': '62701',
                    'country': 'USA',
                },
                'shippingMethod': 'Standard',
                'giftWrapping': True,
                'termsAccepted': True,
            }
        headers = {'content-type': 'application/json'}
        self.client.post("/checkout", data=json.dumps(payload), headers=headers)
"""