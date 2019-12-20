# -*- coding: utf-8 -*-

import logging
import openerp
from openerp import SUPERUSER_ID, _
from openerp.http import request, Response
from openerp import http

class Home(openerp.addons.web.controllers.main.Home):
    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        openerp.addons.web.controllers.main.ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = openerp.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except openerp.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(
                request.session.db, request.params['login'], request.params['password'])
            if uid is not False:
                request.params['login_success'] = True
                if not redirect:
                    redirect = '/web'
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = _(
                "Login failed due to one of the following reasons")
            values['error2'] = _("- Wrong login/password")
            values['error3'] = _(
                "- User already logged in from another system")
        return request.render('web.login', values)