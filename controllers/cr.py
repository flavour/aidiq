# -*- coding: utf-8 -*-

"""
    Shelter Registry - Controllers
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    from s3db.cms import cms_index
    return cms_index(c, alt_function="index_alt")

# -----------------------------------------------------------------------------
def index_alt():
    """
        Module homepage for non-Admin users when no CMS content found
    """

    # Just redirect to the list of Shelters
    s3_redirect_default(URL(f = "shelter"))

# =============================================================================
def shelter():
    """
        RESTful CRUD controller
    """

    tablename = "cr_shelter"

    # Filter to just Open shelters (status=2)
    from s3 import s3_set_default_filter
    s3_set_default_filter("shelter_details.status",
                          [2, None],
                          tablename = tablename)

    # Pre-processor
    def prep(r):
        # Function to call for all Site Instance Types
        from s3db.org import org_site_prep
        org_site_prep(r)

        method = r.method
        if method == "create":
            dtable = s3db.cr_shelter_details
            dtable.population_day.readable = False
            dtable.population_night.readable = False

        elif method == "import":
            s3db.cr_shelter.organisation_id.default = None

        elif method == "profile":
            name = r.record.name
            site_id = r.record.site_id

            profile_header = settings.get_ui_profile_header(r)

            map_widget = {"label": T("Housing Units"),
                          "type": "map",
                          "icon": "globe",
                          "colspan": 2,
                          "height": 500,
                          #"bbox": bbox,
                          }
            ftable = s3db.gis_layer_feature
            query = (ftable.controller == "cr") & \
                    (ftable.function == "shelter_unit")
            layer = db(query).select(ftable.layer_id,
                                     limitby = (0, 1),
                                     ).first()
            try:
                layer = {"active": True,
                         "layer_id": layer.layer_id,
                         "filter": "~.site_id=%s" % site_id,
                         "name": T("Housing Units"),
                         "id": "profile-header-%s-%s" % (tablename, site_id),
                         }
            except:
                # No suitable prepop found
                layer = None

            profile_widgets = [map_widget,
                               ]
            s3db.configure(tablename,
                           profile_header = profile_header,
                           profile_layers = (layer,),
                           profile_title = "%s : %s" % (s3_str(s3.crud_strings["cr_shelter"].title_display),
                                                        name),
                           profile_widgets = profile_widgets,
                           )

        if r.interactive:
            if r.component:
                component_name = r.component_name
                if component_name == "shelter_registration":
                    if settings.get_cr_shelter_housing_unit_management():
                        # Filter housing units to units of this shelter
                        from s3 import IS_ONE_OF
                        field = s3db.cr_shelter_registration.shelter_unit_id
                        dbset = db(s3db.cr_shelter_unit.site_id == r.record.site_id)
                        field.requires = IS_EMPTY_OR(IS_ONE_OF(dbset, "cr_shelter_unit.id",
                                                               field.represent,
                                                               sort = True,
                                                               ))
                    s3db.pr_person.pe_label.label = T("Registration Number")
                    s3.crud_strings.cr_shelter_registration = Storage(
                        label_create = T("Register Person"),
                        title_display = T("Registration Details"),
                        title_list = T("Registered People"),
                        title_update = T("Edit Registration"),
                        label_list_button = T("List Registrations"),
                        msg_record_created = T("Registration added"),
                        msg_record_modified = T("Registration updated"),
                        msg_record_deleted = T("Registration entry deleted"),
                        msg_list_empty = T("No people currently registered in this shelter"),
                        )

                elif component_name == "shelter_allocation":
                    s3.crud_strings.cr_shelter_allocation = Storage(
                        label_create = T("Allocate Group"),
                        title_display = T("Allocation Details"),
                        title_list = T("Allocated Groups"),
                        title_update = T("Edit Allocation"),
                        label_list_button = T("List Allocations"),
                        msg_record_created = T("Reservation done"),
                        msg_record_modified = T("Reservation updated"),
                        msg_record_deleted = T("Reservation entry deleted"),
                        msg_list_empty = T("No groups currently allocated for this shelter"),
                        )

        return True
    s3.prep = prep

    from s3db.cr import cr_shelter_rheader
    return s3_rest_controller(rheader = cr_shelter_rheader)

# -----------------------------------------------------------------------------
def shelter_flag():
    """
        Shelter Flags - RESTful CRUD controller
    """

    def prep(r):

        if r.interactive:

            # Filter task_assign_to option to human resources and teams
            assignees = []

            # Select active HRs
            hr = s3db.resource("hrm_human_resource",
                               filter = FS("status") == 1,
                               )
            rows = hr.select(["person_id$pe_id"],
                             limit = None,
                             represent = False,
                             ).rows
            if rows:
                assignees.extend(row["pr_person.pe_id"] for row in rows)

            # Select teams
            teams = s3db.resource("pr_group",
                                  filter = FS("group_type") == 3,
                                  )
            rows = teams.select(["pe_id"],
                                limit = None,
                                represent = False,
                                ).rows
            if rows:
                assignees.extend(row["pr_group.pe_id"] for row in rows)

            # Set filter for task_assign_to.requires
            field = r.table.task_assign_to
            requires = field.requires
            if isinstance(requires, IS_EMPTY_OR):
                requires = requires.other
            requires.set_filter(filterby = "pe_id",
                                filter_opts = assignees,
                                )
        return True
    s3.prep = prep

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def shelter_inspection():
    """
        Shelter Inspections - RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def shelter_inspection_flag():
    """
        Shelter Inspection Flags - RESTful CRUD controller
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def shelter_registration():
    """
        RESTful CRUD controller
    """

    s3.crud_strings.cr_shelter_registration = Storage(
        label_create = T("Register Person"),
        title_display = T("Registration Details"),
        title_list = T("Registered People"),
        title_update = T("Edit Registration"),
        label_list_button = T("List Registrations"),
        msg_record_created = T("Registration added"),
        msg_record_modified = T("Registration updated"),
        msg_record_deleted = T("Registration entry deleted"),
        msg_list_empty = T("No people currently registered in shelters"),
        )

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def shelter_service():
    """
        RESTful CRUD controller
        List / add shelter services (e.g. medical, housing, food, ...)
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def shelter_type():
    """
        RESTful CRUD controller
        List / add shelter types (e.g. NGO-operated, Government evacuation center,
        School, Hospital -- see Agasti opt_camp_type.)
    """

    return s3_rest_controller()

# -----------------------------------------------------------------------------
def shelter_unit():
    """
        REST controller to
            retrieve options for shelter unit selection
            show layer on Map
            imports
    """

    # [Geo]JSON & Map Popups or Imports only
    def prep(r):
        if r.representation == "plain":
            # Have the 'Open' button open in the context of the Shelter
            record_id = r.id
            stable = s3db.cr_shelter
            utable = s3db.cr_shelter_unit
            query = (utable.id == record_id) & \
                    (utable.site_id == stable.site_id)
            row = db(query).select(stable.id,
                                   limitby = (0, 1),
                                   ).first()
            s3db.configure("cr_shelter_unit",
                           popup_url = URL(c="cr", f="shelter",
                                           args = [row.id,
                                                   "shelter_unit",
                                                   record_id,
                                                   ],
                                           ),
                        )
            return True
        elif r.representation in ("json", "geojson", "plain") or \
             r.method == "import":
            return True
        return False

    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def incoming():
    """
        Incoming Shipments for Sites

        Used from Requests rheader when looking at Transport Status
    """

    # @ToDo: Create this function!
    from s3db.inv import inv_incoming
    return inv_incoming()

# -----------------------------------------------------------------------------
def req_match():
    """ Match Requests """

    from s3db.inv import inv_req_match
    return inv_req_match()

# END =========================================================================
