# -*- coding: utf-8 -*-

import os

from copy import deepcopy
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT#, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, \
                               Image, \
                               Paragraph, \
                               Table

from gluon import *
from gluon.contenttype import contenttype

from s3 import NONE, S3GroupedItems, S3GroupedItemsTable
from s3.s3export import S3Exporter

from .layouts import OM

# Names of Orgs with specific settings
HNRC = "Honduran Red Cross"

# GRN Form
def inv_recv_form(r, **attr):
    if current.auth.root_org_name() == HNRC:
        return grn_hnrc(r, **attr)
    else:
        #return grn_S3html2pdf(r, **attr)
        return grn(r, **attr)

# Waybill Form
def inv_send_form(r, **attr):
    #if current.auth.root_org_name() == HNRC:
    #    return waybill_hnrc(r, **attr)
    #else:
    return waybill(r, **attr)

# Requests Form
def inv_req_form(r, **attr):

    T = current.T

    # Master record (=inv_req)
    resource = current.s3db.resource(r.tablename,
                                     id = r.id,
                                     components = ["req_item"],
                                     )

    # Columns and data for the form header
    header_fields = ["req_ref",
                     "date",
                     "date_required",
                     (T("Deliver to"), "site_id"),
                     (T("Reason for Request"), "purpose"),
                     "requester_id",
                     "site_id$site_id:inv_warehouse.contact",
                     "comments",
                     ]

    header_data = resource.select(header_fields,
                                  start = 0,
                                  limit = 1,
                                  represent = True,
                                  show_links = False,
                                  raw_data = True,
                                  )
    if not header_data:
        r.error(404, current.ERROR.BAD_RECORD)

    # Generate PDF header
    row = header_data.rows[0]
    labels = {rfield.colname: rfield.label for rfield in header_data.rfields}

    def row_(left, right):
        return header_row_(left, right, row=row, labels=labels)

    # Get organisation name and logo
    name, logo = OM().render()

    # The title
    title = H2(T("Logistics Requisition"))

    # Waybill details
    dtable = TABLE(TR(TD(DIV(logo,
                             H4(name),
                             ),
                         _colspan = 2,
                         ),
                      TD(DIV(title),
                         _colspan = 2,
                         ),
                      ),
                   row_("inv_req.req_ref", None),
                   row_("inv_req.date", "inv_req.date_required"),
                   row_("inv_req.site_id", "inv_req.purpose"),
                   row_("inv_req.requester_id", "inv_warehouse.contact"),
                   )

    # Waybill comments
    ctable = TABLE(TR(TH(T("Comments"))),
                   TR(TD(row["inv_req.comments"])),
                   )

    pdf_header = DIV(dtable,
                     P("&nbsp;"),
                     ctable,
                     )

    # Filename from send_ref
    header_row = header_data.rows[0]
    pdf_filename = header_row["_row"]["inv_req.req_ref"]

    # Component (=req_item)
    component = resource.components["req_item"]
    body_fields = ["item_id",
                   "item_pack_id",
                   "quantity",
                   "comments",
                   ]

    # Aggregate methods and column names
    aggregate = [("sum", "inv_req_item.quantity"),
                 ]

    # Generate the JSON data dict
    json_data = json_data_(component,
                           body_fields,
                           aggregate = aggregate,
                           )

    # Generate the grouped items table
    output = S3GroupedItemsTable(component,
                                 data = json_data,
                                 totals_label = T("Total"),
                                 title = T("Logistics Requisition"),
                                 pdf_header = pdf_header,
                                 pdf_footer = inv_req__footer,
                                 )

    # ...and export it as PDF
    return output.pdf(r, filename=pdf_filename)

# -----------------------------------------------------------------------------
def header_row_(left, right, row=None, labels=None):
    """
        Helper function to generate a 2-column table row
        for the PDF header

        @param left: the column name for the left column
        @param right: the column name for the right column,
                      or None for an empty column
        @param row: the S3ResourceData row
        @param labels: dict of labels {colname: label}
    """

    if right:
        header_row = TR(TH(labels[left]),
                        TD(row[left]),
                        TH(labels[right]),
                        TD(row[right]),
                        )
    else:
        header_row = TR(TH(labels[left]),
                        TD(row[left],
                           _colspan = 3,
                           ),
                        )
    return header_row

# -----------------------------------------------------------------------------
def json_data_(component, list_fields, aggregate=None):
    """
        Extract, group and aggregate the data for the form body

        @param component: the component (S3Resource)
        @param list_fields: the columns for the form body
                            (list of field selectors)
        @param aggregate: aggregation methods and fields,
                          a list of tuples (method, column name)
    """

    # Extract the data
    data = component.select(list_fields,
                            limit = None,
                            raw_data = True,
                            represent = True,
                            show_links = False,
                            )

    # Get the column names and labels
    columns = []
    append_column = columns.append
    labels = {}
    for rfield in data.rfields:
        colname = rfield.colname
        append_column(colname)
        labels[colname] = rfield.label

    # Group and aggregate the items
    gi = S3GroupedItems(data.rows,
                        aggregate = aggregate,
                        )

    # Convert into JSON-serializable dict for S3GroupedItemsTable
    json_data = gi.json(fields = columns,
                        labels = labels,
                        as_dict = True,
                        )

    return json_data

# -----------------------------------------------------------------------------
def inv_req__footer(r):

    from s3db.pr import pr_PersonRepresent
    from s3db.inv import inv_req_approvers

    T = current.T

    header = TR(TH("&nbsp;"),
                TH(T("Name")),
                TH(T("Signature")),
                TH(T("Date")),
                )

    record = r.record
    requester = record.requester_id
    approvers = inv_req_approvers(record.site_id)
    person_ids = [requester] + list(approvers)

    names = pr_PersonRepresent().bulk(person_ids)

    signature_rows = [TR(TH(T("Requester")),
                         TD(names[requester]),
                         )]
    append = signature_rows.append

    for approver in approvers:
        append(TR(TH(approvers[approver]["title"]),
                  TD(names[approver]),
                  ))

    return TABLE(header,
                 *signature_rows
                 )

# =============================================================================
def grn(r, **attr):
    """
        GRN (Goods Received Note) for French Red Cross (& current default)

        Using ReportLab's PLATYPUS direct

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    # Styles
    styleSheet = getSampleStyleSheet()

    style = styleSheet["Normal"]
    style.fontName = "Helvetica"
    style.fontSize = 9

    style_center = deepcopy(style)
    style_center.alignment = TA_CENTER

    style_right = deepcopy(style)
    style_right.alignment = TA_RIGHT

    style_6_center = deepcopy(style_center)
    style_6_center.fontSize = 6

    style_7_center = deepcopy(style_center)
    style_7_center.fontSize = 7

    style_8_center = deepcopy(style_center)
    style_8_center.fontSize = 8

    style_8_right = deepcopy(style_8_center)
    style_8_right.alignment = TA_RIGHT

    style_12_center = deepcopy(style_center)
    style_12_center.fontSize = 12

    style_18_center = deepcopy(style_center)
    style_18_center.fontSize = 18

    size = current.deployment_settings.get_pdf_size()
    if size == "Letter":
        pagesize = landscape(LETTER)
    elif size == "A4" or not isinstance(size, tuple):
        pagesize = landscape(A4)
    else:
        pagesize = landscape(size)

    db = current.db
    s3db = current.s3db

    # Master record
    recv_table = s3db.inv_recv
    record = r.record
    recv_ref = record.recv_ref
    date = recv_table.date.represent(record.date)
    from_site_id = record.from_site_id
    if from_site_id:
        received_from = recv_table.from_site_id.represent(from_site_id,
                                                          show_link = False,
                                                          )
    else:
        received_from = recv_table.organisation_id.represent(record.organisation_id,
                                                             show_link = False,
                                                             )

    # Get organisation logo
    stable = s3db.org_site
    site = db(stable.site_id == record.site_id).select(stable.organisation_id,
                                                       limitby = (0, 1),
                                                       ).first()
    organisation_id = site.organisation_id

    from s3db.org import org_root_organisation_name
    recipient_ns = org_root_organisation_name(organisation_id)

    otable = s3db.org_organisation
    org = db(otable.id == organisation_id).select(otable.logo,
                                                  otable.root_organisation,
                                                  limitby = (0, 1),
                                                  ).first()
    logo = org.logo
    if not logo:
        root_organisation = org.root_organisation
        if organisation_id != root_organisation:
            org = db(otable.id == root_organisation).select(otable.logo,
                                                            limitby = (0, 1),
                                                            ).first()
            logo = org.logo

    if logo:
        src = os.path.join(r.folder,
                           "uploads",
                           logo,
                           )
    else:
        # Use default IFRC
        src = os.path.join(r.folder,
                           "static",
                           "themes",
                           "RMS",
                           "img",
                           "logo_small.png",
                           )

    logo = Image(src)

    # Assuming 96dpi original resolution
    resolution = 96
    iwidth = logo.drawWidth
    iheight = logo.drawHeight
    height = 50 * inch / resolution
    width = iwidth * (height / iheight)
    logo.drawHeight = height
    logo.drawWidth = width

    output = BytesIO()
    doc = SimpleDocTemplate(output,
                            title = recv_ref,
                            pagesize = pagesize,
                            leftMargin = 0.3 * inch,
                            rightMargin = 0.3 * inch,
                            topMargin = 0.5 * inch,
                            bottomMargin = 0.5 * inch,
                            )

    lightgrey = colors.lightgrey
    table_style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                   ("SPAN", (0, 0), (5, 0)),
                   ("SPAN", (7, 0), (8, 0)),
                   ("BACKGROUND", (6, 0), (8, 0), lightgrey),
                   ("SPAN", (0, 1), (5, 1)),
                   ("SPAN", (7, 1), (8, 1)),
                   ("SPAN", (0, 3), (1, 3)),
                   ("SPAN", (2, 3), (3, 3)),
                   ("SPAN", (4, 3), (6, 3)),
                   ("SPAN", (7, 3), (8, 3)),
                   ("BACKGROUND", (0, 3), (0, 3), lightgrey),
                   ("BACKGROUND", (4, 3), (4, 3), lightgrey),
                   ("SPAN", (2, 5), (3, 5)),
                   ("SPAN", (5, 5), (6, 5)),
                   ("SPAN", (7, 5), (8, 5)),
                   ("BACKGROUND", (0, 5), (0, 5), lightgrey),
                   ("BACKGROUND", (2, 5), (3, 5), lightgrey),
                   ("BACKGROUND", (5, 5), (6, 5), lightgrey),
                   ("SPAN", (0, 7), (0, 10)),
                   ("SPAN", (5, 7), (6, 7)),
                   ("SPAN", (5, 8), (6, 8)),
                   ("SPAN", (5, 9), (6, 9)),
                   ("SPAN", (7, 7), (8, 7)),
                   ("SPAN", (7, 8), (8, 8)),
                   ("SPAN", (7, 9), (8, 9)),
                   ("BACKGROUND", (0, 7), (1, 10), lightgrey),
                   ("BACKGROUND", (5, 7), (6, 9), lightgrey),
                   ("SPAN", (0, 12), (3, 12)),
                   ("SPAN", (4, 12), (6, 12)),
                   ("SPAN", (1, 13), (2, 13)),
                   ("SPAN", (7, 12), (7, 13)),
                   ("SPAN", (8, 12), (8, 13)),
                   ("BACKGROUND", (0, 12), (8, 13), lightgrey),
                   ]
    sappend = table_style.append

    spacer = ["",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              "",
              ]

    content = [
               # Row 0
               [logo,
                "",
                "",
                "",
                "",
                "",
                Paragraph(str(B("COUNTRY CODE")), style_center),
                Paragraph(str(B("GRN NUMBER")), style_center),
                "",
                ],
               # Row 1
               [Paragraph("%s / %s" % (B("GOODS RECEIVED NOTE"),
                                       I("Accusé de Réception"),
                                       ), style_18_center),
                "",
                "",
                "",
                "",
                "",
                "", # @ToDo: Country Code?
                Paragraph(str(B(recv_ref)), style_12_center),
                "",
                ],
               # Row 2
               spacer,
               # Row 3
               [Paragraph("%s<br/>(%s)" % (B("DELEGATION/CONSIGNEE"),
                                           B("LOCATION"),
                                           ), style_right),
                "",
                Paragraph(recipient_ns, style_8_center),
                "",
                Paragraph("%s / %s" % (B("RECEIVED FROM"),
                                       I("reçu de"),
                                       ), style_center),
                "",
                "",
                Paragraph(received_from, style_center),
                "",
                ],
               # Row 4
               spacer,
               # Row 5
               [Paragraph("%s<br/>%s" % (B("DATE OF ARRIVAL"),
                                         I("Date de réception"),
                                         ), style_right),
                Paragraph(date, style_center),
                Paragraph(str(B("DOCUMENT WELL RECEIVED")), style_center),
                "",
                "",
                Paragraph(str(B("IF NO, PLEASE SPECIFY")), style_center),
                "",
                "",
                "",
                ],
               # Row 6
               spacer,
               # Row 7
               [Paragraph("%s<br/>%s" % (B("MEANS OF TRANSPORT"),
                                         I("Moyen de transport"),
                                         ), style_center),
                Paragraph(str(B("Air")), style_right),
                "", # @ToDo: Checkbox
                Paragraph(str(B("AWB n°:")), style),
                "",
                Paragraph(str(B("FLIGHT N°")), style_right),
                "",
                "",
                "",
                ],
               # Row 8
               ["",
                Paragraph(str(B("Road")), style_right),
                "", # @ToDo: Checkbox
                Paragraph(str(B("Waybill n°/ CMR n°:")), style),
                "",
                Paragraph(str(B("REGISTRATION N°")), style_right),
                "",
                "",
                "",
                ],
               # Row 9
               ["",
                Paragraph(str(B("Sea")), style_right),
                "", # @ToDo: Checkbox
                Paragraph(str(B("B/L n°:")), style),
                "",
                Paragraph(str(B("VESSEL")), style_right),
                "",
                "",
                "",
                ],
               # Row 10
               ["",
                Paragraph("Handcarried by", style_8_right),
                "", # @ToDo: Checkbox
                Paragraph(str(B("Waybill n°:")), style),
                "",
                "",
                "",
                "",
                "",
                ],
               # Row 11
               spacer,
               # Row 12
               [Paragraph("%s / %s" % (B("GOODS RECEIVED"),
                                       I("Marchandises reçues"),
                                       ), style_7_center),
                "",
                "",
                "",
                Paragraph(str(I("FOR FOOD INDICATE NET WEIGHT")), style_7_center),
                "",
                "",
                Paragraph("%s<br/>%s" % (B("RECEIVED ACCORDING TO DOCUMENT AND RECEIVED IN GOOD CONDITIONS"),
                                         I("Reçu selon documents et en bonne condition"),
                                         ), style_7_center),

                Paragraph("%s<br/>%s" % (B("CLAIM"),
                                         I("Réclamation"),
                                         ), style_7_center),
                ],
               # Row 13
               [Paragraph("%s<br/>%s" % (B("ITEMS CODE"),
                                         I("Description générale et remarques"),
                                         ), style_6_center),
                Paragraph("%s<br/>%s" % (B("DESCRIPTION"),
                                         I("Code article"),
                                         ), style_6_center),
                "",
                Paragraph(str(B("COMMODITY TRACKING N° OR DONOR")), style_7_center),
                Paragraph("%s<br/>%s" % (B("NB. OF UNITS"),
                                         I("nb. colis"),
                                         ), style_6_center),
                Paragraph("%s<br/>%s" % (B("UNIT TYPE/WEIGHT"),
                                         I("type d'unité/poids"),
                                         ), style_6_center),
                Paragraph("%s<br/>%s" % (B("WEIGHT (kg)"),
                                         I("Total (kg)"),
                                         ), style_6_center),
                "",
                "",
                ],
               ]
    cappend = content.append

    rowHeights = [1.64 * cm,
                  1.16 * cm,
                  0.16 * cm,
                  0.82 * cm,
                  0.21 * cm,
                  1.06 * cm,
                  0.25 * cm,
                  0.56 * cm,
                  0.56 * cm,
                  0.56 * cm,
                  0.56 * cm,
                  0.24 * cm,
                  0.40 * cm,
                  0.85 * cm,
                  ]
    rappend = rowHeights.append

    # Received Items
    ttable = s3db.inv_track_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    query = (ttable.recv_id == record.id) & \
            (ttable.item_id == itable.id) & \
            (ttable.item_pack_id == ptable.id)
    items = db(query).select(itable.code,
                             itable.name,
                             ttable.item_source_no,
                             ttable.recv_quantity,
                             ptable.name,
                             ptable.quantity,
                             itable.weight,
                             )

    rowNo = 14
    for row in items:
        item = row["supply_item"]
        pack = row["supply_item_pack"]
        track_item = row["inv_track_item"]
        quantity = track_item.recv_quantity
        pack_details = pack.name
        weight = item.weight
        if weight:
            pack_weight = weight * pack.quantity
            pack_details = "%s / %s" % (pack_details,
                                        round(pack_weight, 2),
                                        )
            total_weight = round(pack_weight * quantity, 2)
        else:
            total_weight = NONE
        body_row = [Paragraph(item.code or NONE, style_7_center),
                    Paragraph(item.name, style_7_center),
                    "",
                    Paragraph(track_item.item_source_no or NONE, style_7_center),
                    Paragraph(str(quantity), style_7_center),
                    Paragraph(pack_details, style_7_center),
                    Paragraph(str(total_weight), style_7_center),
                    "", # @ToDo: Checkbox
                    ]
        rappend(0.67 * cm)
        sappend(("SPAN", (1, rowNo), (2, rowNo)))
        cappend(body_row)
        rowNo += 1

    rowHeights += [0.32 * cm,
                   0.45 * cm,
                   2.04 * cm,
                   0.32 * cm,
                   0.39 * cm,
                   0.81 * cm,
                   0.39 * cm,
                   0.81 * cm,
                   ]

    table_style += [("SPAN", (0, rowNo + 1), (8, rowNo + 1)),
                    ("SPAN", (0, rowNo + 2), (8, rowNo + 2)),
                    ("SPAN", (2, rowNo + 4), (3, rowNo + 4)),
                    ("SPAN", (4, rowNo + 4), (6, rowNo + 4)),
                    ("SPAN", (7, rowNo + 4), (8, rowNo + 4)),
                    ("SPAN", (2, rowNo + 5), (3, rowNo + 5)),
                    ("SPAN", (4, rowNo + 5), (6, rowNo + 5)),
                    ("SPAN", (7, rowNo + 5), (8, rowNo + 5)),
                    ("SPAN", (2, rowNo + 6), (3, rowNo + 6)),
                    ("SPAN", (4, rowNo + 6), (6, rowNo + 6)),
                    ("SPAN", (7, rowNo + 6), (8, rowNo + 6)),
                    ("SPAN", (2, rowNo + 7), (3, rowNo + 7)),
                    ("SPAN", (4, rowNo + 7), (6, rowNo + 7)),
                    ("SPAN", (7, rowNo + 7), (8, rowNo + 7)),
                    ("BACKGROUND", (0, rowNo + 4), (8, rowNo + 4), lightgrey),
                    ("BACKGROUND", (0, rowNo + 6), (8, rowNo + 6), lightgrey),
                    ]

    content += [spacer,
                [Paragraph("%s / %s" % (B("COMMENTS"),
                                        I("Observations"),
                                        ), style),
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 "",
                 ],
                spacer,
                spacer,
                [Paragraph(str(B("DELIVERED BY")), style_8_center),
                 Paragraph(str(B("DATE")), style_8_center),
                 Paragraph(str(B("FUNCTION")), style_8_center),
                 "",
                 Paragraph("%s (%s)" % (B("NAME"),
                                        "IN BLOCK LETTER",
                                        ), style_8_center),
                 "",
                 "",
                 Paragraph(str(B("SIGNATURE")), style_8_center),
                 "",
                 ],
                spacer,
                [Paragraph(str(B("RECEIVED BY")), style_8_center),
                 Paragraph(str(B("DATE")), style_8_center),
                 Paragraph(str(B("FUNCTION")), style_8_center),
                 "",
                 Paragraph("%s (%s)" % (B("NAME"),
                                        "IN BLOCK LETTER",
                                        ), style_8_center),
                 "",
                 "",
                 Paragraph(str(B("SIGNATURE / STAMP")), style_8_center),
                 "",
                 ],
                spacer,
                ]

    table = Table(content,
                  colWidths = (4.17 * cm,
                               2.73 * cm,
                               1.20 * cm,
                               4.06 * cm,
                               2.29 * cm,
                               3.13 * cm,
                               2.03 * cm,
                               6.25 * cm,
                               1.33 * cm,
                               ),
                  rowHeights = rowHeights,
                  style = table_style,
                  hAlign = "LEFT",   # defaults to "CENTER"
                  vAlign = "MIDDLE", # defaults to "MIDDLE", but better to specify
                  )

    doc.build([table],
              canvasmaker = canvas.Canvas, # S3NumberedCanvas
              )

    # Return the generated PDF
    response = current.response
    if response:
        filename = "%s.pdf" % recv_ref
        if "uwsgi_scheme" in current.request.env:
            # Running uwsgi then we can't have unicode filenames
            # Accent Folding
            def string_escape(s):
                import unicodedata
                return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("utf-8")
            filename = string_escape(filename)
        disposition = 'attachment; filename="%s"' % filename
        response.headers["Content-Type"] = contenttype(".pdf")
        response.headers["Content-disposition"] = disposition

    return output.getvalue()

# =============================================================================
def waybill(r, **attr):
    """
        Waybill for HNRC

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    T = current.T
    s3db = current.s3db

    # Component declarations to distinguish between the
    # origin and destination warehouses
    s3db.add_components("inv_send",
                        inv_warehouse = ({"name": "origin",
                                          "joinby": "site_id",
                                          "pkey": "site_id",
                                          "filterby": False,
                                          "multiple": False,
                                          },
                                         {"name": "destination",
                                          "joinby": "site_id",
                                          "pkey": "to_site_id",
                                          "filterby": False,
                                          "multiple": False,
                                          },
                                         ),
                        )

    # Master record (=inv_send)
    resource = s3db.resource(r.tablename,
                             id = r.id,
                             components = ["origin",
                                           "destination",
                                           "track_item",
                                           ],
                             )

    # Columns and data for the form header
    header_fields = ["send_ref",
                     # @ToDo: Will ned updating to use inv_send_req
                     #"req_ref",
                     "date",
                     "delivery_date",
                     (T("Origin"), "site_id"),
                     (T("Destination"), "to_site_id"),
                     "sender_id",
                     "origin.contact",
                     "recipient_id",
                     "destination.contact",
                     "transported_by",
                     "transport_ref",
                     (T("Delivery Address"), "destination.location_id"),
                     "comments",
                     ]

    header_data = resource.select(header_fields,
                                  start = 0,
                                  limit = 1,
                                  represent = True,
                                  show_links = False,
                                  raw_data = True,
                                  )
    if not header_data:
        r.error(404, current.ERROR.BAD_RECORD)

    # Generate PDF header
    row = header_data.rows[0]
    labels = {rfield.colname: rfield.label for rfield in header_data.rfields}
    def row_(left, right):
        return header_row_(left, right, row=row, labels=labels)

    # Get organisation name and logo
    name, logo = OM().render()

    # The title
    title = H2(T("Waybill"))

    # Waybill details
    dtable = TABLE(TR(TD(DIV(logo,
                             H4(name),
                             ),
                         _colspan = 2,
                         ),
                      TD(DIV(title),
                         _colspan = 2,
                         ),
                      ),
                   # @ToDo: Will ned updating to use inv_send_req
                   row_("inv_send.send_ref", None
                        #"inv_send.req_ref",
                        ),
                   row_("inv_send.date", "inv_send.delivery_date"),
                   row_("inv_send.site_id", "inv_send.to_site_id"),
                   row_("inv_send.sender_id", "inv_send.recipient_id"),
                   row_("inv_origin_warehouse.contact",
                        "inv_destination_warehouse.contact",
                        ),
                   row_("inv_send.transported_by", "inv_send.transport_ref"),
                   row_("inv_destination_warehouse.location_id", None),
                   )

    # Waybill comments
    ctable = TABLE(TR(TH(T("Comments"))),
                   TR(TD(row["inv_send.comments"])),
                   )

    pdf_header = DIV(dtable,
                     P("&nbsp;"),
                     ctable,
                     )

    # Filename from send_ref
    header_row = header_data.rows[0]
    pdf_filename = header_row["_row"]["inv_send.send_ref"]

    # Component (=inv_track_item)
    component = resource.components["track_item"]
    body_fields = ["item_id",
                   "item_pack_id",
                   "quantity",
                   (T("Total Volume (m3)"), "total_volume"),
                   (T("Total Weight (kg)"), "total_weight"),
                   "supply_org_id",
                   "inv_item_status",
                   ]
    # Any extra fields needed for virtual fields
    component.configure(extra_fields = ["item_id$weight",
                                        "item_id$volume",
                                        ],
                        )

    # Aggregate methods and column names
    aggregate = [("sum", "inv_track_item.quantity"),
                 ("sum", "inv_track_item.total_volume"),
                 ("sum", "inv_track_item.total_weight"),
                 ]

    # Generate the JSON data dict
    json_data = json_data_(component,
                           body_fields,
                           aggregate = aggregate,
                           )

    # Generate the grouped items table
    output = S3GroupedItemsTable(component,
                                 data = json_data,
                                 totals_label = T("Total"),
                                 title = T("Waybill"),
                                 pdf_header = pdf_header,
                                 pdf_footer = waybill_footer,
                                 )

    # ...and export it as PDF
    return output.pdf(r, filename=pdf_filename)

# -----------------------------------------------------------------------------
def waybill_footer(r):
    """
        Footer for Waybills for HNRC

        @param r: the S3Request
    """

    T = current.T

    return TABLE(TR(TH(T("Shipment")),
                    TH(T("Date")),
                    TH(T("Function")),
                    TH(T("Name")),
                    TH(T("Signature")),
                    TH(T("Status")),
                    ),
                 TR(TD(T("Sent by"))),
                 TR(TD(T("Transported by"))),
                 TR(TH(T("Received by")),
                    TH(T("Date")),
                    TH(T("Function")),
                    TH(T("Name")),
                    TH(T("Signature")),
                    TH(T("Status")),
                    ),
                 TR(TD("&nbsp;")),
                 )

# -------------------------------------------------------------------------
def grn_S3html2pdf(r, **attr):
    """
        GRN (Goods Received Note) for French Red Cross (& current default)

        Using S3html2pdf to convert gluon.html TABLE

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    # Not translated (has both English & French elements within)
    #T = current.T
    db = current.db
    s3db = current.s3db

    # Master record
    table = s3db.inv_recv
    record = r.record
    recv_ref = record.recv_ref
    from_site_id = record.from_site_id
    if from_site_id:
        received_from = table.from_site_id.represent(from_site_id)
    else:
        received_from = table.organisation_id.represent(record.organisation_id)

    # Get organisation logo
    stable = s3db.org_site
    site = db(stable.site_id == record.site_id).select(stable.organisation_id,
                                                       limitby = (0, 1),
                                                       ).first()
    organisation_id = site.organisation_id

    otable = s3db.org_organisation
    org = db(otable.id == organisation_id).select(otable.logo,
                                                  otable.root_organisation,
                                                  limitby = (0, 1),
                                                  ).first()
    logo = org.logo
    if not logo:
        root_organisation = org.root_organisation
        if organisation_id != root_organisation:
            org = db(otable.id == root_organisation).select(otable.logo,
                                                            limitby = (0, 1),
                                                            ).first()
            logo = org.logo

    if logo:
        logo = URL(c="default", f="download",
                   args = logo,
                   )
    else:
        # Use default IFRC
        logo = "/%s/static/themes/RMS/img/logo_small.png" % r.application

    # Received Items
    ttable = s3db.inv_track_item
    itable = s3db.supply_item
    ptable = s3db.supply_item_pack
    query = (ttable.recv_id == record.id) & \
            (ttable.item_id == itable.id) & \
            (ttable.item_pack_id == ptable.id)
    items = db(query).select(itable.code,
                             itable.name,
                             ttable.item_source_no,
                             ttable.recv_quantity,
                             ptable.name,
                             ptable.quantity,
                             itable.weight,
                             )

    body = TABLE()
    bappend = body.append

    for row in items:
        item = row["supply_item"]
        pack = row["supply_item_pack"]
        track_item = row["inv_track_item"]
        quantity = track_item.recv_quantity
        pack_details = pack.name
        weight = item.weight
        if weight:
            pack_weight = weight * pack.quantity
            pack_details = "%s / %s" % (pack_details,
                                        round(pack_weight, 2),
                                        )
            total_weight = round(pack_weight * quantity, 2)
        else:
            total_weight = NONE
        body_row = TR(TD(item.code or NONE),
                      TD(item.name),
                      TD(track_item.item_source_no or NONE),
                      TD(quantity),
                      TD(pack_details),
                      TD(total_weight),
                      )
        bappend(body_row)

    #styles = {}

    def pdf_header(r):
        return DIV(TABLE(TR(TD(IMG(_src = logo,
                                   _height = 50,
                                   ),
                               _colspan = 6,
                               ),
                            TH("COUNTRY CODE",
                               _align = "center",
                               _valign = "middle",
                               ),
                            TH("GRN NUMBER",
                               _align = "center",
                               _valign = "middle",
                               _colspan = 2,
                               ),
                            ),
                         TR(TD(B("GOODS RECEIVED NOTE"),
                               I(" / %s" % "Accusé de Réception"),
                               _align = "center",
                               _colspan = 6,
                               ),
                            TD(""), # @ToDo: Country Code?
                            TD(B(recv_ref),
                               _align = "center",
                               _colspan = 2,
                               ),
                            ),
                         TR(TH("%s\n(%s)" % ("DELEGATION/CONSIGNEE",
                                             "LOCATION",
                                             ),
                               _align = "right",
                               _colspan = 2,
                               ),
                            TD("", # @ToDo: Recipient NS
                               _align = "center",
                               _colspan = 2,
                               ),
                            TH("RECEIVED FROM",
                               I(" / %s" % "reçu de"),
                               _align = "center",
                               _colspan = 3,
                               ),
                            TD(received_from,
                               _align = "center",
                               _colspan = 2,
                               ),
                            ),
                         TR(TD("",
                               _colspan = 9,
                               ),
                            ),
                         TR(TH("DATE OF ARRIVAL",
                               I("\n%s" % "Date de réception"),
                               _align = "right",
                               ),
                            TD(table.date.represent(record.date),
                               _align = "center",
                               ),
                            TH("DOCUMENT WELL RECEIVED",
                               _align = "center",
                               _colspan = 2,
                               ),
                            TD("", # Leave Blank?
                               ),
                            TH("IF NO, PLEASE SPECIFY",
                               _align = "center",
                               _colspan = 2,
                               ),
                            TD("", # Leave Blank?
                               _colspan = 2,
                               ),
                            ),
                         TR(TD("",
                               _colspan = 9,
                               ),
                            ),
                         TR(TH("MEANS OF TRANSPORT",
                               I("\n%s" % "Moyen de transport"),
                               _align = "center",
                               ),
                            TH("ROAD",
                               "\n",
                               "AIR",
                               "\n",
                               "SEA",
                               "\n",
                               "Handcarried",
                               _align = "right",
                               ),
                            # @ToDo Checkboxes
                            TD(TABLE(TR(TD("")),
                                     TR(TD("")),
                                     TR(TD("")),
                                     TR(TD("")),
                                     ),
                               ),
                            TD(TABLE(TR(TD("AWB no:")),
                                     TR(TD("Waybill n°/ CMR n°:")),
                                     TR(TD("B/L n°:")),
                                     TR(TD("Waybill No.:")),
                                     ),
                               _colspan = 2,
                               ),
                            TD(TABLE(TR(TH("FLIGHT N°:"),
                                        TD(""),
                                        ),
                                     TR(TH("REGISTRATION N°:"),
                                        TD(""),
                                        ),
                                     TR(TH("VESSEL:"),
                                        TD(""),
                                        ),
                                     ),
                               _colspan = 4,
                               ),
                            ),
                         ))

    def pdf_body(r):
        #TABLE(TR(TH("GOODS RECEIVED",
                                   #      I("/ %s" % "Marchandises reçues"),
                                   #      _colpsan = 3,
                                   #      ),
                                   #   TH("FOR FOOD INDICATE NET WEIGHT",
                                   #      _colpsan = 3,
                                   #      ),
                                   #   ),
        body.insert(0, TR(TH("ITEMS CODE",
                             "\n",
                             I("Description générale et remarques"),
                             ),
                          TH("DESCRIPTION",
                             "\n",
                             I("Code article"),
                             ),
                          TH("COMMODITY TRACKING N° OR DONOR",
                             ),
                          TH("NB. OF UNITS",
                             "\n",
                             I("nb. colis"),
                             ),
                          TH("UNIT TYPE/WEIGHT",
                             "\n",
                             I("type d'unité/poids"),
                             ),
                          TH("WEIGHT (kg)",
                             "\n",
                             I("Total (kg)"),
                             ),
                          TH(B("RECEIVED ACCORDING TO DOCUMENT AND RECEIVED IN GOOD CONDITIONS"),
                             I("\n%s" % "Reçu selon documents et en bonne condition"),
                             ),
                          TH(B("CLAIM"),
                             I("\n%s" % "Réclamation"),
                             ),
                          ),
                    )

        bappend(TR(TD(B("COMMENTS"),
                      I(" / %s" % "Observations"),
                      _colspan = 8,
                      ),
                   ))
        bappend(TR(TD("\n\n\n\n",
                      _colspan = 8,
                      ),
                   ))
        bappend(TR(TD("",
                      _colspan = 8,
                      ),
                   ))

        return DIV(body)

    def pdf_footer(r):
        return DIV(TABLE(TR(TH("DELIVERED BY",
                               _align = "center",
                               ),
                            TH("DATE",
                               _align = "center",
                               ),
                            TH("FUNCTION",
                               _align = "center",
                               _colspan = 2,
                               ),
                            TH("%s (%s)" % ("NAME",
                                            "IN BLOCK LETTER",
                                            ),
                               _align = "center",
                               _colspan = 3,
                               ),
                            TH("SIGNATURE",
                               _align = "center",
                               _colspan = 2,
                               ),
                            ),
                         TR(TD(""),
                            TD(""),
                            TD("",
                               _colspan = 2,
                               ),
                            TD("",
                               _colspan = 3,
                               ),
                            TD("",
                               _colspan = 2,
                               ),
                            ),
                         TR(TH("RECEIVED BY",
                               _align = "center",
                               ),
                            TH("DATE",
                               _align = "center",
                               ),
                            TH("FUNCTION",
                               _align = "center",
                               _colspan = 2,
                               ),
                            TH("%s (%s)" % ("NAME",
                                            "IN BLOCK LETTER",
                                            ),
                               _align = "center",
                               _colspan = 3,
                               ),
                            TH("SIGNATURE / STAMP",
                               _align = "center",
                               _colspan = 2,
                               ),
                            ),
                         TR(TD(""),
                            TD(""),
                            TD("",
                               _colspan = 2,
                               ),
                            TD("",
                               _colspan = 3,
                               ),
                            TD("",
                               _colspan = 2,
                               ),
                            ),
                         ))

    exporter = S3Exporter().pdf
    return exporter(r.resource,
                    request = r,
                    pdf_title = current.deployment_settings.get_inv_recv_form_name(),
                    pdf_filename = recv_ref,
                    pdf_header = pdf_header,
                    pdf_header_padding = 12,
                    #method = "list",
                    #pdf_componentname = "track_item",
                    #list_fields = list_fields,
                    pdf_callback = pdf_body,
                    pdf_footer = pdf_footer,
                    pdf_hide_comments = True,
                    #pdf_html_styles = styles,
                    pdf_table_autogrow = "B",
                    pdf_orientation = "Landscape",
                    **attr
                    )

# -------------------------------------------------------------------------
def grn_hnrc(r, **attr):
    """
        GRN (Goods Received Note) for HNRC: Honduran Red Cross

        @param r: the S3Request instance
        @param attr: controller attributes
    """

    T = current.T

    # Master record (=inv_recv)
    resource = current.s3db.resource(r.tablename,
                                     id = r.id,
                                     components = ["track_item"],
                                     )

    # Columns and data for the form header
    header_fields = ["eta",
                     "date",
                     (T("Origin"), "from_site_id"),
                     (T("Destination"), "site_id"),
                     "sender_id",
                     "recipient_id",
                     "send_ref",
                     "recv_ref",
                     "comments",
                     ]

    header_data = resource.select(header_fields,
                                  start = 0,
                                  limit = 1,
                                  represent = True,
                                  show_links = False,
                                  raw_data = True,
                                  )
    if not header_data:
        r.error(404, current.ERROR.BAD_RECORD)

    # Generate PDF header
    row = header_data.rows[0]
    labels = {rfield.colname: rfield.label for rfield in header_data.rfields}
    def row_(left, right):
        return header_row_(left, right, row=row, labels=labels)

    # Get organisation name and logo
    name, logo = OM().render()

    # The title
    title = H2(T("Goods Received Note"))

    # GRN details
    dtable = TABLE(TR(TD(DIV(logo,
                             H4(name),
                             ),
                         _colspan = 2,
                         ),
                      TD(DIV(title),
                         _colspan = 2,
                         ),
                      ),
                   row_("inv_recv.eta", "inv_recv.date"),
                   row_("inv_recv.from_site_id", "inv_recv.site_id"),
                   row_("inv_recv.sender_id", "inv_recv.recipient_id"),
                   row_("inv_recv.send_ref", "inv_recv.recv_ref"),
                   )

    # GRN comments
    ctable = TABLE(TR(TH(T("Comments"))),
                   TR(TD(row["inv_recv.comments"])),
                   )

    pdf_header = DIV(dtable,
                     P("&nbsp;"),
                     ctable,
                     )

    # Filename from send_ref
    header_row = header_data.rows[0]
    pdf_filename = header_row["_row"]["inv_recv.recv_ref"]

    # Component (=inv_track_item)
    component = resource.components["track_item"]
    body_fields = ["item_id",
                   "item_pack_id",
                   "recv_quantity",
                   (T("Total Volume (m3)"), "total_recv_volume"),
                   (T("Total Weight (kg)"), "total_recv_weight"),
                   "supply_org_id",
                   "inv_item_status",
                   ]
    # Any extra fields needed for virtual fields
    component.configure(extra_fields = ["item_id$weight",
                                        "item_id$volume",
                                        ],
                        )

    # Aggregate methods and column names
    aggregate = [("sum", "inv_track_item.recv_quantity"),
                 ("sum", "inv_track_item.total_recv_volume"),
                 ("sum", "inv_track_item.total_recv_weight"),
                 ]

    # Generate the JSON data dict
    json_data = json_data_(component,
                           body_fields,
                           aggregate = aggregate,
                           )

    # Generate the grouped items table
    from s3 import S3GroupedItemsTable
    output = S3GroupedItemsTable(component,
                                 data = json_data,
                                 totals_label = T("Total"),
                                 title = T("Goods Received Note"),
                                 pdf_header = pdf_header,
                                 pdf_footer = grn_hnrc_footer,
                                 )

    # ...and export it as PDF
    return output.pdf(r, filename=pdf_filename)

# -------------------------------------------------------------------------
def grn_hnrc_footer(r):
    """
        Footer for Goods Received Notes for HNRC: Honduran Red Cross

        @param r: the S3Request
    """

    T = current.T

    return TABLE(TR(TH(T("Delivered by")),
                    TH(T("Date")),
                    TH(T("Function")),
                    TH(T("Name")),
                    TH(T("Signature")),
                    TH(T("Status")),
                    ),
                 TR(TD(T("&nbsp;"))),
                 TR(TH(T("Received by")),
                    TH(T("Date")),
                    TH(T("Function")),
                    TH(T("Name")),
                    TH(T("Signature")),
                    TH(T("Status")),
                    ),
                 TR(TD("&nbsp;")),
                 )

# END =========================================================================
