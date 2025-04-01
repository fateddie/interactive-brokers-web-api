import openai

# Replace this with real headlines from an API in future
def get_mock_headlines(pair):
    return [
        f"{pair}: ECB remains cautious as inflation softens",
        f"{pair}: US job market data stronger than expected",
        f"{pair}: Traders await Powell speech on rate outlook"
    ]

def analyze_sentiment_with_gpt(headlines):
    joined = "\n".join(headlines)
    prompt = (
        "Given the following headlines about a currency pair, "
        "is the sentiment bullish, bearish, or neutral for the quote currency?\n\n"
        f"{joined}\n\n"
        "Respond only with: 'Bullish', 'Bearish', or 'Neutral', then provide a one-line justification."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )
        content = response.choices[0].message.content.strip()
        sentiment, summary = content.split("\n", 1)
        return {
            "sentiment": sentiment.strip(),
            "summary": summary.strip(),
            "confidence": 0.85,
            "source": "Mock GPT Analysis"
        }
    except Exception as e:
        return {
            "sentiment": "Neutral",
            "summary": f"Error analyzing sentiment: {e}",
            "confidence": 0.0,
            "source": "Error"
        }

def get_live_sentiment(pair):
    headlines = get_mock_headlines(pair)
    sentiment_data = analyze_sentiment_with_gpt(headlines)
    sentiment_data["headlines"] = headlines
    sentiment_data["pair"] = pair.upper()
    return sentiment_data 