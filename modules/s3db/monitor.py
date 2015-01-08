# -*- coding: utf-8 -*-

""" Sahana Eden Monitoring Model

    @copyright: 2014-2015 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3MonitorModel",
           "monitor_run_task",
           )

import sys

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3MonitorModel(S3Model):

    names = ("monitor_host",
             "monitor_service",
             "monitor_check",
             "monitor_check_option",
             "monitor_task",
             "monitor_task_option",
             "monitor_run",
             "monitor_alert",
             )

    def model(self):

        T = current.T
        db = current.db

        add_components = self.add_components
        configure = self.configure
        define_table = self.define_table
        set_method = self.set_method

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        STATUS_OPTS = {1 : T("OK"),
                       2 : T("Warning"),
                       3 : T("Critical"),
                       }

        status_id = S3ReusableField("status", "integer", notnull=True,
                                    default = 1,
                                    label = T("Status"),
                                    represent = lambda opt: \
                                                    STATUS_OPTS.get(opt,
                                                                    UNKNOWN_OPT),
                                    requires = IS_IN_SET(STATUS_OPTS,
                                                         zero=None),
                                    )

        # =============================================================================
        # Hosts

        tablename = "monitor_host"
        define_table(tablename,
                     # @ToDo: Host Groups
                     #group_id(),
                     Field("name", unique=True, length=255,
                           label = T("Name"),
                           ),
                     status_id(),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        represent = S3Represent(lookup=tablename)
        host_id = S3ReusableField("host_id", "reference %s" % tablename,
                                  label = T("Host"),
                                  ondelete = "CASCADE",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "monitor_host.id",
                                                          represent)),
                                  )

        add_components(tablename,
                       monitor_task = "host_id",
                       )

        set_method("monitor", "host",
                   method = "enable",
                   action = self.monitor_host_enable_interactive)

        set_method("monitor", "host",
                   method = "disable",
                   action = self.monitor_host_disable_interactive)

        set_method("monitor", "host",
                   method = "check",
                   action = self.monitor_host_check)

        configure(tablename,
                  onaccept = self.monitor_host_onaccept,
                  )

        # =============================================================================
        # Services

        tablename = "monitor_service"
        define_table(tablename,
                     Field("name", unique=True, length=255,
                           label = T("Name"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        represent = S3Represent(lookup=tablename)
        service_id = S3ReusableField("service_id", "reference %s" % tablename,
                                     label = T("Service"),
                                     ondelete = "CASCADE",
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "monitor_service.id",
                                                  represent,
                                                  )),
                                     )

        add_components(tablename,
                       monitor_check = "service_id",
                       )

        # =============================================================================
        # Checks

        tablename = "monitor_check"
        define_table(tablename,
                     service_id(),
                     Field("name", unique=True, length=255,
                           label = T("Name"),
                           ),
                     Field("function_name",
                           label = T("Script"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        represent = S3Represent(lookup=tablename)
        check_id = S3ReusableField("check_id", "reference %s" % tablename,
                                   label = T("Check"),
                                   ondelete = "CASCADE",
                                   represent = represent,
                                   requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "monitor_check.id",
                                                          represent)),
                                   )

        add_components(tablename,
                       monitor_check_option = {"name": "option",
                                               "joinby": "check_id",
                                               },
                       monitor_task = "check_id",
                       )

        # =============================================================================
        # Check Options
        # - default configuration of the Check

        tablename = "monitor_check_option"
        define_table(tablename,
                     check_id(),
                     # option is a reserved word in MySQL
                     Field("tag",
                           label = T("Option"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # =============================================================================
        # Tasks

        tablename = "monitor_task"
        define_table(tablename,
                     host_id(),
                     check_id(),
                     status_id(),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Enabled?"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # @ToDo: Fix represent
        represent = S3Represent(lookup=tablename, fields=["host_id", "check_id"])
        task_id = S3ReusableField("task_id", "reference %s" % tablename,
                                  label = T("Task"),
                                  ondelete = "CASCADE",
                                  represent = represent,
                                  requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "monitor_task.id",
                                                          represent)),
                                  )

        add_components(tablename,
                       monitor_alert = "task_id",
                       monitor_run = "task_id",
                       monitor_task_option = {"name": "option",
                                              "joinby": "task_id",
                                              },
                       )

        set_method("monitor", "task",
                   method = "enable",
                   action = self.monitor_task_enable_interactive)

        set_method("monitor", "task",
                   method = "disable",
                   action = self.monitor_task_disable_interactive)

        set_method("monitor", "task",
                   method = "check",
                   action = self.monitor_task_run)

        configure(tablename,
                  # Open the Options after creation
                  create_next = URL(c="monitor", f="task", args=["[id]", "option"]),
                  onaccept = self.monitor_task_onaccept,
                  )

        # =============================================================================
        # Task Options
        # - configuration of the Task

        tablename = "monitor_task_option"
        define_table(tablename,
                     task_id(),
                     # option is a reserved word in MySQL
                     Field("tag",
                           label = T("Option"),
                           ),
                     Field("value",
                           label = T("Value"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # =============================================================================
        # Runs

        tablename = "monitor_run"
        define_table(tablename,
                     task_id(),
                     status_id(),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  insertable = False,
                  )

        # =============================================================================
        # Alerts

        tablename = "monitor_alert"
        define_table(tablename,
                     task_id(),
                     self.pr_person_id(),
                     # Threshold
                     s3_comments(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_host_enable(host_id):
        """
            Enable a Host
            - Schedule all enabled Checks

            CLI API for shell scripts & to be called by S3Method
        """

        db = current.db
        table = current.s3db.monitor_task
        htable = db.monitor_host

        record = db(query).select(htable.id, # needed for update_record
                                  htable.enabled,
                                  limitby=(0, 1),
                                  ).first()

        if not record.enabled:
            # Flag it as enabled
            record.update_record(enabled = True)

        query = (table.host_id == host_id) & \
                (table.enabled == True) & \
                (table.deleted == False)
        tasks = db(query).select(table.id)

        # Do we have any Tasks already Scheduled?
        args = []
        for task in tasks:
            args.append("[%s]" % task.id)
        ttable = db.scheduler_task
        query = ((ttable.function_name == "monitor_run_task") & \
                 (ttable.args.belongs(args)) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id)
        exists = [r.id for r in exists]
        for task in tasks:
            task_id = task.id
            if task_id not in exists:
                current.s3task.schedule_task("monitor_run_task",
                                             args = [task_id],
                                             period = 300,  # seconds
                                             timeout = 300, # seconds
                                             repeats = 0    # unlimited
                                             )
        return "Host enabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_host_enable_interactive(r, **attr):
        """
            Enable a Host
            - Schedule all enabled Checks

            S3Method for interactive requests
        """

        result = S3MonitorModel.monitor_host_enable(r.id)
        current.session.confirmation = result
        redirect(URL(f="host"))

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_host_disable(host_id):
        """
            Disable a Host
            - Remove all Scheduled Checks

            CLI API for shell scripts & to be called by S3Method
        """
    
        db = current.db
        table = current.s3db.monitor_task
        htable = db.monitor_host

        record = db(query).select(htable.id, # needed for update_record
                                  htable.enabled,
                                  limitby=(0, 1),
                                  ).first()

        if record.enabled:
            # Flag it as disabled
            record.update_record(enabled = False)

        query = (table.host_id == host_id) & \
                (table.enabled == True) & \
                (table.deleted == False)
        tasks = db(query).select(table.id)

        # Do we have any Tasks already Scheduled?
        args = []
        for task in tasks:
            args.append("[%s]" % task.id)
        ttable = db.scheduler_task
        query = ((ttable.function_name == "monitor_run_task") & \
                 (ttable.args.belongs(args)) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            # Disable all
            db(query).update(status="STOPPED")
            return "Host disabled"
        else:
            return "Host already disabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_host_disable_interactive(r, **attr):
        """
            Disable a Host
            - Remove all Scheduled Checks

            S3Method for interactive requests
        """

        result = S3MonitorModel.monitor_host_disable(r.id)
        current.session.confirmation = result
        redirect(URL(f="host"))

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_host_onaccept(form):
        """
            Process the Enabled Flag
        """

        if form.record:
            # Update form
            # process of changed
            if form.record.enabled and not form.vars.enabled:
                S3MonitorModel.monitor_host_disable(form.vars.id)
            elif form.vars.enabled and not form.record.enabled:
                S3MonitorModel.monitor_host_enable(form.vars.id)
        else:
            # Create form
            # Process only if enabled
            if form.vars.enabled:
                S3MonitorModel.monitor_host_enable(form.vars.id)

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_host_check(r, **attr):
        """
            Run all enabled Tasks for this Host

            S3Method for interactive requests
        """

        db = current.db
        table = current.s3db.monitor_task
        query = (table.host_id == host_id) & \
                (table.enabled == True) & \
                (table.deleted == False)
        tasks = db(query).select(table.id)
        for task in tasks:
            current.s3task.async("monitor_run_task", args=[task.id])
        current.session.confirmation = \
            current.T("The check requests have been submitted, so results should appear shortly - refresh to see them")

        redirect(URL(c="monitor", f="run"))

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_task_enable(task_id):
        """
            Enable a Task
            - Schedule Check

            CLI API for shell scripts & to be called by S3Method
        """

        db = current.db
        table = current.s3db.monitor_task

        record = db(table.id == task_id).select(table.id, # needed for update_record
                                                table.enabled,
                                                limitby=(0, 1),
                                                ).first()

        if not record.enabled:
            # Flag it as enabled
            record.update_record(enabled = True)

        # Is the task already Scheduled?
        ttable = db.scheduler_task
        args = "[%s]" % task_id
        query = ((ttable.function_name == "monitor_run_task") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            return "Task already enabled"
        else:
            current.s3task.schedule_task("monitor_run_task",
                                         args = [task_id],
                                         period = 300,  # seconds
                                         timeout = 300, # seconds
                                         repeats = 0    # unlimited
                                         )
            return "Task enabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_task_enable_interactive(r, **attr):
        """
            Enable a Task
            - Schedule Check

            S3Method for interactive requests
        """

        result = S3MonitorModel.monitor_task_enable(r.id)
        current.session.confirmation = result
        redirect(URL(f="task"))

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_task_disable(task_id):
        """
            Disable a Check
            - Remove Schedule for Check

            CLI API for shell scripts & to be called by S3Method
        """
    
        db = current.db
        table = current.s3db.monitor_task

        record = db(table.id == task_id).select(table.id, # needed for update_record
                                                table.enabled,
                                                limitby=(0, 1),
                                                ).first()

        if record.enabled:
            # Flag it as disabled
            record.update_record(enabled = False)

        # Is the task already Scheduled?
        ttable = db.scheduler_task
        args = "[%s]" % task_id
        query = ((ttable.function_name == "monitor_run_task") & \
                 (ttable.args == args) & \
                 (ttable.status.belongs(["RUNNING", "QUEUED", "ALLOCATED"])))
        exists = db(query).select(ttable.id,
                                  limitby=(0, 1)).first()
        if exists:
            # Disable all
            db(query).update(status="STOPPED")
            return "Task disabled"
        else:
            return "Task already disabled"

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_task_disable_interactive(r, **attr):
        """
            Disable a Task
            - Remove Schedule for Check

            S3Method for interactive requests
        """

        result = S3MonitorModel.monitor_task_disable(r.id)
        current.session.confirmation = result
        redirect(URL(f="task"))

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_task_onaccept(form):
        """
            Process the Enabled Flag
            Create Form:
                PrePopulate Task Options from Check Options
        """

        if form.record:
            # Update form
            # process of changed
            if form.record.enabled and not form.vars.enabled:
                S3MonitorModel.monitor_task_disable(form.vars.id)
            elif form.vars.enabled and not form.record.enabled:
                S3MonitorModel.monitor_task_enable(form.vars.id)
        else:
            # Create form
            if form.vars.enabled:
                # Process only if enabled
                S3MonitorModel.monitor_task_enable(form.vars.id)
            # Pre-populate task options
            check_id = form.vars.check_id # or r.id if task created on tab of check
            db = current.db
            ctable = db.monitor_check_option
            query = (ctable.check_id == check_id) & \
                    (ctable.deleted == False)
            options = db(query).select(ctable.tag,
                                       ctable.value)
            if not options:
                return
            table = db.monitor_task_option
            for option in options:
                table.insert(tag=option.tag,
                             value=option.value)

    # -------------------------------------------------------------------------
    @staticmethod
    def monitor_task_run(r, **attr):
        """
            Run a Task

            S3Method for interactive requests
        """

        current.s3task.async("monitor_run_task", args=[r.id])
        current.session.confirmation = \
            current.T("The check request has been submitted, so results should appear shortly - refresh to see them")

        redirect(URL(c="monitor", f="run"))

# =============================================================================
def monitor_run_task(task_id):
    """
        Check a Service
    """

    db = current.db
    table = current.s3db.monitor_task
    ctable = db.monitor_check

    query = (table.id == task_id) & \
            (table.check_id == ctable.id)
    row = db(query).select(ctable.function_name,
                           #ttable.host_id,
                           limitby=(0, 1)
                           ).first()
    function_name = row.function_name

    # Load the Monitor template for this deployment
    template = current.deployment_settings.get_monitor_template()
    module_name = "applications.%s.private.templates.%s.monitor" \
        % (current.request.application, template)
    __import__(module_name)
    mymodule = sys.modules[module_name]
    S3Monitor = mymodule.S3Monitor()

    # Get the Check Script
    try:
        fn = getattr(S3Monitor, function_name)
    except:
        current.log.error("Check Script not found: %s" % function_name)
        return None

    # Create an entry in the monitor_run table
    rtable = db.monitor_run
    run_id = rtable.insert(task_id=task_id)
    # Ensure the entry is made even if the script crashes
    db.commit()

    # Run the script
    result = fn(task_id, run_id)

    # Update the entry with the result
    if result:
        status = result
    else:
        # No result
        status = 2 # Warning

    db(rtable.id == run_id).update(status=status)

    # @ToDo: Cascade status to Host

    return result

# =============================================================================
def monitor_check_email_reply(run_id):
    """
        Check whether we have received a reply to an Email check
    """

    rtable = current.s3db.monitor_run
    record = current.db(rtable.id == run_id).select(rtable.id,
                                                    rtable.status,
                                                    limitby=(0, 1)).first()
    try:
        status = record.status
    except:
        # Can't find run record!
        # @ToDo: Send Alert
        pass
    else:
        if status == 2:
            # Still in Warning State: Make it go Critical
            record.update_record(status=3)
            # @ToDo: Send Alert

# END =========================================================================
