# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`turk` is a Frappe app ("Customizations for TURK") that sits on top of ERPNext (branch `version-15`, Frappe/ERPNext v15). It lives in a shared multi-tenant bench at `/home/erp15/frappe-bench` with many other client apps and sites. Turk is not installed on every site, so check which site you're targeting (`bench --site <site> list-apps`).

**Convention:** customize ERPNext from this app (hooks, overrides, Custom Fields, injected JS). Never edit `apps/erpnext` or `apps/frappe`.

## Commands

Run these from `/home/erp15/frappe-bench`:

```bash
bench --site <site> migrate                 # sync doctype/report JSON + turk/turk/custom/*.json customizations
bench build --app turk                      # rebuild public/ assets (turk.css)
bench --site <site> clear-cache             # needed after changing doctype_js files or hooks.py
bench --site <site> run-tests --app turk                        # all tests
bench --site <site> run-tests --doctype "Item Label"            # one doctype's tests
bench --site <site> run-tests --module turk.turk.doctype.item_label.test_item_label
bench --site <site> console                 # IPython with frappe initialised
```

There is no lint config or CI. The existing `test_*.py` files are empty Frappe scaffolds.

## Architecture

The code lives in the Python package `turk/`. The single Frappe module is `Turk`, at `turk/turk/`.

- **`hooks.py` is the map of all behaviour.** Start here. It wires:
  - `doc_events` for Sales Order, Sales Invoice, Payment Entry, Purchase Invoice, Purchase Receipt, Journal Entry and Opportunity. The handlers live in `turk/hook_events/<doctype>.py`, plus a few in `turk/utils.py`.
  - `doctype_js`, which injects `turk/public/js/<doctype>.js` into the standard ERPNext forms.
  - `override_doctype_class`: `Journal Entry` → `hook_events/override_journal_entry.py`, which disables `validate_invoices`.
  - `override_whitelisted_methods`: `frappe.desk.query_report.get_script` → `hook_events/query_report.py`.
  - `jenv` exposes `get_qrcode_image` to Jinja print formats.
- **Client JS:** most `public/js/<doctype>.js` files start with `{% include "turk/public/js/utils.js" %}`. That shared file registers handlers on `cur_frm.doctype`, so it applies to every doctype that includes it. `sales_order.js` also includes the full ERPNext `sales_order.js`. The JS calls whitelisted methods mostly in `turk.utils` (`ts_make_sales_invoice`, `make_debit_note_from_sales_return`, `get_item_details`, `warehouse_query`, …) and in `turk.hook_events.*`.
- **Customizations as files:** `turk/turk/custom/*.json` holds the Custom Fields and Property Setters for standard doctypes, and `migrate` syncs them. To add a field to an ERPNext doctype, edit or export the matching JSON here. Don't rely on DB-only customizations.
- **Overriding a standard report without touching ERPNext:** add an entry to `CUSTOM_REPORT_OVERRIDES` in `hook_events/query_report.py`. It swaps the report's `html_format` and appends extra JS from a folder under `turk/turk/report/`. `turk/turk/report/general_ledger/` (HTML plus `general_ledger_extra.js`) is the example. That folder is not a real report.
- **Custom reports:** `turk/turk/report/`. Many reports are client-specific forks of ERPNext reports, with suffixes such as `_sih`, `_tc` and `_si` (for example `customer_ledger_summary_sih`, `general_ledger_si`, `gross_profit_tc`).
- **Cross-document automation:** several submit hooks create other documents automatically, so a change to one document's flow often affects another:
  - `party_link.create_invoice_adj_jv` posts an adjustment Journal Entry when a Sales Invoice customer or Purchase Invoice supplier is linked through **Party Link**. It is skipped when `no_double_ledger` is set or the invoice is POS. `cancel_adjusted_jv` and `prevent_linked_jv_cancellation` cover the reverse.
  - Purchase Invoice and Purchase Receipt submit can create a Landed Cost Voucher (`hook_events/utils.py`).
  - Sales Invoice submit can create Purchase Invoices against sales taxes. Payment Entry submit can create a mirrored Payment Entry.
  - Sales Invoice ↔ Purchase Invoice mapping: `make_sales_invoice` builds a Sales Invoice from a Purchase Invoice. `make_debit_note_from_sales_return` drafts a Purchase Invoice return from a Sales return. `shipment_no` ties the two together: it is unique on Sales Invoice and gets an `R-` prefix on returns.
- `hook_events/sales_and_purchase_return_override.py` holds a copied and modified ERPNext `make_return_doc`. Nothing references it yet.

## Commit style

Use conventional-commit subjects scoped by doctype or report, e.g. `feat(sales invoice): …` or `fix(purchase invoice): …`.
