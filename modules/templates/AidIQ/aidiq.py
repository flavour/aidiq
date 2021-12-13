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
           )

from gluon import *

from s3 import *

# =============================================================================
class AidIQProjectBudgetModel(S3Model):

    names = ("aidiq_project_budget",
             )

    def model(self):

        T = current.T

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
                          Field("total_value", "float",
                                label = T("Total Contract Value"),
                                ),
                          # @ToDo: Sub-table to specify individual overheads
                          Field("total_overheads", "float",
                                label = T("Total Overheads"),
                                comments = T("Hosting, Travel, Sub-contracts"),
                                ),
                          Field("hours_contracted", "float",
                                label = T("Hours Contracted"),
                                ),
                          Field("rate_contracted", "float",
                                label = T("Hourly Rate (Contracted)"),
                                # Calculated
                                writable = False,
                                ),
                          Field("hours_used", "float",
                                label = T("Hours Used"),
                                # Calculated
                                writable = False,
                                ),
                          Field("rate_effective", "float",
                                label = T("Hourly Rate (Effective)"),
                                # Calculated
                                writable = False,
                                ),
                          Field("time_remaining_minimum", "float",
                                label = T("Time Remaining (Minimum)"),
                                # Calculated
                                writable = False,
                                ),
                          Field("time_remaining_current", "float",
                                label = T("Time Remaining (Current Velocity)"),
                                # Calculated
                                writable = False,
                                ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

# END =========================================================================
