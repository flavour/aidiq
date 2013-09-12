# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current, URL, TR, TD, DIV
from gluon.storage import Storage

T = current.T
settings = current.deployment_settings

"""
    Template settings for AidIQ
"""

# Pre-Populate
settings.base.prepopulate = ["AidIQ"]

# Theme
settings.base.theme = "AidIQ"

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
def formstyle_row(id, label, widget, comment, hidden=False):
    if hidden:
        hide = "hide"
    else:
        hide = ""
    row = TR(TD(DIV(label,
                _id=id + "1",
                _class="w2p_fl %s" % hide),
            DIV(widget,
                _id=id,
                _class="w2p_fw %s" % hide),
            DIV(comment,
                _id=id, 
                _class="w2p_fc %s" % hide),
           ))
    return row
def form_style(self, xfields):
    """
        @ToDo: Requires further changes to code to use
        - Adding a formstyle_row setting to use for indivdual rows
        Use new Web2Py formstyle to generate form using DIVs & CSS
        CSS can then be used to create MUCH more flexible form designs:
        - Labels above vs. labels to left
        - Multiple Columns 
    """
    form = DIV()

    for id, a, b, c, in xfields:
        form.append(formstyle_row(id, a, b, c))

    return form
settings.ui.formstyle_row = formstyle_row
settings.ui.formstyle = formstyle_row

# Uncomment this to request the Organisation when a user registers
settings.auth.registration_requests_organisation = True
# Uncomment this to have the Organisation selection during registration be mandatory
settings.auth.registration_organisation_mandatory = True
# Uncomment to set the default role UUIDs assigned to newly-registered users
settings.auth.registration_roles = {"site_id": ["project_reader"]}

def aidiq_realm_entity(table, row):
    """
        Assign a Realm Entity to records
    """

    tablename = table._tablename

    # Do not apply realms for Master Data
    # @ToDo: Restore Realms and add a role/functionality support for Master Data  
    if tablename in [#"hrm_certificate",
                     #"hrm_department",
                     #"hrm_job_title",
                     #"hrm_course",
                     #"hrm_programme",
                     #"member_membership_type",
                     #"vol_award",
                     "project_status",
                     ]:
        return None

    db = current.db
    s3db = current.s3db

    # Entity reference fields
    EID = "pe_id"
    #OID = "organisation_id"
    SID = "site_id"
    #GID = "group_id"
    PID = "person_id"

    # Owner Entity Foreign Key
    realm_entity_fks = dict(pr_contact = EID,
                            #pr_contact_emergency = EID,
                            #pr_physical_description = EID,
                            pr_address = EID,
                            pr_image = EID,
                            #pr_identity = PID,
                            #pr_education = PID,
                            #pr_note = PID,
                            hrm_human_resource = SID,
                            #inv_recv = SID,
                            #inv_recv_item = "req_id",
                            #inv_send = SID,
                            #inv_track_item = "track_org_id",
                            #inv_adj_item = "adj_id",
                            #req_req_item = "req_id"
                            )

    # Default Foreign Keys (ordered by priority)
    default_fks = [#"catalog_id",
                   "project_id",
                   "project_location_id"
                   ]

    # Link Tables
    realm_entity_link_table = dict(
        project_task = Storage(tablename = "project_task_project",
                               link_key = "task_id"
                               )
        )
    if tablename in realm_entity_link_table:
        # Replace row with the record from the link table
        link_table = realm_entity_link_table[tablename]
        table = s3db[link_table.tablename]
        rows = db(table[link_table.link_key] == row.id).select(table.id,
                                                               limitby=(0, 1))
        if rows:
            # Update not Create
            row = rows.first()

    # Check if there is a FK to inherit the realm_entity
    realm_entity = 0
    fk = realm_entity_fks.get(tablename, None)
    for default_fk in [fk] + default_fks:
        if default_fk in table.fields:
            fk = default_fk
            # Inherit realm_entity from parent record
            if fk == EID:
                ftable = s3db.pr_person
                query = ftable[EID] == row[EID]
            else:
                ftablename = table[fk].type[10:] # reference tablename
                ftable = s3db[ftablename]
                query = (table.id == row.id) & \
                        (table[fk] == ftable.id)
            record = db(query).select(ftable.realm_entity,
                                      limitby=(0, 1)).first()
            if record:
                realm_entity = record.realm_entity
                break
            #else:
            # Continue to loop through the rest of the default_fks
            # Fall back to default get_realm_entity function
    
    use_user_organisation = False
    # Suppliers & Partners are owned by the user's organisation
    #if realm_entity == 0 and tablename == "org_organisation":
    #    ott = s3db.org_organisation_type
    #    query = (table.id == row.id) & \
    #            (table.organisation_type_id == ott.id)
    #    row = db(query).select(ott.name,
    #                           limitby=(0, 1)
    #                           ).first()

    #    if row and row.name != "Red Cross / Red Crescent":
    #        use_user_organisation = True

    # Groups are owned by the user's organisation
    #elif tablename in ["pr_group"]:
    #    use_user_organisation = True

    user = current.auth.user
    if use_user_organisation and user:
        # @ToDo - this might cause issues if the user's org is different from the realm that gave them permissions to create the Org 
        realm_entity = s3db.pr_get_pe_id("org_organisation",
                                         user.organisation_id)

    return realm_entity

settings.auth.realm_entity = aidiq_realm_entity

# Projects
# Uncomment this to use settings suitable for detailed Task management
settings.project.mode_task = True
# Uncomment this to use Activities for projects
settings.project.activities = True
# Uncomment this to use Milestones in project/task.
settings.project.milestones = True
# Uncomment this to disable Sectors in projects
#settings.project.sectors = False
# Change the label for Organisation from 'Lead Implementer'
settings.project.organisation_roles = {
    1: T("Customer")
}

from s3 import s3forms
settings.ui.crud_form_project_project = s3forms.S3SQLCustomForm(
        "organisation_id",
        "name",
        "description",
        "status_id",
        "start_date",
        "end_date",
        "calendar",
        "human_resource_id",
        s3forms.S3SQLInlineComponentCheckbox(
            "sector",
            label = T("Sectors"),
            field = "sector_id",
            cols = 4,
        ),
        "budget",
        "currency",
        "comments",
    )

# Uncomment to allow HR records to be deletable rather than just marking them as obsolete
settings.hrm.deletable = True

# Frontpage settings
# RSS feeds
#deployment_settings.frontpage.rss = [
#    {"title": "Blog",
#     # Drupal Blog
#     "url": "http://aidiq.com/blog/feed"
#    },
#    {"title": "Twitter",
#     # Use idfromuser.com to determine the ID
#     # @SahanaFOSS
#     "url": "http://twitter.com/statuses/user_timeline/80964032.rss"
#     # Hashtag
#     #url: "http://search.twitter.com/search.atom?q=%23eqnz"
#    }
#]

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
    #("survey", Storage(
    #        name_nice = T("Surveys"),
    #        #description = "Create, enter, and manage surveys.",
    #        restricted = True,
    #        module_type = 5,
    #    )),
])
