# -*- coding: utf-8 -*-

from gluon import *
#from gluon.storage import Storage
#from s3 import *
from s3utils import s3_register_validation

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        auth = current.auth
        roles = current.session.s3.roles
        system_roles = auth.get_system_roles()
        AUTHENTICATED = system_roles.AUTHENTICATED

        if AUTHENTICATED in roles:
            if auth.s3_has_role("STAFF"):
                redirect(URL(c="project", f="task", vars={"mine":1}))
            else:
                # Customer
                redirect(URL(c="project", f="project", vars={"tasks":1}))
        
        T = current.T
        s3db = current.s3db
        request = current.request
        appname = request.application
        response = current.response
        s3 = response.s3
        settings = current.deployment_settings

        title = settings.get_system_name()
        response.title = title
        response.view = "../private/templates/AidIQ/views/index.html"

        item = ""
        if settings.has_module("cms"):
            table = s3db.cms_post
            query = (table.module == "default")
            item = current.db(query).select(table.body,
                                            limitby=(0, 1)).first()
            if item:
                item = DIV(XML(item.body))
            else:
                item = ""

        # Menu Boxes
        datatable_ajax_source = ""
        # Check logged in AND permissions
        if AUTHENTICATED in roles and \
           auth.s3_has_permission("read", s3db.project_project):
            project_items = self.project()
            datatable_ajax_source = "/%s/default/project.aaData" % \
                                    appname
            s3.actions = None
            response.view = "default/index.html"
            if auth.s3_has_role(ADMIN):
                add_btn = A(T("Add Project"),
                            _href = URL(c="project", f="project",
                                        args=["create"]),
                            _id = "add-btn",
                            _class = "action-btn",
                            _style = "margin-right: 10px;")
            else:
                add_btn = ""
            project_box = DIV( H3(T("Projects")),
                           add_btn,
                            project_items["items"],
                            _id = "project_box",
                            _class = "menu_box fleft"
                            )
        else:
            project_box = ""



        # Login/Registration forms
        self_registration = settings.get_security_self_registration()
        registered = False
        login_form = None
        login_div = None
        register_form = None
        register_div = None
        if AUTHENTICATED not in roles:
            # This user isn't yet logged-in
            if request.cookies.has_key("registered"):
                # This browser has logged-in before
                registered = True

            if self_registration:
                # Provide a Registration box on front page
                request.args = ["register"]
                if settings.get_terms_of_service():
                    auth.messages.submit_button = T("I accept. Create my account.")
                else:
                    auth.messages.submit_button = T("Register")
                register_form = auth()
                register_div = DIV(H3(T("Register")),
                                   P(XML(T("If you need an account, then please %(sign_up_now)s") % \
                                            dict(sign_up_now=B(T("sign-up now"))))))

                 # Add client-side validation
                s3_register_validation()

                if s3.debug:
                    s3.scripts.append( "/%s/static/scripts/jquery.validate.js" % appname)
                else:
                    s3.scripts.append( "/%s/static/scripts/jquery.validate.min.js" % appname)
                if request.env.request_method == "POST":
                    post_script = '''// Unhide register form
        $('#register_form').removeClass('hide');
        // Hide login form
        $('#login_form').addClass('hide');'''
                else:
                    post_script = ""
                register_script = '''
        // Change register/login links to avoid page reload, make back button work.
        $('#register-btn').attr('href', '#register');
        $('#login-btn').attr('href', '#login');
        %s
        // Redirect Register Button to unhide
        $('#register-btn').click(function() {
            // Unhide register form
            $('#register_form').removeClass('hide');
            // Hide login form
            $('#login_form').addClass('hide');
        });

        // Redirect Login Button to unhide
        $('#login-btn').click(function() {
            // Hide register form
            $('#register_form').addClass('hide');
            // Unhide login form
            $('#login_form').removeClass('hide');
        });''' % post_script
                s3.jquery_ready.append(register_script)

            # Provide a login box on front page
            request.args = ["login"]
            auth.messages.submit_button = T("Login")
            login_form = auth()
            login_div = DIV(H3(T("Login")),
                            P(XML(T("Registered users can %(login)s to access the system" % \
                                    dict(login=B(T("login")))))))

        if settings.frontpage.rss:
            s3.external_stylesheets.append("http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.css")
            s3.scripts.append("http://www.google.com/jsapi?key=notsupplied-wizard")
            s3.scripts.append("http://www.google.com/uds/solutions/dynamicfeed/gfdynamicfeedcontrol.js")
            counter = 0
            feeds = ""
            for feed in settings.frontpage.rss:
                counter += 1
                feeds = "".join((feeds,
                                 "{title: '%s',\n" % feed["title"],
                                 "url: '%s'}" % feed["url"]))
                # Don't add a trailing comma for old IEs
                if counter != len(settings.frontpage.rss):
                    feeds += ",\n"
            feed_control = "".join(('''
function LoadDynamicFeedControl() {
  var feeds = [
    """, feeds, """
  ];
  var options = {
    // milliseconds before feed is reloaded (5 minutes)
    feedCycleTime : 300000,
    numResults : 5,
    stacked : true,
    horizontal : false,
    title : '''', str(T("News")), ''''
  };
  new GFdynamicFeedControl(feeds, 'feed-control', options);
}
// Load the feeds API and set the onload callback.
google.load('feeds', '1');
google.setOnLoadCallback(LoadDynamicFeedControl);'''))
            s3.js_global.append(feed_control)

        return dict(title = title,
                    item = item,
                    project_box = project_box,
                    r = None, # Required for dataTable to work
                    datatable_ajax_source = datatable_ajax_source,
                    self_registration=self_registration,
                    registered=registered,
                    login_form=login_form,
                    login_div=login_div,
                    register_form=register_form,
                    register_div=register_div
                    )

    # -----------------------------------------------------------------------------
    @staticmethod
    def project():
        """
            Function to handle pagination for the project list on the homepage
        """

        s3db = current.s3db
        s3 = current.response.s3

        table = s3db.project_project
        table.id.label = current.T("Project")
        table.id.represent = lambda id: \
            s3db.project_project_represent(id, show_link=False)

        s3.dataTable_sPaginationType = "two_button"
        s3.dataTable_sDom = "rtip" #"frtip" - filter broken
        s3.dataTable_iDisplayLength = 25

        s3db.configure("project_project",
                       listadd = False,
                       addbtn = True,
                       # Link straight to Tasks view & filter to just those which are open
                       linkto = "/%s/project/project/%s/task?open=1" % \
                        (current.request.application, "%s"),
                       list_fields = ["id",])

        return current.s3_rest_controller("project", "project")

# END =========================================================================
