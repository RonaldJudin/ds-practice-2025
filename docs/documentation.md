# Bookstore documentation

Our bookstore consists of the following components:

 - frontend, which is for the user to interact with;
 - orchestrator, which organises a response to the user's book order;
 - fraud detection, which detects fraud;
 - transaction verification, which verifies the transaction;
 - suggestions, which compiles a list of book suggestions to accompany a positive order response.
 - order queue, which stores unprocessed orders;
 - executor, which processes orders from the queue;
 - database, which stores and modifies information about the store's stock;
 - payment service, which handles users' payments;
 - observability, which collects system metrics and traces and displays them.

 The fraud detection, transaction verification and suggestions service are not operational for checkpoint 3 or 4.
 The transaction verification service is partly operational for checkpoint 4.

![Figure 1. Our bookstore's architectural diagram](Architecture%20diagram.svg)

## Orchestrator
The orchestrator receives a book order from the user with all the information they input to the bookstore website's form. The orchestrator creates separate threads to contact the fraud detection, transaction verification and suggestions services. However, it creates these sequentially due to the APIs involved in all three microservices: we do not want to make too many requests to third parties, so the orchestrator waits until one API has produced a positive response before making the next API call. If one microservice produces a negative response, the orchestrator does not call the next microservice(s), but denies the book order and has the frontend display the according message. If all microservices produce positive responses, the orchestrator approves the book order and has the frontend display the message of success along with two book suggestions. The orchestrator then forwards the order to the order queue.
## Fraud detection
The fraud detection microservice receives as input the client's name from the orchestrator and makes a call to the FBI Most Wanted database with it. If any one of the client's names (first and last names etc. are considered separately) matches exactly with any one of the names in FBI's database, the transaction is flagged as fraud and the microservice returns a negative response: request denied. If the call to FBI's API returns no results, the request is approved.
## Transaction verification
The transaction verification microservice makes a call to the Kanye West API, which returns a random quote from Kanye West. That quote is then run through sentiment analysis, the values of which range from -1 to 1. Kanye is said to have verified the transaction if the sentiment analysis returns a score of at least -0,2. The microservice will respond accordingly.
## Suggestions
The suggestions microservice makes a simple HTTP request to OpenLibrary's website and receives a webpage of a random book. It then scrapes the webpage to get the book's title and author's name. The process is then repeated. The two pieces of book data are returned to the orchestrator as book suggestions.
## Order queue
The order queue receives approved orders from the orchestrator and orders them by priority. It also dequeues them as needed.
## Executor
The order executor works in three replicas that elect the leader using a modified bully algorithm. The leader queries the order queue every second or instantly after processing an order. If the queue has something, it is dequeued and the executor processes it. The executor organises a two-phase commit process with the database and the payment service for processing the order. If at least one of them is down, the executor waits using exponential backoff, but does not cancel the order. The non-leading replicas check on the leader every second and start elections if the leader does not respond in time. An election is also started whenever a replica comes online.
## Database
The database works in three replicas and stores information about every book the store has had in stock and its current quantity. When queried by the executor, the database can send information about its stock or modify it, most commonly by decrementing. Each replica uses a lock to prevent concurrent writes to it by multiple clients or other processes. To maintain consistency between replicas, a primary-based protocol is used: only one replica is exposed to the executor at a time and stock information is sent to the other replicas after each write. This also ensures that if a secondary replica is down for an extended period and can't carry out instructions of orders, it still receives up-to-date information about the stock.
## Payment
The payment service responds to the executor's requests for preparing, committing and aborting orders, but otherwise operates on dummy logic.
## Observability
Metrics are collected for the number of orders made, distinguishing between correct orders (that are queued) and fraudulent orders, the average response time and the queue size. They are displayed on a Grafana dashboard. The charts on the dashboard update once a minute.

![Figure 2. Our bookstore's system diagram](System%20diagram.svg)
