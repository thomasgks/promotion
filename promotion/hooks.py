app_name = "promotion"
app_title = "Promotion"
app_publisher = "Printechs"
app_description = "Promotion"
app_email = "info@printechs.com"
app_license = "mit"
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/promotion/css/promotion.css"
# app_include_js = "/assets/promotion/js/promotion.js"

# include js, css files in header of web template
# web_include_css = "/assets/promotion/css/promotion.css"
# web_include_js = "/assets/promotion/js/promotion.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "promotion/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
doctype_js = {"Quotation" : "public/js/quotation.js"}
#doctype_js = {"Quotation" : "public/js/coupon_integration.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }
fixtures = [
    {"doctype": "Custom Field", "filters": [["module", "=", "Promotion"]]},
    {"doctype": "Property Setter", "filters": [["module", "=", "Promotion"]]}
]


# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "promotion.install.before_install"
# after_install = "promotion.install.after_install"

# Uninstallation
# --------------

# before_uninstall = "promotion.uninstall.before_uninstall"
# after_uninstall = "promotion.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "promotion.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Quotation": {
		"validate": "promotion.promotion.doctype.promotion.quotation_integration.validate_quotation_promotions",
		"on_submit": "promotion.promotion.doctype.promotion.quotation_integration.apply_quotation_promotions",
		"on_cancel": "promotion.promotion.doctype.promotion.quotation_integration.remove_quotation_promotions",
		"after_save": "promotion.promotion.doctype.promotion.quotation_integration.apply_quotation_promotions",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"promotion.tasks.all"
#	],
#	"daily": [
#		"promotion.tasks.daily"
#	],
#	"hourly": [
#		"promotion.tasks.hourly"
#	],
#	"weekly": [
#		"promotion.tasks.weekly"
#	]
#	"monthly": [
#		"promotion.tasks.monthly"
#	]
# }

# Testing
# -------

# before_tests = "promotion.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "promotion.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "promotion.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"promotion.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Translatable doctypes = ["Promotion", "Promotion Action", "Promotion Source Brand"]

# Global Search
# ---------------

# global_search_doctypes = [
#	"Promotion",
#	"Promotion Action",
#	"Promotion Source Brand",
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Translatable doctypes = ["Promotion", "Promotion Action", "Promotion Source Brand"]