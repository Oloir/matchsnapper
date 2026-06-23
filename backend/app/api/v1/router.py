from fastapi import APIRouter

from app.api.v1 import auth

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Phases 3–5:
# from app.api.v1 import users, tags, snapshots, matching, interactions
# router.include_router(users.router, prefix="/users", tags=["users"])
# router.include_router(tags.router, prefix="/tags", tags=["tags"])
# router.include_router(snapshots.router, prefix="/snapshots", tags=["snapshots"])
# router.include_router(matching.router, prefix="/matching", tags=["matching"])
# router.include_router(interactions.router, prefix="/users", tags=["interactions"])
