# -*- coding: utf-8 -*-

import openerp
from openerp.http import request
from openerp.http import Response
from openerp import http

class Root_new(openerp.http.Root):
    def get_response(self, httprequest, result, explicit_session):
        if isinstance(result, openerp.http.Response) and result.is_qweb:
            try:
                result.flatten()
            except(Exception), e:
                if request.db:
                    result = request.registry['ir.http']._handle_exception(e)
                else:
                    raise

        if isinstance(result, basestring):
            response = Response(result, mimetype='text/html')
        else:
            response = result

        # save to cache if requested and possible
        if getattr(request, 'cache_save', False) and response.status_code == 200:
            response.freeze()
            r = response.response
            if isinstance(r, list) and len(r) == 1 and isinstance(r[0], str):
                request.registry.cache[request.cache_save] = {
                    'content': r[0],
                    'mimetype': response.headers['Content-Type'],
                    'time': time.time(),
                }

        if httprequest.session.should_save:
            self.session_store.save(httprequest.session)
        # We must not set the cookie if the session id was specified using a http header or a GET parameter.
        # There are two reasons to this:
        # - When using one of those two means we consider that we are overriding the cookie, which means creating a new
        #   session on top of an already existing session and we don't want to create a mess with the 'normal' session
        #   (the one using the cookie). That is a special feature of the Session Javascript class.
        # - It could allow session fixation attacks.
        if not explicit_session and hasattr(response, 'set_cookie'):
            response.set_cookie(
                'session_id', httprequest.session.sid, max_age=2 * 60)

        return response


root = Root_new()
openerp.http.Root.get_response = root.get_response
