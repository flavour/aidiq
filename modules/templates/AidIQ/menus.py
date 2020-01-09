# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """
        Custom Application Main Menu:
    """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):
        """ Compose Menu """

        main_menu = MM()(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_auth(right=True),
            cls.menu_admin(right=True),
        )
        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Custom Auth Menu """

        auth = current.auth

        if not auth.is_logged_in():
            request = current.request
            login_next = URL(args=request.args, vars=request.vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            menu_auth = MM("Login", c="default", f="user", m="login",
                           _id="auth_menu_login",
                           vars=dict(_next=login_next), **attr)
        else:
            # Logged-in
            menu_auth = [
                        MM("Logout", c="default", f="user", args="logout",
                           _id="auth_menu_logout", **attr),
                        MM(auth.user.email, c="default", f="user", args="profile",
                           translate=False, _id="auth_menu_email", **attr),
                        ]

        return menu_auth

    # -------------------------------------------------------------------------
    @classmethod
    def menu_admin(cls, **attr):
        """ Administrator Menu """

        ADMIN = current.session.s3.system_roles.ADMIN
        name_nice = current.deployment_settings.modules["admin"].name_nice

        menu_admin = MM(name_nice, c="admin",
                        restrict=[ADMIN], **attr)

        return menu_admin

# END =========================================================================
