import os
from dotenv import load_dotenv
load_dotenv()

from features.price_validator import validate_single
import json
import traceback

try:
    result = validate_single("Tomato 1kg", "Grocery", 100)
    with open("out.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
except Exception as e:
    with open("err.txt", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
