# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020, libracore and contributors
# License: AGPL v3. See LICENCE
from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("Settings"),
            "icon": "octicon octicon-tools",
            "items": [
                   {
                       "type": "doctype",
                       "name": "Bazzell Settings",
                       "label": _("Bazzell Settings"),
                       "description": _("Bazzell Settings")
                   }
            ]
        }
    ]
