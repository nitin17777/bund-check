import sys
sys.path.insert(0, r'D:\bund-check\backend')
from backend.app.main import app
for route in app.routes:
    print(f'Route: {route.path}' if hasattr(route, 'path') else f'Route (no path)')