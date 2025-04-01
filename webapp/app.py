import requests, time, os, random
from flask import Flask, render_template, request, redirect
from graph_loader import load_graph_data
from broker_data import get_total_exposure_by_asset, get_drawdown
from dotenv import load_dotenv
from pair_context import get_pair_context

# Load environment variables
load_dotenv()

# disable warnings until you install a certificate
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Get configuration from environment variables
ACCOUNT_ID = os.getenv('IBKR_ACCOUNT_ID', 'DU123456')  # Default value as fallback
GATEWAY_PORT = os.getenv('GATEWAY_PORT', '5055')  # IB Gateway port
FLASK_PORT = os.getenv('FLASK_PORT', '5056')  # Flask server port

BASE_API_URL = f"https://localhost:{GATEWAY_PORT}/v1/api"

os.environ['PYTHONHTTPSVERIFY'] = '0'

app = Flask(__name__)

@app.template_filter('ctime')
def timectime(s):
    return time.ctime(s/1000)


@app.route("/")
def dashboard():
    try:
        r = requests.get(f"{BASE_API_URL}/portfolio/accounts", verify=False)
        accounts = r.json()
    except Exception as e:
        return 'Make sure you authenticate first then visit this page. <a href="https://localhost:5055">Log in</a>'

    account = accounts[0]

    account_id = accounts[0]["id"]
    r = requests.get(f"{BASE_API_URL}/portfolio/{account_id}/summary", verify=False)
    summary = r.json()
    
    return render_template("dashboard.html", account=account, summary=summary)


@app.route("/lookup")
def lookup():
    symbol = request.args.get('symbol', None)
    stocks = []

    if symbol is not None:
        r = requests.get(f"{BASE_API_URL}/iserver/secdef/search?symbol={symbol}&name=true", verify=False)

        response = r.json()
        stocks = response

    return render_template("lookup.html", stocks=stocks)


@app.route("/contract/<contract_id>/<period>")
def contract(contract_id, period='5d', bar='1d'):
    data = {
        "conids": [
            contract_id
        ]
    }
    
    r = requests.post(f"{BASE_API_URL}/trsrv/secdef", data=data, verify=False)
    contract = r.json()['secdef'][0]

    r = requests.get(f"{BASE_API_URL}/iserver/marketdata/history?conid={contract_id}&period={period}&bar={bar}", verify=False)
    price_history = r.json()

    return render_template("contract.html", price_history=price_history, contract=contract)


@app.route("/orders")
def orders():
    try:
        r = requests.get(f"{BASE_API_URL}/iserver/account/orders", verify=False)
        
        # If there are no orders, IB Gateway returns an empty response
        if not r.content:
            return render_template("orders.html", orders=[])
            
        # If we have content, try to parse it
        try:
            data = r.json()
            # IB Gateway might return an empty array for no orders
            if isinstance(data, list):
                return render_template("orders.html", orders=data)
            # Or it might return an object with orders key
            return render_template("orders.html", orders=data.get("orders", []))
        except:
            # If JSON parsing fails, assume no orders
            return render_template("orders.html", orders=[])
    except Exception as e:
        print(f"Error fetching orders: {str(e)}")
        return render_template("orders.html", orders=[], error="Failed to fetch orders. Please ensure you are logged in to IB Gateway")


@app.route("/order", methods=['POST'])
def place_order():
    print("== placing order ==")

    data = {
        "orders": [
            {
                "conid": int(request.form.get('contract_id')),
                "orderType": "LMT",
                "price": float(request.form.get('price')),
                "quantity": int(request.form.get('quantity')),
                "side": request.form.get('side'),
                "tif": "GTC"
            }
        ]
    }

    r = requests.post(f"{BASE_API_URL}/iserver/account/{ACCOUNT_ID}/orders", json=data, verify=False)

    return redirect("/orders")

@app.route("/orders/<order_id>/cancel")
def cancel_order(order_id):
    cancel_url = f"{BASE_API_URL}/iserver/account/{ACCOUNT_ID}/order/{order_id}" 
    r = requests.delete(cancel_url, verify=False)

    return r.json()


@app.route("/portfolio")
def portfolio():
    r = requests.get(f"{BASE_API_URL}/portfolio/{ACCOUNT_ID}/positions/0", verify=False)

    if r.content:
        positions = r.json()
    else:
        positions = []

    # return my positions, how much cash i have in this account
    return render_template("portfolio.html", positions=positions)

@app.route("/watchlists")
def watchlists():
    r = requests.get(f"{BASE_API_URL}/iserver/watchlists", verify=False)

    watchlist_data = r.json()["data"]
    watchlists = []
    if "user_lists" in watchlist_data:
        watchlists = watchlist_data["user_lists"]
        
    return render_template("watchlists.html", watchlists=watchlists)


@app.route("/watchlists/<int:id>")
def watchlist_detail(id):
    r = requests.get(f"{BASE_API_URL}/iserver/watchlist?id={id}", verify=False)

    watchlist = r.json()

    return render_template("watchlist.html", watchlist=watchlist)


@app.route("/watchlists/<int:id>/delete")
def watchlist_delete(id):
    r = requests.delete(f"{BASE_API_URL}/iserver/watchlist?id={id}", verify=False)

    return redirect("/watchlists")

@app.route("/watchlists/create", methods=['POST'])
def create_watchlist():
    data = request.get_json()
    name = data['name']

    rows = []
    symbols = data['symbols'].split(",")
    for symbol in symbols:
        symbol = symbol.strip()
        if symbol:
            r = requests.get(f"{BASE_API_URL}/iserver/secdef/search?symbol={symbol}&name=true&secType=STK", verify=False)
            contract_id = r.json()[0]['conid']
            rows.append({"C": contract_id})

    data = {
        "id": int(time.time()),
        "name": name,
        "rows": rows
    }

    r = requests.post(f"{BASE_API_URL}/iserver/watchlist", json=data, verify=False)
    
    return redirect("/watchlists")

@app.route("/scanner")
def scanner():
    try:
        r = requests.get(f"{BASE_API_URL}/iserver/scanner/params", verify=False)
        params = r.json()
        
        if 'error' in params:
            return render_template("scanner.html", 
                                error="Scanner not available. Please ensure you are connected to TWS or IB Gateway.",
                                params={}, 
                                scanner_map={}, 
                                filter_map={}, 
                                scan_results=[])

        scanner_map = {}
        filter_map = {}

        # Only process these if they exist in the response
        if 'instrument_list' in params:
            for item in params['instrument_list']:
                scanner_map[item['type']] = {
                    "display_name": item['display_name'],
                    "filters": item['filters'],
                    "sorts": []
                }

        if 'filter_list' in params:
            for item in params['filter_list']:
                filter_map[item['group']] = {
                    "display_name": item['display_name'],
                    "type": item['type'],
                    "code": item['code']
                }

        if 'scan_type_list' in params:
            for item in params['scan_type_list']:
                for instrument in item['instruments']:
                    if instrument in scanner_map:
                        scanner_map[instrument]['sorts'].append({
                            "name": item['display_name'],
                            "code": item['code']
                        })

        if 'location_tree' in params:
            for item in params['location_tree']:
                if item['type'] in scanner_map:
                    scanner_map[item['type']]['locations'] = item['locations']

        submitted = request.args.get("submitted", "")
        selected_instrument = request.args.get("instrument", "")
        location = request.args.get("location", "")
        sort = request.args.get("sort", "")
        scan_results = []
        filter_code = request.args.get("filter", "")
        filter_value = request.args.get("filter_value", "")

        if submitted:
            data = {
                "instrument": selected_instrument,
                "location": location,
                "type": sort,
                "filter": [
                    {
                        "code": filter_code,
                        "value": filter_value
                    }
                ]
            }
                
            r = requests.post(f"{BASE_API_URL}/iserver/scanner/run", json=data, verify=False)
            scan_results = r.json()

        return render_template("scanner.html", params=params, scanner_map=scanner_map, filter_map=filter_map, scan_results=scan_results)
    
    except Exception as e:
        return render_template("scanner.html", 
                            error=f"Scanner error: {str(e)}. Please ensure you are connected to TWS or IB Gateway.",
                            params={}, 
                            scanner_map={}, 
                            filter_map={}, 
                            scan_results=[])

@app.route("/graph")
def show_graph():
    graph = load_graph_data()
    return render_template("graph_view.html", graph=graph)

@app.route("/check_plan", methods=['GET', 'POST'])
def check_plan():
    result = None
    if request.method == 'POST':
        trade_idea = request.form.get('plan', '').lower()
        try:
            # Get portfolio data for context
            r = requests.get(f"{BASE_API_URL}/portfolio/{ACCOUNT_ID}/positions/0", verify=False)
            positions = r.json() if r.content else []
            
            # Initialize feedback lists
            assistant_feedback = []
            matched_rules = []
            matched_concepts = []

            # Strategy logic: feedback rules
            if "structure" not in trade_idea:
                assistant_feedback.append("⚠️ No mention of structure. Are you entering before the break?")
            if "confirmation" not in trade_idea and "bias" in trade_idea:
                assistant_feedback.append("💡 Bias mentioned — consider waiting for confirmation.")
            if "hedge" in trade_idea:
                assistant_feedback.append("✅ Hedge logic detected — check confluence or invalidation levels.")
            if "damage control" in trade_idea or "dct" in trade_idea:
                assistant_feedback.append("✅ DCT logic mentioned — ensure it aligns with portfolio risk.")

            # Add basic trading concepts
            if any(word in trade_idea for word in ["risk", "stop", "sl"]):
                matched_concepts.append({
                    "name": "Risk Management",
                    "description": "Proper position sizing and stop loss placement"
                })
            
            if any(word in trade_idea for word in ["trend", "support", "resistance", "level"]):
                matched_concepts.append({
                    "name": "Technical Analysis",
                    "description": "Using price levels and market structure"
                })

            # Add trading rules based on content
            if "risk" in trade_idea:
                matched_rules.append({
                    "rule": "Position size should not exceed 2% of portfolio value"
                })
            
            if "stop" in trade_idea or "sl" in trade_idea:
                matched_rules.append({
                    "rule": "Always set a stop loss before entering a trade"
                })

            if "target" in trade_idea or "tp" in trade_idea:
                matched_rules.append({
                    "rule": "Define take profit levels based on market structure"
                })

            result = {
                "trade_idea": trade_idea,
                "rules": matched_rules,
                "concepts": matched_concepts,
                "feedback": assistant_feedback
            }
            
        except Exception as e:
            print(f"Error checking plan: {str(e)}")
            result = {'error': str(e)}
    
    return render_template("check_plan.html", result=result)

@app.route("/log_trade", methods=["GET", "POST"])
def log_trade():
    result = None
    warnings = []

    if request.method == "POST":
        asset = request.form.get("asset")
        direction = request.form.get("direction")
        exposure = float(request.form.get("exposure"))
        drawdown = float(request.form.get("drawdown"))

        # Example risk rules
        if exposure > 2.0:
            warnings.append("⚠️ Exposure above 2.0 lots — confirm it's justified.")
        if drawdown > 3.0:
            warnings.append("🚨 Drawdown above 3% — trade may breach your risk rules.")
        if "jpy" in asset.lower() and direction.lower() == "long":
            warnings.append("💡 Check Yen sentiment — recent bias was bearish.")

        result = {
            "asset": asset,
            "direction": direction,
            "exposure": exposure,
            "drawdown": drawdown,
            "warnings": warnings
        }

    return render_template("log_trade.html", result=result)

@app.route("/risk")
def risk_monitor():
    # Load strategy and portfolio data
    graph = load_graph_data()
    exposure = get_total_exposure_by_asset()
    drawdown = get_drawdown()

    alerts = []
    flags = []

    # Check if there was an error loading graph data
    if 'error' in graph:
        alerts.append(f"⚠️ Warning: Could not load strategy data - {graph['error']}")
        return render_template("risk_monitor.html", drawdown=drawdown, exposure=exposure, alerts=alerts, flags=flags)

    for symbol, size in exposure.items():
        symbol_lower = symbol.lower()

        # Example rule: exposure threshold
        if size > 2.0:
            alerts.append(f"⚠️ High exposure on {symbol}: {size} lots")

        # Strategy match: hedge-only zone awareness
        if "concepts" in graph:  # Add check for concepts key
            for concept in graph["concepts"]:
                if "hedge-only" in concept["name"].lower() and symbol_lower in concept["description"].lower():
                    flags.append(f"🔒 {symbol} is in a hedge-only zone — review your open trade.")

        # Risk concept: drawdown sensitivity
        if drawdown > 3.0:
            flags.append(f"🚨 Portfolio drawdown at {drawdown}% — check if {symbol} position needs DCT adjustment")

    return render_template("risk_monitor.html", drawdown=drawdown, exposure=exposure, alerts=alerts, flags=flags)

@app.route("/context/<pair>")
def show_pair_context(pair):
    context = get_pair_context(pair)
    return render_template("pair_context.html", context=context)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(FLASK_PORT))
