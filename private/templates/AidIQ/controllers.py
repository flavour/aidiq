# -*- coding: utf-8 -*-

from os import path

from gluon import current
from gluon.html import *

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "private", "templates",
                         "AidIQ", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        T = current.T

        page = request.get_vars.get("page", None)
        if page:
            vars = {"page":page}
            table = current.s3db.cms_post
            row = current.db(table.name == page).select(table.id,
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
                           A(T("Edit"),
                             _href=URL(c="cms", f="post",
                                       args=[row.id, "update"],
                                       vars=vars),
                             _class="action-btn"))
            else:
                item = XML(row.body)

        elif current.auth.s3_has_role(current.session.s3.system_roles.ADMIN):
            item = A(T("Edit"),
                     _href=URL(c="cms", f="post", args="create",
                               vars=vars),
                     _class="action-btn")
        else:
            item = None

        if not title:
            title = current.deployment_settings.get_system_name()
        response.title = title

        return dict(content=item)
        
# =============================================================================
class contact():
    """ Contact Form """

    def __call__(self):

        request = current.request
        response = current.response

        view = path.join(request.folder, "private", "templates",
                         "AidIQ", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

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
            
        #T = current.T

        form = DIV(
                H1("Contact Us"),
                P("You can leave a message using the contact form below."),
                FORM(TABLE(
                        TR(LABEL("Your name:",
                              SPAN(" *", _class="req"),
                              _for="name")),
                        TR(INPUT(_name="name", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Your e-mail address:",
                              SPAN(" *", _class="req"),
                              _for="address")),
                        TR(INPUT(_name="address", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Subject:",
                              SPAN(" *", _class="req"),
                              _for="subject")),
                        TR(INPUT(_name="subject", _type="text", _size=62, _maxlength="255")),
                        TR(LABEL("Message:",
                              SPAN(" *", _class="req"),
                              _for="name")),
                        TR(TEXTAREA(_name="message", _class="resizable", _rows=5, _cols=62)),
                        TR(INPUT(_type="submit", _value="Send e-mail")),
                        ),
                    _id="mailform"
                    )
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
        return dict(content=form)

# END =========================================================================
