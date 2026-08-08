from .auth import register , AccountLoginView
from .dashboard import dashboard
from .follow import user_follow
from .profile import edit
from .users import user_detail, user_list


__all__ = [
    "dashboard",
    "edit",
    "register",
    "user_detail",
    "user_follow",
    "user_list",
    "AccountLoginView",
]

