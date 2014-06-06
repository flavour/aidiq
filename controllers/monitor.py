# -*- coding: utf-8 -*-

"""
    Monitoring Controllers
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    # Redirect to the latest results
    redirect(URL(f="run"))

# -----------------------------------------------------------------------------
def host():

    def prep(r):
        if r.interactive:

            s3.crud_strings[r.tablename] = Storage(
                label_create = T("Create Host"),
                title_display = T("Host Details"),
                title_list =  T("Hosts"),
                title_update = T("Edit Host"),
                #title_upload = T("Import Hosts"),
                label_list_button =  T("List Hosts"),
                label_delete_button = T("Delete Host"),
                msg_record_created = T("Host added"),
                msg_record_modified = T("Host updated"),
                msg_record_deleted = T("Host deleted"),
                msg_list_empty = T("No Hosts currently registered"))

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [dict(label=str(T("Enable")),
                                _class="action-btn",
                                url=URL(args=["[id]", "enable"]),
                                restrict = restrict_e),
                           dict(label=str(T("Disable")),
                                _class="action-btn",
                                url = URL(args = ["[id]", "disable"]),
                                restrict = restrict_d),
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [dict(label=str(T("Check")),
                                    _class="action-btn",
                                    url = URL(args = ["[id]", "check"]),
                                    restrict = restrict_d)
                               ]
        return output
    s3.postp = postp

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def service():

    def prep(r):
        if r.interactive:

            s3.crud_strings[r.tablename] = Storage(
                label_create = T("Create Service"),
                title_display = T("Service Details"),
                title_list =  T("Services"),
                title_update = T("Edit Service"),
                #title_upload = T("Import Services"),
                label_list_button =  T("List Services"),
                label_delete_button = T("Delete Service"),
                msg_record_created = T("Service added"),
                msg_record_modified = T("Service updated"),
                msg_record_deleted = T("Service deleted"),
                msg_list_empty = T("No Services currently registered"))

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def check():

    def prep(r):
        if r.interactive:

            s3.crud_strings[r.tablename] = Storage(
                label_create = T("Create Check"),
                title_display = T("Check Details"),
                title_list =  T("Checks"),
                title_update = T("Edit Check"),
                title_upload = T("Import Checks"),
                label_list_button =  T("List Checks"),
                label_delete_button = T("Delete Check"),
                msg_record_created = T("Check added"),
                msg_record_modified = T("Check updated"),
                msg_record_deleted = T("Check deleted"),
                msg_list_empty = T("No Checks currently registered"))

            import inspect
            import sys

            template = settings.get_monitor_template()
            module_name = "applications.%s.private.templates.%s.monitor" % \
                (appname, template)
            __import__(module_name)
            mymodule = sys.modules[module_name]
            S3Monitor = mymodule.S3Monitor()

            # Dynamic lookup of the parsing functions in S3Parser class.
            functions = inspect.getmembers(S3Monitor, \
                                           predicate=inspect.isfunction)
            function_opts = []
            append = function_opts.append
            for f in functions:
                f = f[0]
                # Filter out helper functions
                if not f.startswith("_"):
                    append(f)

            r.table.function_name.requires = IS_IN_SET(function_opts,
                                                       zero = None)
        return True
    s3.prep = prep

    return s3_rest_controller(rheader=monitor_rheader)

# -----------------------------------------------------------------------------
def task():

    def prep(r):
        if r.interactive:

            s3.crud_strings[r.tablename] = Storage(
                label_create = T("Create Task"),
                title_display = T("Task Details"),
                title_list =  T("Tasks"),
                title_update = T("Edit Task"),
                title_upload = T("Import Tasks"),
                label_list_button =  T("List Tasks"),
                label_delete_button = T("Delete Task"),
                msg_record_created = T("Task added"),
                msg_record_modified = T("Task updated"),
                msg_record_deleted = T("Task deleted"),
                msg_list_empty = T("No Tasks currently registered"))

        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive:
            # Normal Action Buttons
            s3_action_buttons(r)
            # Custom Action Buttons for Enable/Disable
            table = r.table
            query = (table.deleted == False)
            rows = db(query).select(table.id,
                                    table.enabled,
                                    )
            restrict_e = [str(row.id) for row in rows if not row.enabled]
            restrict_d = [str(row.id) for row in rows if row.enabled]

            s3.actions += [dict(label=str(T("Enable")),
                                _class="action-btn",
                                url=URL(args=["[id]", "enable"]),
                                restrict = restrict_e),
                           dict(label=str(T("Disable")),
                                _class="action-btn",
                                url = URL(args = ["[id]", "disable"]),
                                restrict = restrict_d),
                           ]
            if not s3task._is_alive():
                # No Scheduler Running
                s3.actions += [dict(label=str(T("Check")),
                                    _class="action-btn",
                                    url = URL(args = ["[id]", "check"]),
                                    restrict = restrict_d)
                               ]
        return output
    s3.postp = postp

    return s3_rest_controller(rheader=monitor_rheader)

# -----------------------------------------------------------------------------
def run():

    def prep(r):
        if r.interactive:

            s3.crud_strings[r.tablename] = Storage(
                #label_create = T("Create Log Entry"),
                title_display = T("Log Entry Details"),
                title_list =  T("Log Entries"),
                title_update = T("Edit Log Entry"),
                #title_upload = T("Import Log Entries"),
                label_list_button =  T("List Log Entries"),
                label_delete_button = T("Delete Log Entry"),
                #msg_record_created = T("Log Entry added"),
                msg_record_modified = T("Log Entry updated"),
                msg_record_deleted = T("Log Entry deleted"),
                msg_list_empty = T("No Log Entries currently registered"))

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def alert():

    def prep(r):
        if r.interactive:

            s3.crud_strings[r.tablename] = Storage(
                label_create = T("Create Alert"),
                title_display = T("Alert Details"),
                title_list =  T("Alerts"),
                title_update = T("Edit Alert"),
                title_upload = T("Import Alerts"),
                label_list_button =  T("List Alerts"),
                label_delete_button = T("Delete Alert"),
                msg_record_created = T("Alert added"),
                msg_record_modified = T("Alert updated"),
                msg_record_deleted = T("Alert deleted"),
                msg_list_empty = T("No Alerts currently registered"))

        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def monitor_rheader(r):
    
    rheader = None

    if r.representation == "html":

        if r.name == "check":
            tabs = [(T("Check Details"), None),
                    (T("Options"), "option"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            record = r.record
            if record:
                table = r.table
                rheader = DIV(TABLE(TR(TH("%s: " % table.service_id.label),
                                       table.service_id.represent(record.service_id)),
                                    TR(TH("%s: " % table.name.label),
                                       record.name),
                                    TR(TH("%s: " % table.function_name.label),
                                       record.function_name),
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments or ""),
                                    ), rheader_tabs)

        if r.name == "task":
            tabs = [(T("Task Details"), None),
                    (T("Options"), "option"),
                    (T("Logs"), "run"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            record = r.record
            if record:
                table = r.table
                rheader = DIV(TABLE(TR(TH("%s: " % table.host_id.label),
                                       table.host_id.represent(record.host_id)),
                                    TR(TH("%s: " % table.check_id.label),
                                       table.check_id.represent(record.check_id)),
                                    TR(TH("%s: " % table.status.label),
                                       table.status.represent(record.status)),
                                    TR(TH("%s: " % table.enabled.label),
                                       record.enabled),
                                    TR(TH("%s: " % table.comments.label),
                                       record.comments or ""),
                                    ), rheader_tabs)

    return rheader

# END =========================================================================
