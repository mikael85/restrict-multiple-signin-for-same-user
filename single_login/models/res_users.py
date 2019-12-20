# -*- coding: utf-8 -*-

import logging
import openerp
from datetime import date, datetime, time, timedelta
from openerp import SUPERUSER_ID, _, api, models, fields
from openerp.http import request
from openerp import http

_logger = logging.getLogger(__name__)


class res_users(models.Model):
    _inherit = 'res.users'

    session_id = fields.Char('Session ID', size=100)
    expiration_date = fields.Datetime('Expiration Date')
    logged_in = fields.Boolean('Logged in')

    def _login(self, db, login, password):
        cr = self.pool.cursor()
        cr.autocommit(True)
        user_id = super(res_users, self)._login(db, login, password)
        try:
            session_id = request.httprequest.session.sid
            temp_browse = self.browse(cr, SUPERUSER_ID, user_id)
            if isinstance(temp_browse, list):
                temp_browse = temp_browse[0]
            exp_date = temp_browse.expiration_date
            if exp_date and temp_browse.session_id:
                exp_date = datetime.strptime(exp_date, "%Y-%m-%d %H:%M:%S")
                if exp_date < datetime.utcnow() or temp_browse.session_id != session_id:
                    raise openerp.exceptions.AccessDenied()
            self.save_session(cr, user_id)
        except openerp.exceptions.AccessDenied:
            user_id = False
            _logger.warn(
                _("User %s is already logged in into the system!"), login)
            _logger.warn(
                _("Multiple sessions are not allowed for security reasons!"))
        finally:
            cr.close()
        return user_id

    # clears session_id and session expiry from res.users

    def clear_session(self, cr, user_id):
        if isinstance(user_id, list):
            user_id = user_id[0]
        self.write(cr, SUPERUSER_ID, user_id, {'session_id': '', 'expiration_date': False, 'logged_in': False})

    # insert session_id and session expiry into res.users
    def save_session(self, cr, user_id):
        if isinstance(user_id, list):
            user_id = user_id[0]
        exp_date = datetime.utcnow() + timedelta(minutes=2)
        sid = request.httprequest.session.sid
        self.write(cr, SUPERUSER_ID, user_id, {'session_id': sid, 'expiration_date': exp_date, 'logged_in': True})

    # schedular function to validate users session
    def validate_sessions(self, cr, uid):
        ids = self.search(cr, SUPERUSER_ID, [('expiration_date', '!=', False)])
        users = self.browse(cr, SUPERUSER_ID, ids)

        for user_id in users:
            exp_date = datetime.strptime(
                user_id.expiration_date, "%Y-%m-%d %H:%M:%S")
            if exp_date < datetime.utcnow():
                self.clear_session(cr, user_id.id)

    @api.model
    def _session_terminate(self, session):
        if session.db and session.uid:
            session.logout(keep_db=True)
        return True

    @api.model
    def _auth_timeout_check(self):
        if not http.request:
            return
        session = http.request.session
        expired = False
        logged_user = self.search([
            ('session_id', '=', session.sid),
            ('logged_in', '=', True)
        ])
        if not logged_user:
            expired = self._session_terminate(session)
        if expired:
            raise openerp.http.SessionExpiredException("Session expired")
