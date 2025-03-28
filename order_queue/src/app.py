import threading

class OrderQueueService:
    def __init__(self):
        self.queue = []  # Could be replaced with a priority queue
        self.lock = threading.Lock()

    def Enqueue(self, order):
        """
        Adds an order to the queue.

        Args:
            order: The order object to be added to the queue.

        Returns:
            bool: True if the order was successfully added, False otherwise.
        """
        with self.lock:
            self.queue.append(order)
            print(f"Order {order.order_id} added to queue.")
            return True  # Return True to indicate success

    def Dequeue(self):
        """
        Removes an order from the queue.

        Returns:
            tuple: (bool, order) where the boolean indicates success, and the order is the dequeued order.
        """
        with self.lock:
            if len(self.queue) == 0:
                print("Queue is empty.")
                return False, None
            order = self.queue.pop(0)
            print(f"Order {order.order_id} removed from queue.")
            return True, order