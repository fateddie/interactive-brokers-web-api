"""
Broker data functions for retrieving real-time trading exposure and drawdown information
from Interactive Brokers.
"""

import os
from typing import Dict, Union, Optional, List, Tuple, Any
import json
from ib_insync import IB, util, Contract, Order, Trade
import threading
from datetime import datetime, timedelta
from decimal import Decimal

# Global IB connection instance
ib = IB()
connection_lock = threading.Lock()

def ensure_ib_connection() -> bool:
    """
    Ensures there is an active connection to Interactive Brokers TWS/Gateway.
    Uses a lock to prevent multiple simultaneous connection attempts.
    
    Returns:
        bool: True if connection is established, False otherwise
    """
    with connection_lock:
        try:
            if not ib.isConnected():
                ib.connect('127.0.0.1', 7497, clientId=1)
                # Wait for connection to be established
                timeout = 5  # seconds
                start_time = datetime.now()
                while not ib.isConnected() and (datetime.now() - start_time).seconds < timeout:
                    ib.sleep(0.1)
                
                if not ib.isConnected():
                    print("Failed to connect to IB after timeout")
                    return False
                
            return True
        except Exception as e:
            print(f"Error connecting to IB: {e}")
            return False

def get_total_exposure_by_asset() -> Dict[str, float]:
    """
    Get the total exposure for each asset/symbol in lots from IB.
    Falls back to mock data if IB connection fails.
    
    Returns:
        Dict[str, float]: Dictionary mapping symbols to their exposure in lots
    """
    try:
        if not ensure_ib_connection():
            print("Warning: Using mock data due to IB connection failure")
            return get_mock_data()

        # Get portfolio data from IB
        portfolio = ib.portfolio()
        
        # Calculate exposure in lots (assuming standard lot sizes)
        exposure = {}
        for position in portfolio:
            symbol = position.contract.symbol
            # Convert position size to lots based on instrument type
            if "FX" in position.contract.secType:
                lots = abs(position.position) / 100000  # Standard FX lot = 100,000 units
            else:
                lots = abs(position.position)  # For other instruments, use direct position size
            exposure[symbol] = round(lots, 2)
        
        return exposure
        
    except Exception as e:
        print(f"Error getting exposure data from IB: {e}")
        print("Falling back to mock data")
        return get_mock_data()

def get_drawdown() -> float:
    """
    Calculate current drawdown percentage using IB account data.
    Falls back to mock data if IB connection fails.
    
    Returns:
        float: Current drawdown as a percentage
    """
    try:
        if not ensure_ib_connection():
            print("Warning: Using mock drawdown due to IB connection failure")
            return 3.5

        # Get account summary
        account_values = ib.accountSummary()
        
        # Get current Net Liquidation Value
        nlv = float(next((v.value for v in account_values if v.tag == 'NetLiquidation'), 0))
        
        # Get high water mark from stored data or calculate it
        high_water_mark = get_high_water_mark(nlv)
        
        if high_water_mark == 0:
            return 0.0
            
        # Calculate drawdown
        drawdown = ((high_water_mark - nlv) / high_water_mark) * 100
        return round(drawdown, 2)
        
    except Exception as e:
        print(f"Error calculating drawdown from IB: {e}")
        print("Falling back to mock drawdown")
        return 3.5

def get_high_water_mark(current_nlv: float) -> float:
    """
    Get or update the high water mark for the account.
    
    Args:
        current_nlv: Current Net Liquidation Value
        
    Returns:
        float: The current high water mark
    """
    hwm_file = "high_water_mark.json"
    try:
        if os.path.exists(hwm_file):
            with open(hwm_file, 'r') as f:
                data = json.load(f)
                stored_hwm = float(data.get('high_water_mark', 0))
        else:
            stored_hwm = 0

        # Update high water mark if current NLV is higher
        if current_nlv > stored_hwm:
            with open(hwm_file, 'w') as f:
                json.dump({'high_water_mark': current_nlv}, f)
            return current_nlv
            
        return stored_hwm
        
    except Exception as e:
        print(f"Error managing high water mark: {e}")
        return current_nlv

def get_mock_data() -> Dict[str, float]:
    """
    Mock data for fallback when IB connection fails.
    Returns sample position data.
    """
    return {
        "EURUSD": 1.5,
        "GBPUSD": 0.8,
        "USDJPY": 2.2,
        "AUDUSD": 1.0
    }

def create_contract(symbol: str) -> Contract:
    """
    Create an IB contract object based on the symbol.
    Handles both FX and stock contracts.
    
    Args:
        symbol: Trading symbol (e.g., 'EURUSD', 'AAPL')
        
    Returns:
        Contract: IB contract object
    """
    if len(symbol) == 6 and any(pair in symbol for pair in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']):
        # FX pair
        base = symbol[:3]
        quote = symbol[3:]
        contract = Contract(secType='CASH', symbol=base, currency=quote, exchange='IDEALPRO')
    else:
        # Stock or other instrument
        contract = Contract(secType='STK', symbol=symbol, currency='USD', exchange='SMART')
    
    return contract

def create_order(
    direction: str, 
    size: float, 
    order_type: str = 'MKT',
    limit_price: float = None,
    stop_price: float = None,
    trailing_amount: float = None,
    trailing_percent: float = None,
    tif: str = 'DAY',
    outside_rth: bool = False,
    bracket_params: Dict = None
) -> Union[Order, List[Order]]:
    """
    Create an IB order object with enhanced order types and validation.
    
    Args:
        direction: 'BUY' or 'SELL'
        size: Position size in lots
        order_type: Order type ('MKT', 'LMT', 'STP', 'STP LMT', 'TRAIL', 'TRAIL LIMIT')
        limit_price: Limit price for LMT and STP LMT orders
        stop_price: Stop price for STP and STP LMT orders
        trailing_amount: Trailing amount for TRAIL orders (absolute)
        trailing_percent: Trailing percentage for TRAIL orders
        tif: Time in force ('DAY', 'GTC', 'IOC', 'GTD')
        outside_rth: Allow trades outside regular trading hours
        bracket_params: Dictionary containing take profit and stop loss parameters:
            {
                'take_profit': float,  # Take profit price
                'stop_loss': float,    # Stop loss price
                'trailing_stop': float  # Optional trailing stop amount
            }
        
    Returns:
        Union[Order, List[Order]]: Single order or list of bracket orders
    """
    # Enhanced validation
    validate_order_parameters(
        direction=direction,
        size=size,
        order_type=order_type,
        limit_price=limit_price,
        stop_price=stop_price,
        trailing_amount=trailing_amount,
        trailing_percent=trailing_percent,
        tif=tif,
        bracket_params=bracket_params
    )
    
    # Convert lots to actual units
    units = size * 100000 if order_type == 'CASH' else size
    
    # Handle bracket orders
    if bracket_params:
        return create_bracket_orders(
            direction=direction,
            size=units,
            entry_order_type=order_type,
            entry_price=limit_price if order_type == 'LMT' else None,
            take_profit=bracket_params['take_profit'],
            stop_loss=bracket_params['stop_loss'],
            trailing_stop=bracket_params.get('trailing_stop'),
            tif=tif,
            outside_rth=outside_rth
        )
    
    # Create base order
    order = Order(
        action=direction.upper(),
        totalQuantity=abs(units),
        orderType=order_type,
        tif=tif,
        outsideRth=outside_rth,
        transmit=True
    )
    
    # Add price fields based on order type
    if order_type in ['LMT', 'STP LMT']:
        order.lmtPrice = limit_price
        
    if order_type in ['STP', 'STP LMT']:
        order.auxPrice = stop_price
        
    # Handle trailing stops
    if order_type == 'TRAIL':
        if trailing_amount:
            order.auxPrice = trailing_amount
        elif trailing_percent:
            order.trailingPercent = trailing_percent
            
    return order

def validate_order_parameters(**params) -> None:
    """
    Comprehensive order parameter validation.
    Raises ValueError for any invalid parameters.
    """
    # Direction validation
    if params['direction'].upper() not in ['BUY', 'SELL']:
        raise ValueError(f"Invalid direction: {params['direction']}. Must be 'BUY' or 'SELL'")
    
    # Order type validation
    order_type = params['order_type'].upper()
    valid_types = {'MKT', 'LMT', 'STP', 'STP LMT', 'TRAIL', 'TRAIL LIMIT'}
    if order_type not in valid_types:
        raise ValueError(f"Invalid order type: {order_type}. Must be one of {valid_types}")
    
    # Size validation
    if params['size'] <= 0:
        raise ValueError("Size must be greater than 0")
    
    # Price validations
    if order_type in ['LMT', 'STP LMT'] and params['limit_price'] is None:
        raise ValueError(f"Limit price required for {order_type} orders")
        
    if order_type in ['STP', 'STP LMT'] and params['stop_price'] is None:
        raise ValueError(f"Stop price required for {order_type} orders")
        
    # Trailing stop validations
    if order_type == 'TRAIL':
        if params['trailing_amount'] is None and params['trailing_percent'] is None:
            raise ValueError("Either trailing_amount or trailing_percent must be specified for TRAIL orders")
        if params['trailing_amount'] is not None and params['trailing_percent'] is not None:
            raise ValueError("Cannot specify both trailing_amount and trailing_percent")
            
    # Bracket order validations
    if params['bracket_params']:
        if not isinstance(params['bracket_params'], dict):
            raise ValueError("bracket_params must be a dictionary")
        required_keys = {'take_profit', 'stop_loss'}
        if not all(key in params['bracket_params'] for key in required_keys):
            raise ValueError(f"bracket_params must contain: {required_keys}")
            
    # TIF validation
    tif = params['tif'].upper()
    valid_tifs = {'DAY', 'GTC', 'IOC', 'GTD'}
    if tif not in valid_tifs:
        raise ValueError(f"Invalid TIF: {tif}. Must be one of {valid_tifs}")

def create_bracket_orders(
    direction: str,
    size: float,
    entry_order_type: str,
    entry_price: float = None,
    take_profit: float = None,
    stop_loss: float = None,
    trailing_stop: float = None,
    tif: str = 'GTC',
    outside_rth: bool = False
) -> List[Order]:
    """
    Create a bracket order (entry + take profit + stop loss).
    """
    # Determine reverse action for exit orders
    reverse_action = 'SELL' if direction.upper() == 'BUY' else 'BUY'
    
    # Create entry order
    entry = Order(
        action=direction.upper(),
        totalQuantity=abs(size),
        orderType=entry_order_type,
        tif=tif,
        outsideRth=outside_rth,
        transmit=False  # Don't transmit until we've attached child orders
    )
    
    if entry_order_type == 'LMT':
        entry.lmtPrice = entry_price
    
    # Create take profit order
    take_profit_order = Order(
        action=reverse_action,
        totalQuantity=abs(size),
        orderType='LMT',
        lmtPrice=take_profit,
        parentId=entry.orderId,
        tif=tif,
        outsideRth=outside_rth,
        transmit=False
    )
    
    # Create stop loss/trailing stop order
    if trailing_stop:
        stop_loss_order = Order(
            action=reverse_action,
            totalQuantity=abs(size),
            orderType='TRAIL',
            auxPrice=trailing_stop,
            parentId=entry.orderId,
            tif=tif,
            outsideRth=outside_rth,
            transmit=True  # This is the last order, so transmit
        )
    else:
        stop_loss_order = Order(
            action=reverse_action,
            totalQuantity=abs(size),
            orderType='STP',
            auxPrice=stop_loss,
            parentId=entry.orderId,
            tif=tif,
            outsideRth=outside_rth,
            transmit=True  # This is the last order, so transmit
        )
    
    return [entry, take_profit_order, stop_loss_order]

def modify_order(order_id: int, modifications: Dict[str, Any]) -> bool:
    """
    Modify an existing order.
    
    Args:
        order_id: The ID of the order to modify
        modifications: Dictionary of modifications to apply:
            - limit_price: New limit price
            - stop_price: New stop price
            - trailing_amount: New trailing amount
            - size: New position size
            - tif: New time in force
    
    Returns:
        bool: True if modification was successful
    """
    try:
        if not ensure_ib_connection():
            raise ConnectionError("Not connected to IB")
            
        # Find the order
        trades = ib.trades()
        trade = next((t for t in trades if t.order.orderId == order_id), None)
        
        if not trade:
            raise ValueError(f"Order {order_id} not found")
            
        order = trade.order
        
        # Apply modifications
        if 'limit_price' in modifications:
            order.lmtPrice = modifications['limit_price']
        if 'stop_price' in modifications:
            order.auxPrice = modifications['stop_price']
        if 'trailing_amount' in modifications:
            order.auxPrice = modifications['trailing_amount']
        if 'size' in modifications:
            order.totalQuantity = modifications['size']
        if 'tif' in modifications:
            order.tif = modifications['tif']
            
        # Submit the modified order
        ib.placeOrder(trade.contract, order)
        
        return True
        
    except Exception as e:
        print(f"Error modifying order: {e}")
        return False

def save_trade_log(trade_data: Dict[str, Union[str, float]]) -> None:
    """
    Save trade data to a JSON file and create actual IB trade if connected.
    
    Args:
        trade_data: Dictionary containing trade details including:
            - symbol: Trading symbol
            - direction: 'BUY' or 'SELL'
            - size: Position size in lots
            - order_type: Order type ('MKT', 'LMT', 'STP', 'STP LMT', 'TRAIL')
            - limit_price: Optional limit price
            - stop_price: Optional stop price
            - trailing_amount: Optional trailing amount
            - trailing_percent: Optional trailing percentage
            - bracket_params: Optional bracket order parameters
            - tif: Time in force ('DAY', 'GTC', 'IOC', 'GTD')
            - outside_rth: Allow trades outside regular trading hours
            - max_drawdown: Maximum allowed drawdown
    """
    try:
        # Add timestamp to trade data
        trade_data['timestamp'] = datetime.now().isoformat()
        
        # Save to local log first
        log_file = "trade_log.json"
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(trade_data)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"Error saving to local log: {e}")

        # If connected to IB, create and place the trade
        if ensure_ib_connection():
            try:
                # Create contract
                contract = create_contract(trade_data['symbol'])
                
                # Create order(s)
                order = create_order(
                    direction=trade_data['direction'],
                    size=float(trade_data['size']),
                    order_type=trade_data.get('order_type', 'MKT'),
                    limit_price=trade_data.get('limit_price'),
                    stop_price=trade_data.get('stop_price'),
                    trailing_amount=trade_data.get('trailing_amount'),
                    trailing_percent=trade_data.get('trailing_percent'),
                    tif=trade_data.get('tif', 'DAY'),
                    outside_rth=trade_data.get('outside_rth', False),
                    bracket_params=trade_data.get('bracket_params')
                )
                
                # Handle both single orders and bracket orders
                if isinstance(order, list):
                    # Bracket orders
                    trades = []
                    for o in order:
                        trades.append(ib.placeOrder(contract, o))
                    
                    # Wait for main order status
                    main_trade = trades[0]
                    timeout = 10
                    start_time = datetime.now()
                    while not main_trade.orderStatus.status and (datetime.now() - start_time).seconds < timeout:
                        ib.sleep(0.1)
                    
                    # Log all orders
                    trade_data['bracket_orders'] = []
                    for i, trade in enumerate(trades):
                        order_type = 'ENTRY' if i == 0 else 'TAKE_PROFIT' if i == 1 else 'STOP_LOSS'
                        trade_data['bracket_orders'].append({
                            'order_type': order_type,
                            'order_id': trade.order.orderId,
                            'status': trade.orderStatus.status,
                            'filled': trade.orderStatus.filled,
                            'remaining': trade.orderStatus.remaining,
                            'avg_fill_price': trade.orderStatus.avgFillPrice
                        })
                else:
                    # Single order
                    trade = ib.placeOrder(contract, order)
                    
                    # Wait for order status
                    timeout = 10
                    start_time = datetime.now()
                    while not trade.orderStatus.status and (datetime.now() - start_time).seconds < timeout:
                        ib.sleep(0.1)
                    
                    # Add IB order details to trade log
                    trade_data['ib_order_id'] = trade.order.orderId
                    trade_data['ib_status'] = trade.orderStatus.status
                    trade_data['ib_filled'] = trade.orderStatus.filled
                    trade_data['ib_remaining'] = trade.orderStatus.remaining
                    trade_data['ib_avg_fill_price'] = trade.orderStatus.avgFillPrice
                    trade_data['ib_order_type'] = order.orderType
                    trade_data['ib_tif'] = order.tif
                    
                    if hasattr(order, 'lmtPrice'):
                        trade_data['ib_limit_price'] = order.lmtPrice
                    if hasattr(order, 'auxPrice'):
                        trade_data['ib_stop_price'] = order.auxPrice
                    if hasattr(order, 'trailingPercent'):
                        trade_data['ib_trailing_percent'] = order.trailingPercent
                
                # Update the log file with IB details
                logs[-1] = trade_data
                with open(log_file, 'w') as f:
                    json.dump(logs, f, indent=2)
                
                print(f"Trade(s) placed with IB - Order type: {trade_data.get('order_type', 'MKT')}")
                
            except Exception as e:
                print(f"Error placing trade with IB: {e}")
                trade_data['ib_error'] = str(e)
                
                # Update log with error
                logs[-1] = trade_data
                with open(log_file, 'w') as f:
                    json.dump(logs, f, indent=2)
            
    except Exception as e:
        print(f"Error in trade logging: {e}")

# Cleanup function to properly disconnect from IB
def cleanup():
    """
    Cleanup function to properly disconnect from IB.
    Should be called when the application shuts down.
    """
    if ib.isConnected():
        ib.disconnect() 