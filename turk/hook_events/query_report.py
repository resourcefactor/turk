import frappe
from frappe.desk.query_report import get_script as core_get_script

CUSTOM_REPORT_OVERRIDES = {
	"General Ledger": {
		"app": "turk",
		"folder": ["turk", "report", "general_ledger"],
		"html": "general_ledger.html",
		"extra_js": "general_ledger_extra.js",
	},
}


@frappe.whitelist()
def get_script(report_name: str):
	result = core_get_script(report_name)

	override = CUSTOM_REPORT_OVERRIDES.get(report_name)
	if not override:
		return result

	html_path = frappe.get_app_path(override["app"], *override["folder"], override["html"])
	with open(html_path) as f:
		result["html_format"] = f.read()

	if override.get("extra_js"):
		js_path = frappe.get_app_path(override["app"], *override["folder"], override["extra_js"])
		with open(js_path) as f:
			result["script"] = (result.get("script") or "") + "\n\n" + f.read()

	return result
