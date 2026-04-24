from features.price_validator import get_market_price, scrape_jiomart, scrape_bigbasket

print("BigBasket:", scrape_bigbasket("toned milk 500ml"))
print("JioMart:", scrape_jiomart("toned milk 500ml"))
print("Market Price Validator:", get_market_price("toned milk 500ml", "Dairy"))
