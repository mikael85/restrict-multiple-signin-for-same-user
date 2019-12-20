odoo.define('single_login.custom', function (require) {
    "use strict";

    var WebClient = require('web.WebClient');
    var Model = require('web.DataModel');    

    WebClient.include({
        start: function () {
            function updateExpiry() {
                new Model('res.users').call('save_session').then(function (data) {console.log(data)});
            }
            this._super();
            if (this._session_interval) {
                clearInterval(this._session_interval);
            }
            this._session_interval = setInterval(updateExpiry,60*1000);
        },
        on_logout: function () {
            var self = this;
            this.clear_uncommitted_changes().then(function () {
                clearInterval(self._session_interval);
                new Model('res.users').call('clear_session').then(function (data) {
                    console.log(data);
                });
                self.action_manager.do_action('logout');
            });
        },
    });
});