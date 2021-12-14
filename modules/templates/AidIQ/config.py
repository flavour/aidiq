# -*- coding: utf-8 -*-

from collections import OrderedDict

from gluon import current, URL, TR, TD, DIV
from gluon.storage import Storage

def config(settings):
    """
        Template settings for AidIQ
    """

    T = current.T

    # Custom Models
    settings.base.custom_models = {"aidiq": "AidIQ",
                                   }

    # Custom Controllers
    settings.base.rest_controllers = {("project", "project_budget"): ("aidiq", "project_budget"),
                                      }

    # Pre-Populate
    settings.base.prepopulate += ("AidIQ",)

    # Theme
    settings.base.theme = "AidIQ"

    # Parser
    settings.msg.parser = "AidIQ"

    # Monitoring Scripts
    #settings.monitor.template = "AidIQ"

    # Security Policy
    settings.security.policy = 6 # Entity Realm

    settings.auth.login_next = URL(c="project", f="task",
                                   vars = {"mine":1},
                                   )

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

    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Uncomment this to request the Organisation when a user registers
    settings.auth.registration_requests_organisation = True
    # Uncomment this to have the Organisation selection during registration be mandatory
    settings.auth.registration_organisation_mandatory = True
    # Uncomment to set the default role UUIDs assigned to newly-registered users
    settings.auth.registration_roles = {"site_id": ["project_reader"]}

    # -------------------------------------------------------------------------
    # Uncomment to allow HR records to be deletable rather than just marking them as obsolete
    settings.hrm.deletable = True

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
        ("project", Storage(
                name_nice = T("Projects"),
                #description = "Tracking of Projects, Activities and Tasks",
                restricted = True,
                module_type = 1
            )),
        ("aidiq", Storage(
                name_nice = "AidIQ",
                #description = "Custom AidIQ models",
                restricted = True,
                module_type = 1
            )),
        ("hrm", Storage(
                name_nice = T("Staff"),
                #description = "Human Resources Management",
                restricted = True,
                module_type = 2,
            )),
        ("setup", Storage(
                name_nice = T("Monitoring"),
                #description = "Deployment & Monitoring of Servers & Applications",
                restricted = True,
                module_type = 3
            )),
        ("cms", Storage(
              name_nice = T("CMS"),
              #description = "Content Management System",
              restricted = True,
              module_type = 4,
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
        ("proc", Storage(
                name_nice = T("Procurement"),
                #description = "Purchase Orders",
                restricted = True,
                module_type = None,
            )),
        ("fin", Storage(
                name_nice = T("Finance"),
                #description = "Payment Service",
                restricted = True,
                module_type = None,
            )),
        #("dc", Storage(
        #        name_nice = T("Surveys"),
        #        #description = "Create, enter, and manage surveys.",
        #        restricted = True,
        #        module_type = 5,
        #    )),
        #("budget", Storage(
        #        name_nice = T("Budgets"),
        #        #description = "Manage budgets.",
        #        restricted = True,
        #        module_type = 5,
        #    )),
    ])

    # -------------------------------------------------------------------------
    def customise_aidiq_project_budget_resource(r, tablename):

        # Filter Milestone by Project
        current.s3db.aidiq_project_budget.milestone_id.requires.other.set_filter(filterby = "project_id",
                                                                                 filter_opts = (r.id,),
                                                                                 )

    settings.customise_aidiq_project_budget_resource = customise_aidiq_project_budget_resource

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineLink

        crud_form = S3SQLCustomForm("organisation_id",
                                    "name",
                                    "description",
                                    "status_id",
                                    "start_date",
                                    "end_date",
                                    "calendar",
                                    "human_resource_id",
                                    S3SQLInlineLink("sector",
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
    def customise_project_project_controller(**attr):

        stable = current.s3db.project_status
        statuses = current.db(stable.name.belongs(("Current",
                                                   "Proposed"))).select(stable.id,
                                                                        limitby = (0, 2)
                                                                        )
        statuses = [s.id for s in statuses]

        # Default Filter
        from s3 import s3_set_default_filter
        s3_set_default_filter("~.status_id",
                              statuses,
                              tablename = "project_project")

        return attr


    settings.customise_project_project_controller = customise_project_project_controller

    # -------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):

        from gluon import DIV

        current.s3db.project_task.comment = DIV(_class = "tooltip",
                                                _title = "%s|%s" % (T("Detailed Description/URL"),
                                                                    T("Please provide as much detail as you can, including the URL(s) where the bug occurs or you'd like the new feature to go."),
                                                                    ),
                                                )


    settings.customise_project_task_resource = customise_project_task_resource

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
            r.resource.configure(list_fields = list_fields)

            return result
        s3.prep = custom_prep

        return attr

    #settings.customise_project_task_controller = customise_project_task_controller

    # -------------------------------------------------------------------------
    def customise_project_activity_resource(r, tablename):

        from s3 import S3OptionsFilter
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
                                 defaults = Storage(rows = "activity.project_id",
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
    def create_instance(subscription_id):
        """
            Create a new instance for a new subscription
        """

        db = current.db
        s3db = current.s3db

        # Lookup the Order
        ttable = s3db.proc_order_tag
        query = (ttable.tag == "subscription_id") & \
                (ttable.value == subscription_id)
        tag = db(query).select(ttable.order_id,
                               limitby = (0, 1)
                               ).first()
        order_id = tag.order_id

        # Check if we already have an instance for this subscription
        query = (ttable.order_id == order_id) & \
                (ttable.tag == "deployment_id")
        tag = db(query).select(ttable.value,
                               limitby = (0, 1)
                               ).first()
        if tag:
            #deployment_id = tag.value
            # We already have an instance: Take no action
            return

        # Deploy New Instance

        # Lookup the Deployment Details
        # Initial case is no choice of location, so we do US West (cheapest & where our Monitor/SMTP are)
        ctable = s3db.setup_cloud
        cloud = db(ctable.name == "AWS AidIQ").select(ctable.cloud_id,
                                                      limitby = (0, 1)
                                                      ).first()
        cloud_id = cloud.cloud_id
        # Initial case is no custom URL, so we create as https://cloudxxxx.aidiq.com
        dtable = s3db.setup_dns
        dns = db(dtable.name == "aidiq.com").select(dtable.dns_id,
                                                    limitby = (0, 1)
                                                    ).first()
        dns_id = dns.dns_id
        # SMTP using AWS SES (@ToDo: Allow them to use their own Sendgrid - e.g. from a Control Panel we provide in their profile)
        stable = s3db.setup_smtp
        smtp = db(stable.name == "AidIQ SES").select(stable.id,
                                                     limitby = (0, 1)
                                                     ).first()
        smtp_id = smtp.id

        # Create Deployment
        # eden-stable (default anyway)
        # Default template (@ToDo: Allow them to switch Template - e.g. from a Control Panel we provide in their profile)
        deployment_id = s3db.setup_deployment.insert(cloud_id = cloud_id,
                                                     dns_id = dns_id,
                                                     smtp_id = smtp_id,
                                                     )
        # Link instance to Order
        ttable.insert(order_id = order_id,
                      tag = "deployment_id",
                      value = deployment_id,
                      )

        server_id = s3db.setup_server.insert(deployment_id = deployment_id,
                                             host_ip = "127.0.0.1",
                                             )
        s3db.setup_aws_server.insert(server_id = server_id)
        s3db.setup_monitor_server.insert(server_id = server_id)
        #task_id = current.s3task.run_async("dummy")
        instance_id = s3db.setup_instance.insert(deployment_id = deployment_id,
                                                 url = public_url,
                                                 sender = current.auth.user.email,
                                                 #task_id = task_id,
                                                 )
        # Deploy
        s3db.setup_instance_deploy(deployment_id, instance_id, current.request.folder)

        # Email User that their instance is ready for them at https://cloudxxxx.aidiq.com
        # @ToDo

    # -------------------------------------------------------------------------
    def delete_instance(subscription_id):
        """
            Delete an instance for a cancelled subscription
        """

        # @ToDo
        pass

    # -------------------------------------------------------------------------
    def fin_subscription_onaccept(form):
        """
            After an Order has been approved or cancelled then take the appropriate action
        """

        # Read the status of the subscription
        subscription_id = form.vars.get("id")
        stable = current.s3db.fin_subscription
        subscription = current.db(stable.id == subscription_id).select(stable.status,
                                                                       limitby = (0, 1)
                                                                       ).first()
        status = subscription.status
        if status == "ACTIVE":
            # Create an instance
            create_instance(subscription_id)
        elif status in ("CANCELLED", "EXPIRED", "SUSPENDED"):
            # Delete the instance
            delete_instance(subscription_id)
        else:
            # Take no action
            pass

    # -------------------------------------------------------------------------
    def customise_fin_subscription_resource(r, tablename):
        """
            Call custom Onaccept for fulfilment/cancellation
        """

        current.s3db.configure(tablename,
                               onaccept = fin_subscription_onaccept,
                               )


    settings.customise_fin_subscription_resource = customise_fin_subscription_resource

    # -------------------------------------------------------------------------
    def proc_order_create_onaccept(form):
        """
            After an Order has been created then redirect to PayPal to Register the Subscription
        """

        db = current.db
        s3db = current.s3db

        # Lookup Plan
        # @ToDo: Better link between Order & Plan (DRY, FKs)
        ptable = s3db.fin_subscription_plan
        post_vars_get = current.request.post_vars.get
        term = post_vars_get("sub_term_value")
        if term is None:
            # Service
            hours = post_vars_get("sub_hours_value")
            if hours == "10":
                plan = "Support 10"
            elif hours == "40":
                plan = "Support 40"
            else:
                plan = "Support 80"
            plan = db(ptable.name == plan).select(ptable.id,
                                                  limitby = (0, 1)
                                                  ).first()
        else:
            # Instance
            if term == "YR":
                interval_count = 12
            else:
                # term == "MO"
                interval_count = 1

            plan = db(ptable.interval_count == interval_count).select(ptable.id,
                                                                      limitby = (0, 1)
                                                                      ).first()

        plan_id = plan.id

        # Assume only a single Payment Service defined
        stable = s3db.fin_payment_service
        service = db(stable.deleted == False).select(stable.id,
                                                     limitby = (0, 1)
                                                     ).first()
        service_id = service.id

        # Lookup current User
        auth = current.auth
        pe_id = auth.s3_user_pe_id(auth.user.id)

        # Register with PayPal
        from s3.s3payments import S3PaymentService
        try:
            adapter = S3PaymentService.adapter(service_id)
        except (KeyError, ValueError) as e:
            current.response.error = "Service registration failed: %s" % e
        else:
            subscription_id = adapter.register_subscription(plan_id, pe_id)
            if subscription_id:
                # Link PO to Subscription
                ttable = s3db.proc_order_tag
                ttable.insert(order_id = form.vars.id,
                              tag = "subscription_id",
                              value = subscription_id,
                              )
                # Go to PayPal to confirm payment
                stable = s3db.fin_subscription
                subscription = db(stable.id == subscription_id).select(stable.approval_url,
                                                                       limitby = (0, 1)
                                                                       ).first()
                from gluon import redirect
                redirect(subscription.approval_url)
            else:
                # @ToDo: Read Details from the Log
                current.response.error = "Subscription registration failed"

    # -------------------------------------------------------------------------
    def customise_proc_order_resource(r, tablename):
        """
            @ToDo:
                Explanatory Text
                Javascript to total price client-side (pass details to JS from controller rather than hardcoding in the JS)
                onaccept to total price server-side (avoid hacking)
                Redirect to the Payments page (PayPal currently)
                Later:
                    Instance Size
                    Instance Location
                    Order in different Currencies
        """

        from gluon import IS_IN_SET
        from s3 import S3SQLCustomForm, S3Represent

        s3db = current.s3db

        # Filtered components
        s3db.add_components(tablename,
                            proc_order_tag = ({"name": "term",
                                               "joinby": "order_id",
                                               "filterby": {"tag": "term"},
                                               "multiple": False,
                                               },
                                              {"name": "hours",
                                               "joinby": "order_id",
                                               "filterby": {"tag": "hours"},
                                               "multiple": False,
                                               },
                                              {"name": "hours_free",
                                               "joinby": "order_id",
                                               "filterby": {"tag": "hours_free"},
                                               "multiple": False,
                                               },
                                              ),
                            )

        # Individual settings for specific tag components
        components_get = s3db.resource(tablename).components.get

        get_vars_get = r.get_vars.get

        service_only = get_vars_get("service")

        if service_only:
            hours_default = 10
            hours_options = {10: "10 Hours. USD 750",
                             40: "40 Hours. USD 2880",
                             80: "80 Hours. USD 5600",
                             }

        else:
            term_options = {"MO": T("Monthly. USD 50"),
                            "YR": T("Annual. USD 500"),
                            }

            term_default = get_vars_get("term", "YR")

            term = components_get("term")
            f = term.table.value
            f.default = term_default
            f.represent = S3Represent(options = term_options)
            f.requires = IS_IN_SET(term_options, zero=None)

            hours_default = 0
            hours_options = {0: "0",
                             10: "10. +USD 750",   # Basic Branding, Minor Modifications
                             40: "40. +USD 2880",  # Full Branding, Multiple Modifications
                             80: "80. +USD 5600",  # Significant Customisation
                             }

        hours = components_get("hours")
        f = hours.table.value
        f.default = hours_default
        f.represent = S3Represent(options = hours_options)
        f.requires = IS_IN_SET(hours_options, zero=None)

        if service_only:
            crud_form = S3SQLCustomForm((T("Service Hours"), "hours.value"),
                                        (T("Or Enter Manually"), "hours_free.value"), # Hide by default
                                        )
        else:
            crud_form = S3SQLCustomForm((T("Term"), "term.value"),
                                        (T("Service Hours"), "hours.value"),
                                        )

        current.response.s3.crud.submit_button = "Order"

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

        # Add custom callback (& keep default)
        s3db.add_custom_callback(tablename,
                                 "create_onaccept",
                                 proc_order_create_onaccept,
                                 )


    settings.customise_proc_order_resource = customise_proc_order_resource

# END =========================================================================

