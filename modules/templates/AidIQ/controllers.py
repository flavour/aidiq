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
            vars = {"page": page}
            table = current.s3db.cms_post
            query = (table.name == page) & \
                    (table.deleted != True)
            row = current.db(query).select(table.id,
                                           table.title,
                                           table.body,
                                           limitby = (0, 1)
                                           ).first()
        else:
            module = "default"
            vars = {"module": module}
            table = current.s3db.cms_post
            db = current.db
            ltable = db.cms_post_module
            query = (ltable.module == module) & \
                    (ltable.post_id == table.id) & \
                    (table.deleted != True)
            row = db(query).select(table.id,
                                   table.title,
                                   table.body,
                                   limitby = (0, 1)
                                   ).first()
        title = None
        if row:
            title = row.title
            if row.body:
                from s3compat import StringIO
                try:
                    body = current.response.render(StringIO(row.body), {})
                except:
                    body = row.body
            item = DIV(XML(body), _class="cms-item")
            if current.auth.s3_has_role(current.session.s3.system_roles.ADMIN):
                item.append(BR())
                item.append(A(current.T("Edit"),
                             _href = URL(c="cms", f="post",
                                         args = [row.id, "update"],
                                         vars = vars,
                                         ),
                             _class = "action-btn",
                             ))

        elif current.auth.s3_has_role(current.session.s3.system_roles.ADMIN):
            item = A(current.T("Edit"),
                     _href = URL(c="cms", f="post",
                                 args = "create",
                                 vars = vars,
                                 ),
                     _class = "action-btn",
                     )
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

        from gluon import Field, SQLFORM, IS_NOT_EMPTY, IS_EMAIL, IS_IN_SET, IS_EMPTY_OR
        from s3 import s3_mark_required, S3StringWidget

        T = current.T
        formstyle = current.deployment_settings.get_ui_formstyle()

        fields = [Field("address",
                        label = T("Your e-mail address"),
                        requires = IS_EMAIL(),
                        widget = lambda *args, **kwargs: \
                                 S3StringWidget(placeholder="name@example.com")(_type="email", *args, **kwargs),
                        ),
                  Field("subject",
                        label = T("Subject"),
                        requires = IS_EMPTY_OR(IS_IN_SET(("Solution Development",
                                                          "Workshop / Training",
                                                          "SAHANA Deployment / Support",
                                                          "Other / General Inquiry",
                                                          ),
                                                         zero = "What can we do for you?",
                                                         sort = False,
                                                         )),
                        ),
                  Field("message", "text",
                        label = T("Message"),
                        requires = IS_NOT_EMPTY(),
                        ),
                  ]

        labels, required = s3_mark_required(fields)
        response.form_label_separator = ""
        form = SQLFORM.factory(formstyle = formstyle,
                               labels = labels,
                               submit_button = T("Send Message"),
                               _id = "mailform",
                               *fields,
                               )

        if form.accepts(request.post_vars,
                        current.session,
                        formname = "default/index/contact",
                        #onvalidation = onvalidation,
                        keepvalues = False,
                        hideerror = False,
                        ):

            form_vars = form.vars
            subject = "Request on AidIQ website"
            if form_vars.subject:
                subject = "%s: %s" % (subject, form_vars.subject)

            result = current.msg.send_email(
                        to = current.deployment_settings.get_mail_approver(),
                        subject = form_vars.subject,
                        message = form_vars.message,
                        reply_to = form_vars.address,
                        )
            if result:
                response.confirmation = "Thank you for your message - we'll be in touch shortly"

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
        sappend("/%s/static/themes/AidIQ/js/contact.js" % appname)

        response.title = "Contact Us | AidIQ.com"

        self._view(THEME, "contact.html")

        return {"form": DIV(form, _class="form-container"),
                }

# END =========================================================================
