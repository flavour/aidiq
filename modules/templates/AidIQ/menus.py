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

        # Render the off-canvas menu if on default/index or default/page
        request = current.request
        if request.controller == "default" and request.function in ("index", "page"):
            current.menu.top_menu = cls.menu_top()
            current.menu.bottom_menu = cls.menu_bottom()
        else:
            current.menu.top_menu = ""
            current.menu.bottom_menu = ""

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
                           _id = "auth_menu_login",
                           vars = {"_next": login_next}, **attr)
        else:
            # Logged-in
            menu_auth = [MM("Logout", c="default", f="user",
                            args = ["logout"],
                            _id = "auth_menu_logout",
                            **attr),
                         MM(auth.user.email, c="default", f="user",
                            args = ["profile"],
                            translate = False,
                            _id = "auth_menu_email",
                            **attr),
                         ]

        return menu_auth

    # -------------------------------------------------------------------------
    @classmethod
    def menu_admin(cls, **attr):
        """ Administrator Menu """

        ADMIN = current.session.s3.system_roles.ADMIN
        name_nice = current.deployment_settings.modules["admin"].name_nice

        menu_admin = MM(name_nice, c="admin", restrict=[ADMIN], **attr)

        return menu_admin

    # -------------------------------------------------------------------------
    @classmethod
    def menu_top(cls, **attr):
        """
            Top menu on public pages (website)
        """

        return WM(c="default", f="index", link=False, _class="top-menu")(
                  #WM("Home"),
                  WM("Services", f="page", args=["services"]),
                  WM("Solutions", f= "page", args=["solutions"]),
                  WM("Team", f= "page", args=["team"]),
                  WM("Contact Us", args=["contact"], _class="contact-link"),
                  )

    # -------------------------------------------------------------------------
    @classmethod
    def menu_bottom(cls, **attr):
        """
            Bottom menu on public pages (website)
        """

        menu = WM(c="default", f="index", link=False, _class="bottom-menu")(
                  WM("AidIQ", _class="home-link"),
                  WM("Services", f="page", args=["services"]),
                  WM("Solutions", f= "page", args=["solutions"]),
                  WM("Team", f= "page", args=["team"]),
                  WM("Contact Us", args=["contact"], _class="contact-link"),
                  )

        if current.auth.s3_logged_in():
            menu(WM("CMS", c="cms", f="post"))

        return menu

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """ Custom Controller Menus """

    # -------------------------------------------------------------------------
    def admin(self):
        """ ADMIN menu """

        settings_messaging = self.settings_messaging()

        settings = current.deployment_settings
        consent_tracking = lambda i: settings.get_auth_consent_tracking()
        is_data_repository = lambda i: settings.get_sync_data_repository()
        translate = settings.has_module("translate")

        # NB: Do not specify a controller for the main menu to allow
        #     re-use of this menu by other controllers
        return M()(
                    #M("Setup", c="setup", f="deployment")(
                    #    M("AWS Clouds", f="aws_cloud")(),
                    #    M("OpenStack Clouds", f="openstack_cloud")(),
                    #    M("GANDI DNS", f="gandi_dns")(),
                    #    M("GoDaddy DNS", f="godaddy_dns")(),
                    #    M("Google Email", f="google_email")(),
                    #    M("SMTP SmartHosts", f="smtp")(),
                    #    M("Deployments", f="deployment")(
                    #        M("Create", m="create"),
                    #    ),
                    #),
                    M("Settings", c="admin", f="setting")(
                        settings_messaging,
                    ),
                    M("User Management", c="admin", f="user")(
                        M("Create User", m="create"),
                        M("List All Users"),
                        M("Import Users", m="import"),
                        M("List All Roles", f="role"),
                        M("List All Organization Approvers & Whitelists", f="organisation"),
                        #M("Roles", f="group"),
                        #M("Membership", f="membership"),
                    ),
                    #M("Consent Tracking", c="admin", link=False, check=consent_tracking)(
                    #    M("Processing Types", f="processing_type"),
                    #    M("Consent Options", f="consent_option"),
                    #    ),
                    #M("CMS", c="cms", f="post")(
                    #),
                    M("Database", c="appadmin", f="index")(
                        M("Raw Database access", c="appadmin", f="index")
                    ),
                    M("Error Tickets", c="admin", f="errors"),
                    #M("Monitoring", c="setup", f="server")(
                    #    M("Checks", f="monitor_check"),
                    #    M("Servers", f="server"),
                    #    M("Tasks", f="monitor_task"),
                    #    M("Logs", f="monitor_run"),
                    #),
                    #M("Synchronization", c="sync", f="index")(
                    #    M("Settings", f="config", args=[1], m="update"),
                    #    M("Repositories", f="repository"),
                    #    M("Public Data Sets", f="dataset", check=is_data_repository),
                    #    M("Log", f="log"),
                    #),
                    #M("Edit Application", a="admin", c="default", f="design",
                      #args=[request.application]),
                    #M("Translation", c="admin", f="translate", check=translate)(
                    #   M("Select Modules for translation", c="admin", f="translate",
                    #     m="create", vars=dict(opt="1")),
                    #   M("Upload translated files", c="admin", f="translate",
                    #     m="create", vars=dict(opt="2")),
                    #   M("View Translation Percentage", c="admin", f="translate",
                    #     m="create", vars=dict(opt="3")),
                    #   M("Add strings manually", c="admin", f="translate",
                    #     m="create", vars=dict(opt="4"))
                    #),
                    #M("View Test Result Reports", c="admin", f="result"),
                    #M("Portable App", c="admin", f="portable")
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def cms():
        """ CMS / Content Management System """

        return M(c="cms")(
                    M("Series", f="series")(
                        M("Create", m="create"),
                        M("View as Pages", f="blog"),
                    ),
                    M("Posts", f="post")(
                        M("Create", m="create"),
                        M("Import", m="import"),
                        M("View as Pages", f="page"),
                    ),
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def project():
        """ PROJECT / Project Tracking & Management """

        return M(c="project")(
                    M("Projects", f="project")(
                        M("Create", m="create"),
                        M("Open Tasks for Project", vars={"tasks":1}),
                    ),
                    M("Tasks", f="task")(
                        M("Create", m="create"),
                    ),
                    M("Daily Work", f="time")(
                        M("My Logged Hours", vars={"mine":1}),
                        M("My Open Tasks", f="task", vars={"mine":1}),
                    ),
                    M("Reports", f="report")(
                        M("Activity Report", f="activity", m="report"),
                        M("Budget Report", f="project_budget"),
                        M("Last Week's Work", f="time", m="report",
                          vars = {"rows": "person_id",
                                  "cols": "day",
                                  "fact": "sum(hours)",
                                  "week": 1,
                                  },
                          ),
                        M("Last Month's Work", f="time", m="report",
                          vars = {"rows": "person_id",
                                  "cols": "week",
                                  "fact": "sum(hours)",
                                  "month": 1,
                                  },
                          ),
                        M("Project Time Report", f="time", m="report"),
                     ),
                    )

    # -------------------------------------------------------------------------
    def setup(self):
        """ Setup """

        return M()(
                    M("Deployments", c="setup", f="deployment")(
                        M("AWS Clouds", f="aws_cloud")(),
                        M("OpenStack Clouds", f="openstack_cloud")(),
                        M("GANDI DNS", f="gandi_dns")(),
                        M("GoDaddy DNS", f="godaddy_dns")(),
                        M("Google Email", f="google_email")(),
                        M("SMTP SmartHosts", f="smtp")(),
                        M("Create", m="create")(),
                    ),
                    M("Monitoring", c="setup", f="server")(
                        M("Checks", f="monitor_check"),
                        M("Servers", f="server"),
                        M("Tasks", f="monitor_task"),
                        M("Logs", f="monitor_run"),
                    ),
                )

# END =========================================================================
