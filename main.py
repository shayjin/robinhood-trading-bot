import robin_stocks.robinhood as robinhood
import pyotp
from datetime import datetime, timedelta
import yaml
import requests

with open('config.yaml', encoding='UTF-8') as f:
    data = yaml.load(f, Loader=yaml.FullLoader)

KEY = data['API_KEY']
EMAIL = data["EMAIL"]
PWD = data["PASSWORD"]
CODE = data["CODE"]
DISCORD_WEBHOOK_URL = data["DISCORD_WEBHOOK_URL"]
BUY_AMOUNT = 0.5

login = robinhood.login(EMAIL, PWD, mfa_code=CODE)
topt = pyotp.TOTP(KEY).now()

companies = ["PLTR", "DELL", "GOOGL", "AMZN", "EXPE"]
company_list = {}
done = []
company_target = {}

now = datetime.now()
yesterday = now - timedelta(days=1)
today_date = now.strftime('%Y-%m-%d')
yesterday_date = yesterday.strftime('%Y-%m-%d')

def send_message(msg):
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)

def buy(company, amount):
    robinhood.order_buy_market(company, amount)
    send_message("[Bought " + str(amount) + " " + company + " stocks]")

def sell(company, amount):
    robinhood.order_sell_market(company, amount)
    send_message("[Sold " + str(amount) + " " + company + " stocks]")
    done.append(company)

for company in companies:
    company_list[company] = 0
    historical_data = robinhood.stocks.get_stock_historicals(company, interval='day', span='week', bounds='regular')
    yesterday_data = next(data for data in historical_data if data['begins_at'].startswith(yesterday_date))

    yesterday_high = float(yesterday_data["high_price"])
    yesterday_low = float(yesterday_data["low_price"])

    #today_data = next(data for data in historical_data if data['begins_at'].startswith(today_date))
    start_price = float(yesterday_data["close_price"])

    target_price = start_price + (yesterday_high - yesterday_low) * 0.5
    company_target[company] = target_price

while True:
    current_hour = now.hour
    current_minute = now.minute

    if (current_hour == 9 and current_minute >= 30) or (current_hour >= 10 and current_hour < 16):
        for company, bought_price in company_list.items():
            current_price = float(robinhood.stocks.get_latest_price(company)[0])
            target_price = company_target[company]

            if current_price >= target_price and bought_price == 0:
               # buy(company, BUY_AMOUNT)
                company_list[company] = current_price
            
            if bought_price > 0 and (current_price - bought_price) >= bought_price * 0.3:
                sold_amount = robinhood.build_holdings()[company]['quantity']
                #sell(company, sold_amount)
        
        for d in done:
            if d in company_list:
                company_list.pop(d)
