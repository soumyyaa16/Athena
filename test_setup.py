import os
from dotenv import load_dotenv
import requests

load_dotenv()

print("Testing environment setup...\n")

# Test 1: Check keys loaded
news_key = os.getenv("NEWS_API_KEY")
fmp_key = os.getenv("FMP_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

print(f"NewsAPI key loaded: {bool(news_key)}")
print(f"FMP key loaded: {bool(fmp_key)}")
print(f"Gemini key loaded: {bool(gemini_key)}\n")

# Test 2: yfinance works
import yfinance as yf
ticker = yf.Ticker("AAPL")
info = ticker.info
print(f"yfinance test: {info.get('longName', 'FAILED')}\n")

# Test 3: NewsAPI works
news_url = f"https://newsapi.org/v2/everything?q=Apple&apiKey={news_key}&pageSize=1"
news_resp = requests.get(news_url)
print(f"NewsAPI status: {news_resp.status_code}")
if news_resp.status_code == 200:
    print(f"NewsAPI test: {news_resp.json()['articles'][0]['title']}\n")

# Test 4: FMP works
fmp_url = f"https://financialmodelingprep.com/stable/profile?symbol=AAPL&apikey={fmp_key}"
fmp_resp = requests.get(fmp_url)
print(f"FMP key repr: {repr(fmp_key)}")
print(f"FMP status: {fmp_resp.status_code}")
if fmp_resp.status_code == 200:
    print(f"FMP test: {fmp_resp.json()[0].get('companyName', 'FAILED')}\n")

# Test 5: Gemini works
from google import genai

client = genai.Client(api_key=gemini_key)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say 'connection successful' if you receive this."
)
print(f"Gemini test: {response.text}")