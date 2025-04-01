# Interactive Brokers Gateway Setup Guide

## Prerequisites
- macOS system
- Docker installed and running
- Interactive Brokers account
- Stable internet connection

## Step 1: Download IB Gateway

1. Visit the official Interactive Brokers download page:
   ```
   https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
   ```

2. Download IB Gateway for macOS
   - Click on "Download" for the macOS version
   - The file will be named something like `ibgateway-stable-standalone-{version}.dmg`

## Step 2: Install IB Gateway

1. Open the downloaded .dmg file
2. Drag the IB Gateway application to your Applications folder
3. First time running:
   ```
   - Go to Applications folder
   - Right-click on IB Gateway
   - Select "Open"
   - Click "Open" again if prompted about unverified developer
   ```

## Step 3: Configure IB Gateway

1. Launch IB Gateway
   ```
   - Select "Live Trading" or "Paper Trading" based on your needs
   - Trading Mode: Select "IB API"
   ```

2. Login Settings:
   ```
   - Username: Your IB account username
   - Password: Your IB account password
   - Trading Mode: IB API
   - Region: Select your region (e.g., America)
   ```

3. Configuration Settings:
   ```
   - Click on Configure → Settings
   - API → Enable ActiveX and Socket Clients
   - API → Socket Port: 7496 (default)
   - API → Allow connections from localhost only: Uncheck if needed
   ```

## Step 4: Setup Environment Variables

1. Create/edit your environment file:
   ```
   IBKR_ACCOUNT_ID="Your_Account_ID"  # Format: U1234567
   ```

## Step 5: Running the Web API

1. Start IB Gateway:
   ```
   - Launch IB Gateway
   - Log in with your credentials
   - Ensure it shows "Connected" status
   ```

2. Start the Web API container:
   ```bash
   docker compose up
   ```

3. Verify the connection:
   ```
   - Open browser: https://localhost:5055
   - Accept the self-signed certificate warning
   - You should see the login/authentication page
   ```

## Available Endpoints

After successful setup, you can access:
- Dashboard: https://localhost:5055/
- Portfolio: https://localhost:5055/portfolio
- Orders: https://localhost:5055/orders
- Watchlists: https://localhost:5055/watchlists
- Market Scanner: https://localhost:5055/scanner
- Symbol Lookup: https://localhost:5055/lookup

## Troubleshooting

1. Connection Issues:
   ```
   - Verify IB Gateway is running and connected
   - Check if ports 5055 and 7496 are open
   - Ensure your IB account is active and enabled for API access
   ```

2. Authentication Issues:
   ```
   - Confirm your IBKR_ACCOUNT_ID is correct
   - Verify IB Gateway login credentials
   - Check IB Gateway logs for connection status
   ```

3. Common Error Solutions:
   ```
   - Restart IB Gateway if connection is unstable
   - Clear browser cache if web interface is not loading
   - Check Docker logs: docker logs ibkr
   ```

## Maintenance

1. Regular Updates:
   ```
   - Update IB Gateway when prompted
   - Keep Docker images updated: docker compose pull
   - Check for web API updates periodically
   ```

2. Security Best Practices:
   ```
   - Regularly change IB account password
   - Monitor API access logs
   - Keep system and Docker up to date
   ```

## Shutdown Procedure

1. Proper Shutdown:
   ```bash
   # Stop the web API container
   docker compose down

   # Close IB Gateway properly
   - Click on File → Exit
   - Wait for proper shutdown
   ```

## Additional Resources

- [Interactive Brokers API Documentation](https://www.interactivebrokers.com/en/trading/ib-api.php)
- [IB Gateway Guide](https://www.interactivebrokers.com/en/software/ibgateway/ibgateway.htm)
- [API Support](https://www.interactivebrokers.com/en/support/solutions/trading/api-solutions.php) 