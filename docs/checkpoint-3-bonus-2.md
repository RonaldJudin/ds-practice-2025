## Bonus Task

### Problem

If the coordinator fails then the payment and database services are potentially left in "limbo".

E.g. the payment service is left in a state of `Prepared` and is waiting for the executor to send a `Commit` or `Abort` message.

This results in blocking, which can cause: resource locking, reduced system availability/performance, and/or data inconsistencies.

### Solution

Implement a recovery protocol for the executor.

Modify the `order_queue.dequeue()` logic: wait to dequeue order until final successful `Commit` response received by executor.

**PROBLEM:** What if a new order comes in during that time, and jumps ahead of the current order being processed in the queue?

**NEW SOLUTION:** First, set the priority of the current order being processed to maximum. No new orders coming in can "jump ahead". Dequeue the order when the final successful `Commit` response received by executor.

If an executor crashes in the middle of 2PC, executor leader election gets triggered, a new executor is elected, and begins to work on the highest priority item in the queue, the incomplete order.

**_SUCCESS_**
