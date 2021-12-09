# -*- coding: utf-8 -*-

#from collections import OrderedDict

from gluon import current#, URL
from gluon.storage import Storage

def config(settings):
    """
        Settings for Bhutan's extensions to the core SaFiRe template.
    """

    T = current.T

    settings.base.system_name = T("Disaster Management Information System")
    settings.base.system_name_short = T("DMIS")

    # PrePopulate data
    #settings.base.prepopulate.append("SAFIRE/BT")
    settings.base.prepopulate_demo = ("default/users",
                                      "SAFIRE/BT/Demo",
                                      )

    settings.ui.menu_logo = "/%s/static/themes/SAFIRE/BT/DDM.png" % current.request.application

    modules = settings.modules
    modules["br"] = {"name_nice": T("Case Management"), "module_type": 10}
    modules["budget"] = {"name_nice": T("Budget Management"), "module_type": 10}
    modules["dc"] = {"name_nice": T("Disaster Assessments"), "module_type": 10}
    modules["disease"] = {"name_nice": T("Disease"), "module_type": 10}
    modules["edu"] = {"name_nice": T("Schools"), "module_type": 10}
    modules["stats"] = {"name_nice": T("Statistics"), "module_type": 10}
    modules["transport"] = {"name_nice": T("Transport"), "module_type": 10}
    modules["water"] = {"name_nice": T("Water"), "module_type": 10}

    settings.cr.people_registration = True

    settings.gis.latlon_selector = True

    settings.hrm.id_cards = True
    settings.hrm.show_organisation = True

    settings.supply.catalog_multi = False

    settings.project.mode_3w = True
    settings.project.multiple_organisations = True
    settings.project.activities = True
    settings.project.activity_types = True
    settings.project.budget_monitoring = True
    settings.project.goals = True
    settings.project.outcomes = True
    settings.project.outputs = True
    settings.project.indicators = True
    #settings.project.indicator_criteria = True
    settings.project.programmes = True
    settings.project.themes = True

    # -------------------------------------------------------------------------
    def customise_asset_asset_resource(r, tablename):

        s3db = current.s3db

        s3db.asset_asset.site_id.represent.show_type = False

        list_fields = [(T("Store"), "site_id"),
                       (T("Asset Number"), "number"),
                       (T("Item Name"), "item_id$name"),
                       (T("Condition"), "cond"),
                       (T("Assigned To"), "assigned_to_id"),
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

    settings.customise_asset_asset_resource = customise_asset_asset_resource

    # -------------------------------------------------------------------------
    def customise_asset_asset_controller(**attr):

        workflow = current.request.get_vars.get("workflow")
        if workflow:

            s3 = current.response.s3

            # Custom prep
            standard_prep = s3.prep
            def custom_prep(r):
                # Call standard prep
                if callable(standard_prep):
                    result = standard_prep(r)

                if workflow == "issue":
                    # Filter to Unassigned Assets
                    from s3db.asset import ASSET_LOG_ASSIGN
                    available_assets = []
                    aappend = available_assets.append
                    seen = []
                    sappend = seen.append
                    ltable = current.s3db.asset_log
                    logs = current.db(ltable.deleted == False).select(ltable.asset_id,
                                                                      ltable.status,
                                                                      orderby = ~ltable.date,
                                                                      )
                    for log in logs:
                        asset_id = log.asset_id
                        if asset_id in seen:
                            continue
                        sappend(asset_id)
                        if log.status != ASSET_LOG_ASSIGN:
                            aappend(asset_id)

                    from s3 import FS
                    r.resource.add_filter(FS("~.id").belongs(available_assets))
                elif workflow == "return":
                    # Filter to Assets with log status == ASSET_LOG_ASSIGN
                    from s3db.asset import ASSET_LOG_ASSIGN
                    assigned_assets = []
                    aappend = assigned_assets.append
                    seen = []
                    sappend = seen.append
                    ltable = current.s3db.asset_log
                    logs = current.db(ltable.deleted == False).select(ltable.asset_id,
                                                                      ltable.status,
                                                                      orderby = ~ltable.date,
                                                                      )
                    for log in logs:
                        asset_id = log.asset_id
                        if asset_id in seen:
                            continue
                        sappend(asset_id)
                        if log.status == ASSET_LOG_ASSIGN:
                            aappend(asset_id)

                    from s3 import FS
                    r.resource.add_filter(FS("~.id").belongs(assigned_assets))

                return result
            s3.prep = custom_prep

            # Custom postp
            standard_postp = s3.postp
            def custom_postp(r, output):
                # Call standard postp
                if callable(standard_postp):
                    output = standard_postp(r, output)

                from gluon import URL
                from s3 import s3_str

                if workflow == "issue":
                    s3.actions = [{"label": s3_str(T("Issue")),
                                   "url": URL(f = "asset",
                                              args = ["[id]", "log", "assignperson"],
                                              ),
                                   "_class": "action-btn",
                                   },
                                  ]
                elif workflow == "return":
                    s3.actions = [{"label": s3_str(T("Return")),
                                   "url": URL(f = "asset",
                                              args = ["[id]", "log", "return"],
                                              ),
                                   "_class": "action-btn",
                                   },
                                  ]

                return output
            s3.postp = custom_postp

        return attr

    settings.customise_asset_asset_controller = customise_asset_asset_controller

    # -------------------------------------------------------------------------
    def customise_dc_response_resource(r, tablename):

        if r.controller in ("event",
                            "hrm", # Training Event Evaluations
                            ):
            return

        s3db = current.s3db

        template_name = r.get_vars.get("~.template_id$name")
        if template_name:
            ttable = s3db.dc_template
            template = current.db(ttable.name == template_name).select(ttable.id,
                                                                       limitby = (0, 1),
                                                                       ).first()
            if template:
                f = s3db.dc_response.template_id
                f.default = template.id
                f.readable = f.writable = False

            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Create %s") % template_name,
                title_display = T("%s Details") % template_name,
                title_list = T("%ss") % template_name,
                title_update = T("Edit %s") % template_name,
                #title_upload = T("Import %ss") % template_name,
                label_list_button = T("List %ss") % template_name,
                label_delete_button = T("Delete %s") % template_name,
                msg_record_created = T("%s added") % template_name,
                msg_record_modified = T("%s updated") % template_name,
                msg_record_deleted = T("%s deleted") % template_name,
                msg_list_empty = T("No %ss currently registered") % template_name)

        from s3 import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3SQLCustomForm, S3SQLInlineLink

        crud_form = S3SQLCustomForm(S3SQLInlineLink("event",
                                                    field = "event_id",
                                                    #label = type_label,
                                                    multiple = False,
                                                    ),
                                    "template_id",
                                    "date",
                                    "location_id",
                                    "organisation_id",
                                    "person_id",
                                    "comments",
                                    )

        s3db.configure(tablename,
                       crud_form = crud_form,
                       )

    settings.customise_dc_response_resource = customise_dc_response_resource

    # -------------------------------------------------------------------------
    def customise_dc_target_resource(r, tablename):

        if r.controller in ("event",
                            "hrm", # Training Event Evaluations
                            ):
            return

        s3db = current.s3db

        template_name = r.get_vars.get("~.template_id$name")
        if template_name:
            ttable = s3db.dc_template
            template = current.db(ttable.name == template_name).select(ttable.id,
                                                                       limitby = (0, 1),
                                                                       ).first()
            if template:
                f = s3db.dc_target.template_id
                f.default = template.id
                f.readable = f.writable = False

            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Create %s") % template_name,
                title_display = T("%s Details") % template_name,
                title_list = T("%ss") % template_name,
                title_update = T("Edit %s") % template_name,
                #title_upload = T("Import %ss") % template_name,
                label_list_button = T("List %ss") % template_name,
                label_delete_button = T("Delete %s") % template_name,
                msg_record_created = T("%s added") % template_name,
                msg_record_modified = T("%s updated") % template_name,
                msg_record_deleted = T("%s deleted") % template_name,
                msg_list_empty = T("No %ss currently registered") % template_name)

        from s3 import S3DateFilter, S3LocationFilter, S3OptionsFilter, S3SQLCustomForm, S3SQLInlineLink

        crud_form = S3SQLCustomForm(S3SQLInlineLink("event",
                                                    field = "event_id",
                                                    #label = type_label,
                                                    multiple = False,
                                                    ),
                                    "template_id",
                                    "date",
                                    "location_id",
                                    "comments",
                                    )

        filter_widgets = [S3OptionsFilter("event__link.event_id"),
                          S3LocationFilter(),
                          S3DateFilter("date"),
                          ]

        list_fields = ["event__link.event_id",
                       "location_id$L1",
                       "location_id$L2",
                       (T("Hazard Type"), "name"),
                       (T("Reporting Date"), "date"),
                       (T("Reported by"), "created_by"),
                       ]

        s3db.configure(tablename,
                       crud_form = crud_form,
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       )

    settings.customise_dc_target_resource = customise_dc_target_resource

    # -------------------------------------------------------------------------
    def customise_edu_school_resource(r, tablename):

        s3db = current.s3db

        #s3db.edu_school.

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Education Facility"),
            title_display = T("Education Facility Details"),
            title_list = T("Education Facilities"),
            title_update = T("Edit Education Facility"),
            #title_upload = T("Import Education Facilities"),
            label_list_button = T("List Education Facilities"),
            label_delete_button = T("Delete Education Facility"),
            msg_record_created = T("Education Facility added"),
            msg_record_modified = T("Education Facility updated"),
            msg_record_deleted = T("Education Facility deleted"),
            msg_list_empty = T("No Education Facilities currently registered"))

        list_fields = ["name",
                       "location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

    settings.customise_edu_school_resource = customise_edu_school_resource

    # -------------------------------------------------------------------------
    def customise_med_hospital_resource(r, tablename):

        s3db = current.s3db

        #s3db.med_hospital.

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Health Facility"),
            title_display = T("Health Facility Details"),
            title_list = T("Health Facilities"),
            title_update = T("Edit Health Facility"),
            #title_upload = T("Import Health Facilities"),
            label_list_button = T("List Health Facilities"),
            label_delete_button = T("Delete Health Facility"),
            msg_record_created = T("Health Facility added"),
            msg_record_modified = T("Health Facility updated"),
            msg_record_deleted = T("Health Facility deleted"),
            msg_list_empty = T("No Health Facilities currently registered"))

        list_fields = ["name",
                       "location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

    settings.customise_med_hospital_resource = customise_med_hospital_resource

    # -------------------------------------------------------------------------
    def customise_hrm_human_resource_controller(**attr):

        #if r.representation == "card":
        # Configure ID card layout
        from templates.RMS.idcards import IDCardLayout
        #resource.configure(pdf_card_layout = IDCardLayout)
        current.s3db.configure("hrm_human_resource", pdf_card_layout = IDCardLayout)

        return attr

    settings.customise_hrm_human_resource_controller = customise_hrm_human_resource_controller

    # -------------------------------------------------------------------------
    def customise_hrm_training_event_resource(r, tablename):

        from s3 import S3DateTime
        date_represent = S3DateTime.date_represent

        s3db = current.s3db

        table = s3db.hrm_training_event
        table.site_id.represent.show_type = False
        table.start_date.represent = date_represent
        table.end_date.represent = date_represent

        list_fields = [(T("Training Title"), "course_id"),
                       (T("From Date"), "start_date"),
                       (T("To Date"), "end_date"),
                       (T("Location"), "site_id"),
                       (T("Status"), "comments"),
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

    settings.customise_hrm_training_event_resource = customise_hrm_training_event_resource

    # -------------------------------------------------------------------------
    def customise_inv_inv_item_resource(r, tablename):

        from s3 import S3Represent

        s3db = current.s3db

        s3db.inv_inv_item.site_id.represent.show_type = False
        represent = S3Represent(lookup = "supply_item_category")
        s3db.supply_item.item_category_id.represent = represent
        s3db.supply_item_category.parent_item_category_id.represent = represent

        list_fields = [(T("Store"), "site_id"),
                       (T("Item Name"), "item_id$name"),
                       (T("Item Category"), "item_id$item_category_id$parent_item_category_id"),
                       (T("Item Sub-category"), "item_id$item_category_id"),
                       (T("Quantity"), "quantity"),
                       (T("UoM"), "item_pack_id"),
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

    settings.customise_inv_inv_item_resource = customise_inv_inv_item_resource

    # -------------------------------------------------------------------------
    def customise_org_facility_resource(r, tablename):

        s3db = current.s3db

        #s3db.org_facility.

        facility_type = r.get_vars.get("site_facility_type.facility_type_id$name")
        if facility_type:
            current.response.s3.crud_strings[tablename] = Storage(
                label_create = T("Create %s") % facility_type,
                title_display = T("%s Details") % facility_type,
                title_list = T("%ss") % facility_type,
                title_update = T("Edit %s") % facility_type,
                #title_upload = T("Import %ss") % facility_type,
                label_list_button = T("List %ss") % facility_type,
                label_delete_button = T("Delete %s") % facility_type,
                msg_record_created = T("%s added") % facility_type,
                msg_record_modified = T("%s updated") % facility_type,
                msg_record_deleted = T("%s deleted") % facility_type,
                msg_list_empty = T("No %ss currently registered") % facility_type)

        list_fields = ["name",
                       "location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "location_id$L4",
                       ]

        s3db.configure(tablename,
                       filter_widgets = None,
                       list_fields = list_fields,
                       )

    settings.customise_org_facility_resource = customise_org_facility_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        # Configuration for Suppliers

        list_fields = [(T("Supplier Name"), "name"),
                       (T("Supplier Address"), "donor.organisation_id"),
                       (T("Supplier License Number"), "comments"),
                       (T("Contact No"), "phone"),
                       (T("Email ID"), "contact"),
                       ]

        current.s3db.configure(tablename,
                               list_fields = list_fields,
                               )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_project_project_resource(r, tablename):

        list_fields = [(T("Project Name"), "name"),
                       (T("Funding Source"), "donor.organisation_id"),
                       (T("Project Area"), "location.location_id"),
                       (T("Start Date"), "start_date"),
                       (T("End Date"), "end_date"),
                       (T("Budget(Nu in million)"), "budget"),
                       ]

        current.s3db.configure(tablename,
                               list_fields = list_fields,
                               )

    settings.customise_project_project_resource = customise_project_project_resource

    # -------------------------------------------------------------------------
    def project_task_onaccept(form, create=True):
        """
            Send Person a Notification when they are assigned to a Task
            Log changes in Incident Log

            COPY of one in SAFIRE (referenced by customise_project_task_resource)
        """

        if current.request.function == "scenario":
            # Must be a Scenario
            # - don't Log
            # - don't send Notification
            return

        db = current.db
        s3db = current.s3db
        ltable = s3db.event_task

        form_vars = form.vars
        form_vars_get = form_vars.get
        task_id = form_vars_get("id")
        link = db(ltable.task_id == task_id).select(ltable.incident_id,
                                                    limitby = (0, 1),
                                                    ).first()
        if not link:
            # Not attached to an Incident
            # - don't Log
            # - don't send Notification
            return

        incident_id = link.incident_id

        if create:
            pe_id = form_vars_get("pe_id")
            # Log
            name = form_vars_get("name")
            if name:
                s3db.event_incident_log.insert(incident_id = incident_id,
                                               name = "Task Created",
                                               comments = name,
                                               )

        else:
            # Update
            pe_id = None
            record = form.record
            if record: # Not True for a record merger
                from s3dal import Field
                table = s3db.project_task
                changed = {}
                for var in form_vars:
                    vvar = form_vars[var]
                    if isinstance(vvar, Field):
                        # modified_by/modified_on
                        continue
                    if var == "pe_id":
                        pe_id = vvar
                    rvar = record.get(var, "NOT_PRESENT")
                    if rvar != "NOT_PRESENT" and vvar != rvar:
                        f = table[var]
                        type_ = f.type
                        if type_ == "integer" or \
                           type_.startswith("reference"):
                            if vvar:
                                vvar = int(vvar)
                            if vvar == rvar:
                                continue
                        represent = table[var].represent
                        if represent:
                            if hasattr(represent, "show_link"):
                                represent.show_link = False
                        else:
                            represent = lambda o: o
                        if rvar:
                            changed[var] = "%s changed from %s to %s" % \
                                (f.label, represent(rvar), represent(vvar))
                        else:
                            changed[var] = "%s changed to %s" % \
                                (f.label, represent(vvar))

                if changed:
                    table = s3db.event_incident_log
                    text = []
                    for var in changed:
                        text.append(changed[var])
                    text = "\n".join(text)
                    table.insert(incident_id = incident_id,
                                 name = "Task Updated",
                                 comments = text,
                                 )

        if pe_id:
            # Notify Assignee
            # @ToDo: i18n
            from gluon import URL
            message = "You have been assigned a Task: %s%s" % \
                        (settings.get_base_public_url(),
                         URL(c="event", f= "incident",
                             args = [incident_id, "task", task_id]),
                             )
            from s3db.pr import pr_instance_type
            instance_type = pr_instance_type(pe_id)
            if instance_type == "org_organisation":
                # Notify the Duty Number for the Organisation, not everyone in the Organisation!
                otable = s3db.org_organisation
                ottable = s3db.org_organisation_tag
                query = (otable.pe_id == pe_id) & \
                        (ottable.organisation_id == otable.id) & \
                        (ottable.tag == "duty")
                duty = db(query).select(ottable.value,
                                        limitby = (0, 1),
                                        ).first()
                if duty:
                    current.msg.send_sms_via_api(duty.value,
                                                 message,
                                                 )
            else:
                task_notification = settings.get_event_task_notification()
                if task_notification:
                    current.msg.send_by_pe_id(pe_id,
                                              subject = "%s: Task assigned to you" % settings.get_system_name_short(),
                                              message = message,
                                              contact_method = task_notification,
                                              )

    # -------------------------------------------------------------------------
    def customise_project_task_resource(r, tablename):

        s3db = current.s3db

        table = s3db.project_task
        table.source.readable = table.writable = False

        # Search Persons for assignments, with the extra data that pr_search_ac returns
        from s3 import S3PersonAutocompleteWidget
        table.pe_id.widget = S3PersonAutocompleteWidget(field = "pe_id")

        s3db.configure(tablename,
                       # No need to see time log: KISS
                       crud_form = None,
                       # NB We deliberatly over-ride the default one
                       create_onaccept = project_task_onaccept,
                       # In event_ActionPlan()
                       #list_fields = ["priority",
                       #               "name",
                       #               "pe_id",
                       #               "status_id",
                       #               "date_due",
                       #               ],
                       update_onaccept = lambda form:
                                            project_task_onaccept(form, create=False),
                       )

    settings.customise_project_task_resource = customise_project_task_resource

    # -------------------------------------------------------------------------
    def customise_supply_catalog_item_resource(r, tablename):

        from s3 import S3Represent

        s3db = current.s3db

        represent = S3Represent(lookup = "supply_item_category")
        s3db.supply_catalog_item.item_category_id.represent = represent
        s3db.supply_item_category.parent_item_category_id.represent = represent

        list_fields = [(T("Item Name"), "item_id$name"),
                       (T("Item Category"), "item_category_id$parent_item_category_id"),
                       (T("Item Sub-category"), "item_category_id"),
                       (T("Base UoM"), "item_id$um"),
                       (T("Brand"), "item_id$brand"),
                       ]

        s3db.configure(tablename,
                       list_fields = list_fields,
                       )

    settings.customise_supply_catalog_item_resource = customise_supply_catalog_item_resource

# END =========================================================================
