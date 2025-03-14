# Interactive Brokers Web API

## Video Walkthrough

https://www.youtube.com/watch?v=CRsH9TKveLo

## Requirements

* Docker Desktop - https://www.docker.com/products/docker-desktop/

## Clone the source code
```
git clone https://github.com/hackingthemarkets/interactive-brokers-web-api.git
```

## Bring up the container
```
docker-compose up
```

## Getting a command line prompt

```
docker exec -it ibkr bash
```

## Accessing the web app

You can access the web app by opening your web browser and going to:

```
http://localhost:5002
```

This will show you the main dashboard. From there you can access different features:

1. Dashboard (main page): `http://localhost:5002/`
2. Portfolio: `http://localhost:5002/portfolio`
3. Orders: `http://localhost:5002/orders`
4. Watchlists: `http://localhost:5002/watchlists`
5. Market Scanner: `http://localhost:5002/scanner`
6. Symbol Lookup: `http://localhost:5002/lookup`

The web interface should show you your account information and allow you to interact with your Interactive Brokers account. You'll need to log in with your IB credentials when you first access it.

Would you like me to help you test any specific feature or check if the connection is working properly?
