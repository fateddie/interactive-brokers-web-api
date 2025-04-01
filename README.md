# Interactive Brokers Web API Integration

A Flask-based web application that integrates with Interactive Brokers' Client Portal API to provide a modern, user-friendly interface for trading and portfolio management.

## 🚀 Features

### Portfolio Management
- Dashboard with account overview and summary
- Real-time position tracking
- Portfolio performance metrics
- Risk monitoring with drawdown tracking

### Trading Features
- Stock lookup and market data
- Order management (place, track, cancel)
- Watchlist management
- Market scanner with customizable filters
- Trade planning assistant
- Risk exposure monitoring

### Advanced Features
- Trading knowledge graph visualization
- Trade plan validation
- Pair trading context analysis
- Risk management rules enforcement
- Drawdown control system

## 🛠️ Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: DaisyUI + Tailwind CSS
- **Data Source**: Interactive Brokers Client Portal API
- **Authentication**: IB Gateway integration
- **Environment**: Docker containerization

## 📋 Prerequisites

- Docker installed on your system
- Interactive Brokers account
- IB Gateway or TWS (Trader Workstation)

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the `webapp` directory:
```
IBKR_ACCOUNT_ID=your_account_id
GATEWAY_PORT=5055
FLASK_PORT=5056
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
```

### Ports
- IB Gateway: 5055 (HTTPS)
- Flask Application: 5056 (HTTP)

## 🚀 Getting Started

1. **Build and Run Docker Container**
```bash
docker build -t ibkr-rest-api .
docker run -d --name ibkr -p 5055:5055 -p 5056:5056 ibkr-rest-api
```

2. **Access IB Gateway**
- Open https://localhost:5055
- Log in with your Interactive Brokers credentials
- Accept the SSL certificate warning (development only)

3. **Access Web Application**
- Open http://localhost:5056
- Navigate through the available features

## 📱 Available Endpoints

### Portfolio Management
- `/` - Dashboard with account overview
- `/portfolio` - Current positions and performance
- `/risk` - Risk monitoring dashboard

### Trading Operations
- `/orders` - Order management
- `/lookup` - Stock symbol lookup
- `/contract/<contract_id>/<period>` - Contract details and charts
- `/scanner` - Market scanner

### Watchlist Management
- `/watchlists` - View and manage watchlists
- `/watchlists/create` - Create new watchlist
- `/watchlists/<id>` - View specific watchlist
- `/watchlists/<id>/delete` - Delete watchlist

### Analysis Tools
- `/check_plan` - Trade plan validation
- `/log_trade` - Trade logging with risk checks
- `/graph` - Trading knowledge graph visualization
- `/context/<pair>` - Trading pair context analysis

## 🔒 Security Notes

- SSL certificates are self-signed for development
- Ensure proper authentication through IB Gateway
- Keep your API credentials secure
- Don't expose ports unnecessarily in production

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
