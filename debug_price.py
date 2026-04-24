import traceback
from app import create_app
from features.price_validator import validate_single

app = create_app()
app.app_context().push()

try:
    res = validate_single('Toned Milk 500ml', 'Dairy', 32)
    with open('debug_error.txt', 'w', encoding='utf-8') as f:
        f.write("SUCCESS\n" + str(res))
except Exception as e:
    with open('debug_error.txt', 'w', encoding='utf-8') as f:
        f.write("ERROR:\n" + traceback.format_exc())
