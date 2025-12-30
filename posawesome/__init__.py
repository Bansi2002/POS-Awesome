# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = "6.3.0"

try:
    import frappe  # noqa: F401
except ModuleNotFoundError:
    frappe = None


def console(*data):
    if not frappe:
        return
    frappe.publish_realtime("toconsole", data, user=frappe.session.user)
