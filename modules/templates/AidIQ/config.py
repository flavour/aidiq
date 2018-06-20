# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current, URL, TR, TD, DIV
from gluon.storage import Storage

def config(settings):
    """
        Template settings for AidIQ
    """

    T = current.T

    # Pre-Populate
    settings.base.prepopulate = ("AidIQ",)

    # Theme
    settings.base.theme = "AidIQ"

    # Parser
    settings.msg.parser = "AidIQ"

    # Monitoring Scripts
    settings.monitor.template = "AidIQ"

    # Security Policy
    settings.security.policy = 6 # Entity Realm

    settings.auth.login_next = URL(c="project", f="task", vars={"mine":1})

    # L10n settings
    settings.L10n.languages = OrderedDict([
        ("en-gb", "English"),
    ])
    # Default Language
    settings.L10n.default_language = "en-gb"
    # Uncomment to Hide the language toolbar
    settings.L10n.display_toolbar = False
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = "."
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = ","

    # Formstyle
    #settings.ui.formstyle = "table"
    #settings.ui.filter_formstyle = "table_inline"

    # Uncomment this to request the Organisation when a user registers
    settings.auth.registration_requests_organisation = True
    # Uncomment this to have the Organisation selection during registration be mandatory
    settings.auth.registration_organisation_mandatory = True
    # Uncomment to set the default role UUIDs assigned to newly-registered users
    settings.auth.registration_roles = {"site_id": ["project_reader"]}

    # -------------------------------------------------------------------------
    # Projects
    # Uncomment this to use settings suitable for detailed Task management
    settings.project.mode_task = True
    # Uncomment this to use Activities for projects
    settings.project.activities = True
    # Uncomment this to use Milestones in project/task.
    settings.project.milestones = True
    # Uncomment this to use Projects in Activities & Tasks
    settings.project.projects = True
    # Uncomment this to disable Sectors in projects
    #settings.project.sectors = False
    # Change the label for Organisation from 'Lead Implementer'
    settings.project.organisation_roles = {
        1: T("Customer")
    }

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        from s3.s3forms import S3SQLCustomForm, S3SQLInlineLink
        crud_form = S3SQLCustomForm("organisation_id",
                                    "name",
                                    "description",
                                    "status_id",
                                    "start_date",
                                    "end_date",
                                    "calendar",
                                    "human_resource_id",
                                    S3SQLInlineLink(
                                        "sector",
                                        label = T("Sectors"),
                                        field = "sector_id",
                                        cols = 3,
                                        ),
                                    "budget",
                                    "currency",
                                    "comments",
                                    )
        current.s3db.configure(tablename,
                               crud_form = crud_form,
                               )


    settings.customise_project_project_resource = customise_project_project_resource

    # -------------------------------------------------------------------------
    def customise_project_task_controller(**attr):

        s3 = current.response.s3

        standard_prep = s3.prep
        def custom_prep(r):

            result = standard_prep(r) if callable(standard_prep) else True

            mine = "mine" in r.get_vars
            list_fields = ["id",
                           (T("ID"), "task_id"),
                           "priority",
                           "task_project.project_id",
                           "name",
                           #"task_activity.activity_id",
                           #"task_milestone.milestone_id",
                           ]
            if not mine:
                # Assigned-to field: only needed if not "mine"
                list_fields.append("pe_id")

            list_fields.extend(("date_due",
                                "time_estimated",
                                "time_actual",
                                "created_on",
                                ))
            if not mine:
                list_fields.append("status")
            r.resource.configure(list_fields=list_fields)

            return result
        s3.prep = custom_prep

        return attr

    #settings.customise_project_task_controller = customise_project_task_controller

    # -------------------------------------------------------------------------
    def customise_project_activity_resource(r, tablename):

        from s3.s3filter import S3OptionsFilter
        filter_widgets = [S3OptionsFilter("activity_activity_type.activity_type_id",
                                          label = T("Type"),
                                          ),
                          S3OptionsFilter("project_id",
                                          represent = "%(name)s",
                                          ),
                          ]

        report_fields = [(T("Project"), "project_id"),
                         (T("Activity"), "name"),
                         (T("Activity Type"), "activity_type.name"),
                         (T("Sector"), "project_id$sector.name"),
                         (T("Time Estimated"), "time_estimated"),
                         (T("Time Actual"), "time_actual"),
                         ]

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = report_fields,
                                 defaults=Storage(rows = "activity.project_id",
                                                  cols = "activity.name",
                                                  fact = "sum(activity.time_actual)",
                                                  totals = True,
                                                  )
                                 )

        current.s3db.configure(tablename,
                               filter_widgets = filter_widgets,
                               report_options = report_options,
                               )


    settings.customise_project_activity_resource = customise_project_activity_resource

    # -------------------------------------------------------------------------
    # Uncomment to allow HR records to be deletable rather than just marking them as obsolete
    settings.hrm.deletable = True

    # Comment/uncomment modules here to disable/enable them
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
                name_nice = T("Home"),
                restricted = False, # Use ACLs to control access to this module
                access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
                module_type = None  # This item is not shown in the menu
            )),
        ("admin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                module_type = None  # This item is handled separately for the menu
            )),
        ("appadmin", Storage(
                name_nice = T("Administration"),
                #description = "Site Administration",
                restricted = True,
                module_type = None  # No Menu
            )),
        ("errors", Storage(
                name_nice = T("Ticket Viewer"),
                #description = "Needed for Breadcrumbs",
                restricted = False,
                module_type = None  # No Menu
            )),
        ("sync", Storage(
                name_nice = T("Synchronization"),
                #description = "Synchronization",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
                module_type = None  # This item is handled separately for the menu
            )),
        ("gis", Storage(
                name_nice = T("Map"),
                #description = "Situation Awareness & Geospatial Analysis",
                restricted = True,
                module_type = None,     # 6th item in the menu
            )),
        ("pr", Storage(
                name_nice = T("Person Registry"),
                #description = "Central point to record details on People",
                restricted = True,
                access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
                module_type = None
            )),
        ("org", Storage(
                name_nice = T("Organizations"),
                #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
                restricted = True,
                module_type = None
            )),
        # All modules below here should be possible to disable safely
        ("hrm", Storage(
                name_nice = T("Staff"),
                #description = "Human Resources Management",
                restricted = True,
                module_type = 2,
            )),
        ("cms", Storage(
              name_nice = T("Content Management"),
              #description = "Content Management System",
              restricted = True,
              module_type = None,
          )),
        ("doc", Storage(
                name_nice = T("Documents"),
                #description = "A library of digital resources, such as photos, documents and reports",
                restricted = True,
                module_type = None,
            )),
        ("msg", Storage(
                name_nice = T("Messaging"),
                #description = "Sends & Receives Alerts via Email & SMS",
                restricted = True,
                # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
                module_type = None,
            )),
        ("project", Storage(
                name_nice = T("Projects"),
                #description = "Tracking of Projects, Activities and Tasks",
                restricted = True,
                module_type = 1
            )),
        ("monitor", Storage(
                name_nice = T("Monitor"),
                #description = "Monitoring of Servers & Applications",
                restricted = True,
                module_type = 3
            )),
        #("survey", Storage(
        #        name_nice = T("Surveys"),
        #        #description = "Create, enter, and manage surveys.",
        #        restricted = True,
        #        module_type = 5,
        #    )),
    ])

# END =========================================================================

