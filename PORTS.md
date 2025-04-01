# Port Configuration

This application uses several ports for different services:

## IB Gateway
- Port: `5055`
- URL: `https://localhost:5055`
- Purpose: Interactive Brokers Gateway login and authentication

## Web Application
- Port: `5056`
- URL: `http://localhost:5056`
- Purpose: Main web application interface including:
  - Dashboard
  - Portfolio
  - Orders
  - Watchlists
  - Market Scanner
  - Symbol Lookup
  - Graph View

## Note
The README mentions port 5002, but the current implementation uses port 5056 for the web application. Please use port 5056 to access the web interface. 