# -*- coding: utf-8 -*-

""" AidIQ-specific Models

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("AidIQProjectBudgetModel",
           "aidiq_update_project_budget",
           )

from gluon import *

from s3 import *

# =============================================================================
class AidIQProjectBudgetModel(S3Model):

    names = ("aidiq_project_budget",
             )

    def model(self):

        T = current.T

        is_float_represent = IS_FLOAT_AMOUNT.represent
        float_represent = lambda v: is_float_represent(v, precision=2)

        # ---------------------------------------------------------------------
        # Report on Budget by Project [/ Milestone]
        #
        tablename = "aidiq_project_budget"
        self.define_table(tablename,
                          self.project_project_id(empty = False,
                                                  #ondelete = "CASCADE",
                                                  ),
                          self.project_milestone_id(#empty = True,
                                                    ondelete = "CASCADE",
                                                    ),
                          s3_currency(),
                          Field("total_value", "double",
                                default = 0.0,
                                label = T("Total Contract Value"),
                                represent = float_represent,
                                ),
                          # @ToDo: Sub-table to specify individual overheads
                          Field("total_overheads", "double",
                                default = 0.0,
                                label = T("Total Overheads"),
                                represent = float_represent,
                                comments = T("Hosting, Travel, Sub-contracts"),
                                ),
                          Field("hours_contracted", "double",
                                default = 0,
                                label = T("Hours Contracted"),
                                represent = float_represent,
                                ),
                          Field("rate_contracted", "double",
                                label = T("Hourly Rate (Contracted)"),
                                represent = float_represent,
                                # Calculated
                                writable = False,
                                ),
                          Field("hours_used", "double",
                                label = T("Hours Used"),
                                represent = lambda v: is_float_represent(v, precision=1),
                                # Calculated
                                writable = False,
                                ),
                          Field("rate_effective", "double",
                                label = T("Hourly Rate (Effective)"),
                                represent = float_represent,
                                # Calculated
                                writable = False,
                                ),
                          Field("hours_remaining", "double",
                                label = T("Hours Remaining"),
                                represent = lambda v: is_float_represent(v, precision=1),
                                # Calculated
                                writable = False,
                                ),
                          Field("weeks_remaining_standard", "double",
                                label = T("Weeks Remaining (Standard)"),
                                represent = float_represent,
                                # Calculated
                                writable = False,
                                ),
                          Field("weeks_remaining_current", "double",
                                label = T("Weeks Remaining (Current Velocity)"),
                                represent = float_represent,
                                # Calculated
                                writable = False,
                                ),
                          *s3_meta_fields())

        self.configure(tablename,
                       onaccept = self.aidiq_project_budget_onaccept,
                       )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def aidiq_project_budget_onaccept(form):
        """
            Read the Hours recorded against a Project or Milestone
        """

        form_vars = form.vars

        project_id = form_vars.project_id
        milestone_id = form_vars.milestone_id

        aidiq_update_project_budget(project_id, milestone_id)

# =============================================================================
def aidiq_update_project_budget(project_id, milestone_id=None):
    """
        Update the aidiq_project_budget from the Hours recorded against a Project or Milestone
    """

    db = current.db
    s3db = current.s3db

    apbtable = s3db.aidiq_project_budget
    query = (apbtable.project_id == project_id) & \
            (apbtable.milestone_id == milestone_id)
    record = db(query).select(apbtable.id,
                              apbtable.total_value,
                              apbtable.total_overheads,
                              apbtable.hours_contracted,
                              limitby = (0, 1),
                              ).first()
    if not record:
        # Nothing to calculate
        return

    value = record.total_value - record.total_overheads
    hours_contracted = record.hours_contracted
    if value and hours_contracted:
        rate_contracted = value / hours_contracted
    else:
        rate_contracted = None

    titable = s3db.project_time
    tatable = s3db.project_task
    tptable = s3db.project_task_project

    query = (tptable.project_id == project_id) & \
            (tptable.task_id == tatable.id) & \
            (titable.task_id == tatable.id)
    if milestone_id:
        tmtable = s3db.project_task_milestone
        query &= (tmtable.milestone_id == milestone_id) & \
                 (tmtable.task_id == tatable.id)

    sum = titable.hours.sum()
    hours_used = db(query).select(sum).first()[sum]

    if value and hours_used:
        rate_effective = value / hours_used
    else:
        rate_effective = None

    hours_remaining = hours_contracted - hours_used

    if hours_remaining:
        weeks_remaining_standard = hours_remaining / 40
        min = titable.date.min()
        earliest = db(query).select(min).first()[min]
        if earliest:
            delta = current.request.utcnow - earliest
            weeks = delta.days / 7
            current_velocity = hours_used / weeks
            weeks_remaining_current = hours_remaining / current_velocity
        else:
            weeks_remaining_current = None
    else:
        weeks_remaining_standard = 0
        weeks_remaining_current = 0

    record.update_record(rate_contracted = rate_contracted,
                         hours_used = hours_used,
                         rate_effective = rate_effective,
                         hours_remaining = hours_remaining,
                         weeks_remaining_standard = weeks_remaining_standard,
                         weeks_remaining_current = weeks_remaining_current,
                         )

# END =========================================================================
