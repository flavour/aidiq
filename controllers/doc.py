# -*- coding: utf-8 -*-

"""
    Document Library - Controllers
"""

if not settings.has_module(c):
    raise HTTP(404, body="Module disabled: %s" % c)

# =============================================================================
def index():
    "Module's Home Page"

    module_name = settings.modules[c].get("name_nice")
    response.title = module_name
    return {"module_name": module_name}

# =============================================================================
def card_config():

    return s3_rest_controller()

# =============================================================================
def document():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        if r.method in ("create", "create.popup"):
            doc_id = get_vars.get("~.doc_id", None)
            if doc_id:
                # Coming from Profile page
                s3db.doc_document.doc_id.default = doc_id

        return True
    s3.prep = prep

    return s3_rest_controller(rheader = document_rheader)

# -----------------------------------------------------------------------------
def document_rheader(r):
    if r.representation == "html":
        doc_document = r.record
        if doc_document:
            #rheader_tabs = s3_rheader_tabs(r, document_tabs(r))
            table = db.doc_document
            rheader = DIV(B("%s: " % T("Name")), doc_document.name,
                        TABLE(TR(
                                TH("%s: " % T("File")), table.file.represent(doc_document.file),
                                TH("%s: " % T("URL")), table.url.represent(doc_document.url),
                                ),
                                TR(
                                TH("%s: " % ORGANISATION), table.organisation_id.represent(doc_document.organisation_id),
                                TH("%s: " % T("Person")), table.person_id.represent(doc_document.organisation_id),
                                ),
                            ),
                        #rheader_tabs
                        )
            return rheader
    return None

# -----------------------------------------------------------------------------
def document_tabs(r):
    """
        Display the number of Components in the tabs
        - currently unused as we don't have these tabs off documents
    """

    tab_opts = [{"tablename": "assess_rat",
                 "resource": "rat",
                 "one_title": "1 Assessment",
                 "num_title": " Assessments",
                },
                {"tablename": "irs_ireport",
                 "resource": "ireport",
                 "one_title": "1 Incident Report",
                 "num_title": " Incident Reports",
                },
                {"tablename": "cr_shelter",
                 "resource": "shelter",
                 "one_title": "1 Shelter",
                 "num_title": " Shelters",
                },
                #{"tablename": "flood_freport",
                # "resource": "freport",
                # "one_title": "1 Flood Report",
                # "num_title": " Flood Reports",
                #},
                {"tablename": "inv_req",
                 "resource": "req",
                 "one_title": "1 Request",
                 "num_title": " Requests",
                },
                ]
    tabs = [(T("Details"), None)]
    from s3 import S3CRUD
    crud_string = S3CRUD.crud_string
    for tab_opt in tab_opts:
        tablename = tab_opt["tablename"]
        if tablename in db and document_id in db[tablename]:
            table = db[tablename]
            query = (table.deleted == False) & \
                    (table.document_id == r.id)
            tab_count = db(query).count()
            if tab_count == 0:
                label = crud_string(tablename, "label_create")
            elif tab_count == 1:
                label = tab_opt["one_title"]
            else:
                label = T(str(tab_count) + tab_opt["num_title"] )
            tabs.append( (label, tab_opt["resource"] ) )

    return tabs

# =============================================================================
def image():
    """ RESTful CRUD controller """

    # Pre-processor
    def prep(r):
        # Location Filter
        from s3db.gis import gis_location_filter
        gis_location_filter(r)

        if r.method in ("create", "create.popup"):
            doc_id = get_vars.get("~.doc_id", None)
            if doc_id:
                # Coming from Profile page
                s3db.doc_image.doc_id.default = doc_id

        return True
    s3.prep = prep

    return s3_rest_controller()

# =============================================================================
def bulk_upload():
    """
        Custom view to allow bulk uploading of Photos

        @ToDo: Allow creation of a GIS Feature Layer to view on the map
        @ToDo: Allow uploading of associated GPX track for timestamp correlation.
        See r1595 for the previous draft of this work
    """

    s3.stylesheets.append("plugins/fileuploader.css")
    return {}

def upload_bulk():
    """
        Receive the Uploaded data from bulk_upload()

        https://github.com/valums/file-uploader/blob/master/server/readme.txt

        @ToDo: Read EXIF headers to geolocate the Photos
    """

    tablename = "doc_image"
    table = s3db[tablename]

    import cgi

    source = request.post_vars.get("qqfile", None)
    if isinstance(source, cgi.FieldStorage) and source.filename:
        # For IE6-8, Opera, older versions of other browsers you get the file as you normally do with regular form-base uploads.
        name = source.filename
        image = source.file

    else:
        # For browsers which upload file with progress bar, you will need to get the raw post data and write it to the file.
        if "name" in request.vars:
            name = request.vars.name
        else:
            HTTP(400, "Invalid Request: Need a Name!")

        image = request.body.read()
        # Convert to StringIO for onvalidation/import
        from io import StringIO
        image = StringIO(image)
        source = Storage()
        source.filename = name
        source.file = image

    form = SQLFORM(table)
    vars = Storage()
    vars.name = name
    vars.image = source
    vars._formname = "%s_create" % tablename

    # onvalidation callback
    onvalidation = s3db.get_config(tablename, "create_onvalidation",
                   s3db.get_config(tablename, "onvalidation"))

    if form.accepts(vars, onvalidation=onvalidation):
        msg = Storage(success = True)
        # onaccept callback
        onaccept = s3db.get_config(tablename, "create_onaccept",
                   s3db.get_config(tablename, "onaccept"))
        from gluon.tools import callback
        callback(onaccept, form) # , tablename=tablename (if we ever define callbacks as a dict with tablename)
    else:
        error_msg = ""
        for error in form.errors:
            error_msg = "%s\n%s:%s" % (error_msg, error, form.errors[error])
        msg = Storage(error = error_msg)

    response.headers["Content-Type"] = "text/html"  # This is what the file-uploader widget expects
    return json.dumps(msg)

# =============================================================================
def ck_upload():
    """
        Controller to handle uploads to CKEditor

        https://ckeditor.com/docs/ckeditor4/latest/guide/dev_file_upload.html

        Originally based on https://github.com/timrichardson/web2py_ckeditor4
    """

    # Assumed by presence of post_vars
    #if request.method != "POST":
    #    raise HTTP(405, "Only POST supported.")

    post_vars = request.post_vars

    upload = post_vars.upload

    if upload is None:
        raise HTTP(401, "Missing required upload.")

    if not hasattr(upload, "file"):
        raise HTTP(401, "Upload is not a file")

    if post_vars.get("ckCsrfToken") != request.cookies["ckCsrfToken"].value:
        raise HTTP(401, "CSRF failure")

    os_path = os.path

    path = os_path.join(request.folder, "uploads")

    # Load Model
    table = s3db.doc_ckeditor

    form = SQLFORM.factory(Field("upload", "upload",
                                 requires = IS_NOT_EMPTY(),
                                 #uploadfs = self.settings.uploadfs,
                                 uploadfolder = path,
                                 ),
                           table_name = "doc_ckeditor",
                           )

    old_filename = upload.filename
    new_filename = table.upload.store(upload.file,
                                      upload.filename)
    #if self.settings.uploadfs:
    #    length = self.settings.uploadfs.getsize(new_filename)
    #else:
    length = os_path.getsize(os_path.join(path, new_filename))

    mime_type = upload.headers["content-type"]

    title = os_path.splitext(old_filename)[0]

    result = table.validate_and_insert(title = title,
                                       filename = old_filename,
                                       upload = new_filename,
                                       flength = length,
                                       mime_type = mime_type,
                                       )

    url = URL(c = "default",
              f = "download",
              args = [new_filename],
              )

    output = {"uploaded": 1,
              "fileName": old_filename,
              "url": url,
              }
    if not result.id:
        output["errors"] = {"message": result.errors,
                            }

    from s3 import SEPARATORS
    response.headers["Content-Type"] = "application/json"
    return json.dumps(output, separators=SEPARATORS)

# -----------------------------------------------------------------------------
def ck_browse():
    """
        Controller to view files uploaded to CKEditor by this User

        https://ckeditor.com/docs/ckeditor4/latest/guide/dev_file_browser_api.html
    """

    table = s3db.doc_ckeditor

    if auth.s3_has_role("ADMIN"):
        query = (table.deleted == False)
    else:
        # @ToDo: More detailed permissions?
        query = (table.owned_by_user == auth.user.id)

    rows = db(query).select(table.title,
                            table.filename,
                            table.upload,
                            orderby = table.title,
                            )

    return {"rows": rows,
            "ckfuncnum": get_vars.CKEditorFuncNum,
            }

# -----------------------------------------------------------------------------
def ck_delete():
    """
        Controller to handle deletes in CKEditor
    """

    try:
        filename = request.args[0]
    except:
        raise HTTP(401, "Required argument filename missing.")

    if auth.s3_has_role("ADMIN"):
        db(s3db.doc_ckeditor.upload == filename).delete()
    else:
        table = s3db.doc_ckeditor
        record = db(table.upload == filename).select(table.id,
                                                     table.owned_by_user,
                                                     limitby = (0, 1),
                                                     ).first()
        if record and \
           record.owned_by_user == auth.user.id:
            db(table.id == record.id).delete()

# END =========================================================================
