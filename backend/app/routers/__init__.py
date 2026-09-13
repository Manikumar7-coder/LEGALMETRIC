from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router, settings_router
from app.routers.inspections import router as inspections_router
from app.routers.dashboard import router as dashboard_router
from app.routers.reports import router as reports_router
from app.routers.rules import router as rules_router
from app.routers.users import router as users_router

__all__ = [
    "auth_router", "profile_router", "settings_router", "inspections_router",
    "dashboard_router", "reports_router", "rules_router", "users_router"
]
