# -*- coding: utf-8 -*-

from gluon import current
from gluon.html import *

from s3 import S3CustomController

THEME = "AidIQ"

# =============================================================================
class index(S3CustomController):
    """ Custom Home Page """

    def __call__(self):

        page = current.request.get_vars.get("page", None)
        if page:
            vars = {"page":page}
            table = current.s3db.cms_post
            query = (table.name == page) & \
                    (table.deleted != True)
            row = current.db(query).select(table.id,
                                           table.title,
                                           table.body,
                                           limitby=(0, 1)).first()
        else:
            module = "default"
            vars = {"module":module}
            table = current.s3db.cms_post
            db = current.db
            ltable = db.cms_post_module
            query = (ltable.module == module) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            row = db(query).select(table.id,
                                   table.title,
                                   table.body,
                                   limitby=(0, 1)).first()
        title = None
        if row:
            title = row.title
            if current.auth.s3_has_role(current.session.s3.system_roles.ADMIN):
                item = DIV(XML(row.body),
                           BR(),
                           A(current.T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[row.id, "update"],
                                       vars=vars),
                             _class="action-btn"))
            else:
                item = XML(row.body)

        elif current.auth.s3_has_role(current.session.s3.system_roles.ADMIN):
            item = A(current.T("Edit"),
                     _href=URL(c="cms", f="post", args="create",
                               vars=vars),
                     _class="action-btn")
        else:
            item = None

        if not title:
            title = current.deployment_settings.get_system_name()
        current.response.title = title

        self._view(THEME, "index.html")
        return {"content": item,
                }

# =============================================================================
class contact(S3CustomController):
    """ Contact Form """

    def __call__(self):

        request = current.request
        response = current.response

        if request.env.request_method == "POST":
            # Processs Form
            vars = request.post_vars
            result = current.msg.send_email(
                        to=current.deployment_settings.get_mail_approver(),
                        subject=vars.subject,
                        message=vars.message,
                        reply_to=vars.address,
                )
            if result:
                response.confirmation = "Thankyou for your message - we'll be in touch shortly"

        from gluon import Field, SQLFORM
        from s3 import s3_mark_required, S3StringWidget

        T = current.T
        formstyle = current.deployment_settings.get_ui_formstyle()

        fields = [Field("name",
                        label = T("Your name"),
                        required = True,
                        ),
                  Field("address",
                        label = T("Your e-mail address"),
                        required = True,
                        #widget = S3StringWidget(placeholder="name@example.com"),
                        ),
                  Field("subject",
                        label = T("Subject"),
                        required = True,
                        ),
                  Field("message", "text",
                        label = T("Message"),
                        required = True,
                        ),
                  ]

        labels, required = s3_mark_required(fields)
        response.form_label_separator = ""
        form = SQLFORM.factory(formstyle = formstyle,
                               labels = labels,
                               submit_button = T("Send Message"),
                               *fields)
        form["_id"] = "mailform"
        form = DIV(
                H4("Contact Us", _style="background-color:#f7f8f9;padding:0.1rem 0.3rem"),
                P("You can leave a message using the contact form below."),
                form,
                _class="form-container",
                )

        appname = request.application
        s3 = response.s3
        sappend = s3.scripts.append
        if s3.cdn:
            if s3.debug:
                sappend("http://ajax.aspnetcdn.com/ajax/jquery.validate/1.11.1/jquery.validate.js")
            else:
                sappend("http://ajax.aspnetcdn.com/ajax/jquery.validate/1.11.1/jquery.validate.min.js")

        else:
            if s3.debug:
                sappend("/%s/static/scripts/jquery.validate.js" % appname)
            else:
                sappend("/%s/static/scripts/jquery.validate.min.js" % appname)
        if s3.debug:
            sappend("/%s/static/themes/AidIQ/js/contact.js" % appname)
        else:
            sappend("/%s/static/themes/AidIQ/js/contact.min.js" % appname)

        response.title = "Contact | AidIQ.com"

        self._view(THEME, "contact.html")
        return {"form": form,
                }

# END =========================================================================
