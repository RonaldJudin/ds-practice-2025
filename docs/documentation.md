# Bookstore documentation

Our bookstore consists of the following components:

 - frontend, which is for the user to interact with;
 - orchestrator, which organises a response to the user's book order;
 - fraud detection, which detects fraud;
 - transaction verification, which verifies the transaction;
 - suggestions, which compiles a list of book suggestions to accompany a positive order response.

![Figure 1. Our bookstore's architectural diagram]("Architecture diagram.svg")

## Orchestrator
The orchestrator receives a book order from the user with all the information they input to the bookstore website's form. The orchestrator creates separate threads to contact the fraud detection, transaction verification and suggestions services. However, it creates these sequentially due to the APIs involved in all three microservices: we do not want to make too many requests to third parties, so the orchestrator waits until one API has produced a positive response before making the next API call. If one microservice produces a negative response, the orchestrator does not call the next microservice(s), but denies the book order and has the frontend display the according message. If all microservices produce positive responses, the orchestrator approves the book order and has the frontend display the message of success along with two book suggestions.
## Fraud detection
The fraud detection microservice receives as input the client's name from the orchestrator and makes a call to the FBI Most Wanted database with it. If any one of the client's names (first and last names etc. are considered separately) matches exactly with any one of the names in FBI's database, the transaction is flagged as fraud and the microservice returns a negative response: request denied. If the call to FBI's API returns no results, the request is approved.
## Transaction verification
The transaction verification microservice makes a call to the Kanye West API, which returns a random quote from Kanye West. That quote is then run through sentiment analysis, the values of which range from -1 to 1. Kanye is said to have verified the transaction if the sentiment analysis returns a score of at least -0,2. The microservice will respond accordingly.
## Suggestions
The suggestions microservice makes a simple HTTP request to OpenLibrary's website and receives a webpage of a random book. It then scrapes the webpage to get the book's title and author's name. The process is then repeated. The two pieces of book data are returned to the orchestrator as book suggestions.

![Figure 2. Our bookstore's system diagram]("System diagram.svg")
