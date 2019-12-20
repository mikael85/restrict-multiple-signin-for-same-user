# -*- coding: utf-8 -*-

from openerp.http import request
from openerp import models


class ir_http(models.AbstractModel):
    _inherit = 'ir.http'

    def _authenticate(self, auth_method='user'):
        res = super(ir_http, self)._authenticate(auth_method=auth_method)
        if request and request.env and request.env.user:
            request.env.user._auth_timeout_check()
        return res
