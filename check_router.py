import sys
sys.path.insert(0, r'D:\bund-check\backend')
from backend.app.api.v1.endpoints import users as users_mod
r = getattr(users_mod, 'router', None)
print('router:', r)
if r:
    print('router.path:', getattr(r, 'path', 'NO PATH'))
    print('router.routes count:', len(r.routes) if hasattr(r, 'routes') else 'N/A')
    for route in r.routes:
        print('  route.path:', getattr(route, 'path', 'NO PATH'))