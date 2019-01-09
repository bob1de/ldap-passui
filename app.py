#!/usr/bin/env python3

import configparser
import logging
import os

import bottle

import ldap3
from ldap3.core.exceptions import LDAPBindError, LDAPConstraintViolationResult, \
    LDAPInvalidCredentialsResult, LDAPUserNameIsMandatoryError, \
    LDAPSocketOpenError, LDAPExceptionError

import voluptuous as vol

import yaml


__version__ = "0.0.0"


BASE_DIR = os.path.dirname(__file__)

# Set up logging.
LOG = logging.getLogger(__name__)
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(format=LOG_FORMAT)
LOG.setLevel(logging.INFO)

CONFIG_SCHEMA = vol.Schema(vol.All(
    lambda v: v or {},
    {
        vol.Optional("html", default=None): vol.All(
            vol.DefaultTo(dict),
            {
                "page_title": str,
            },
        ),
        vol.Optional("ldap", default=None): vol.All(
            vol.DefaultTo(dict),
            vol.Schema({
                vol.Required(
                    vol.Any("user_dn", "user_search_base"),
                    msg="Either 'user_dn' or 'user_search_base' "
                        "needs to be configured."
                ): object,
            }, extra=vol.ALLOW_EXTRA),
            vol.Schema({
                vol.Exclusive(
                    "user_dn", "user_resolution_method",
                    msg="Only one of 'user'dn' and 'user_search_base' "
                        "may be configured."
                ): object,
                vol.Exclusive(
                    "user_search_base", "user_resolution_method",
                    msg="Only one of 'user'dn' and 'user_search_base' "
                        "may be configured."
                ): object,
            }, extra=vol.ALLOW_EXTRA),
            vol.Schema({
                vol.Inclusive(
                    "user_search_base", "user_search",
                    msg="'user_search_base' and 'user_search_filter' "
                        "may only be configured together."
                ): object,
                vol.Inclusive(
                    "user_search_filter", "user_search",
                    msg="'user_search_base' and 'user_search_filter' "
                        "may only be configured together."
                ): object,
            }, extra=vol.ALLOW_EXTRA),
            {
                vol.Required("host"): str,
                vol.Required("port"): int,
                vol.Optional("use_ssl", default=False): bool,
                vol.Optional("type", default="ldap"): vol.Any(
                    "ad", "ldap",
                ),
                "user_dn": str,
                "user_search_base": str,
                "user_search_filter": str,
                "user_search_bind_dn": str,
                "user_search_bind_pass": str,
                "bind_dn": str,
                "bind_pass": str,
            },
        ),
        vol.Optional("policy", default=None): vol.All(
            vol.DefaultTo(dict),
            {
                vol.Optional("enable", default=False): bool,
                vol.Optional("min_length", default=0): int,
                vol.Optional("max_length", default=0): int,
                vol.Optional("min_lowers", default=0): int,
                vol.Optional("min_uppers", default=0): int,
                vol.Optional("min_digits", default=0): int,
                vol.Optional("min_specials", default=0): int,
                vol.Optional("specials", default=" äöüÄÖÜß,.-;:_!/%"): str,
                vol.Optional("forbid_others", default=False): bool,
                vol.Optional("forbid_username", default=False): bool,
                vol.Optional("forbid_reuse", default=False): bool,
            },
        ),
        vol.Optional("server", default=None): vol.All(
            vol.DefaultTo(dict),
            {
                str: object,
            },
        ),
    },
))

def read_config():
    config_file = os.environ.get(
        "CONFIG_FILE", os.path.join(BASE_DIR, "config.yaml")
    )
    with open(config_file) as file:
        config = yaml.load(file)

    return CONFIG_SCHEMA(config)

CONF = read_config()

if os.environ.get("DEBUG"):
    bottle.debug(True)
bottle.TEMPLATE_PATH = [os.path.join(BASE_DIR, "templates")]

# Set default attributes to pass into templates.
bottle.SimpleTemplate.defaults["url"] = bottle.url
bottle.SimpleTemplate.defaults["html"] = CONF["html"]
bottle.SimpleTemplate.defaults["policy"] = CONF["policy"]


########## /static/

@bottle.route("/static/<filename>", name="static")
def serve_static(filename):
    return bottle.static_file(filename, root=os.path.join(BASE_DIR, "static"))


########## /

def index_tpl(**kwargs):
    return bottle.template('index', **kwargs)

@bottle.get("/")
def get_index():
    return index_tpl()

@bottle.post("/")
def post_index():
    form = bottle.request.forms
    username = form.username
    old = form.old_password
    new = form.new_password

    def error(msg):
        return index_tpl(username=username, alerts=[("error", msg)])

    if new != form.confirm_password:
        return error("The new password and its confirmation don't match.")

    if CONF["policy"]["enable"]:
        policy = CONF["policy"]
        policy_violation = lambda: error(
            "The requirements on password strength are not fulfilled. "
            "Please choose another password."
        )
        if len(new) < policy["min_length"]:
            return policy_violation()
        if policy["max_length"] and len(new) > policy["max_length"]:
            return policy_violation()
        sum_lowers = sum(int(c.islower()) for c in new)
        if sum_lowers < policy["min_lowers"]:
            return policy_violation()
        sum_uppers = sum(int(c.isupper()) for c in new)
        if sum_uppers < policy["min_uppers"]:
            return policy_violation()
        sum_digits = sum(int(c.isdigit()) for c in new)
        if sum_digits < policy["min_digits"]:
            return policy_violation()
        specials = policy["specials"]
        sum_specials = sum(int(c in specials) for c in new)
        if sum_specials < policy["min_specials"]:
            return policy_violation()
        if policy["forbid_others"] and \
           sum_lowers + sum_uppers + sum_digits + sum_specials != len(new):
            return policy_violation()
        if policy["forbid_username"] and \
           username.strip().lower() in new.lower():
            return policy_violation()
        if policy["forbid_reuse"] and new == old:
            return policy_violation()

    try:
        change_password(username, old, new)
    except Exception as e:
        LOG.warning("Failed to change password for %s: %s", username, e)
        return error(str(e))

    LOG.info("Password successfully changed for: %s", username)
    return index_tpl(alerts=[("success", "Password has been changed.")])


def connect_ldap(**kwargs):
    server = ldap3.Server(
        host=CONF["ldap"]["host"], port=CONF["ldap"]["port"],
        use_ssl=CONF["ldap"]["use_ssl"], connect_timeout=5,
    )
    return ldap3.Connection(server, raise_exceptions=True, **kwargs)

def find_user_dn(conn, username):
    search_filter = CONF["ldap"]["user_search_filter"].format(username=username)
    conn.search(
        CONF["ldap"]["user_search_base"], search_filter, ldap3.SUBTREE,
        attributes=["dn"]
    )
    return conn.response[0]["dn"] if conn.response else None

def change_password(*args):
    try:
        _do_change_password(*args)
    except (LDAPBindError, LDAPInvalidCredentialsResult, LDAPUserNameIsMandatoryError):
        raise Exception("Username or old password is incorrect.")
    except LDAPConstraintViolationResult as e:
        # Extract useful part of the error message (for Samba 4 / AD).
        msg = e.message.split('check_password_restrictions: ')[-1].capitalize()
        raise Error(msg)
    except LDAPSocketOpenError as e:
        LOG.error('{}: {!s}'.format(e.__class__.__name__, e))
        raise Error('Unable to connect to the remote server.')
    except LDAPExceptionError as e:
        LOG.error('{}: {!s}'.format(e.__class__.__name__, e))
        raise Exception("Unexpected error while communicating with the remote server.")

def _do_change_password(username, old_pass, new_pass):
    if CONF["ldap"].get("user_dn"):
        user_dn = CONF["ldap"]["user_dn"].format(username=username)
    elif CONF["ldap"].get("user_search_bind_dn"):
        bind_dn = CONF["ldap"]["user_search_bind_dn"].format(username=username)
        bind_pass = CONF["ldap"].get("user_search_bind_pass", old_pass)
        with connect_ldap(
            authentication=ldap3.SIMPLE, user=bind_dn, password=bind_pass
        ) as c:
            user_dn = find_user_dn(c, username)
    else:
        # search anonymously
        with connect_ldap() as c:
            user_dn = find_user_dn(c, username)

    if CONF["ldap"].get("bind_dn"):
        bind_dn = CONF["ldap"]["bind_dn"].format(username=username)
    else:
        bind_dn = user_dn
    bind_pass = CONF["ldap"].get("bind_pass", old_pass)

    # Note: raises LDAPUserNameIsMandatoryError when bind_dn is None.
    with connect_ldap(
        authentication=ldap3.SIMPLE, user=bind_dn, password=bind_pass
    ) as c:
        c.bind()
        if CONF["ldap"]["type"] == "ad":
            c.extend.microsoft.modify_password(user_dn, new_pass, old_pass)
        else:
            c.extend.standard.modify_password(user_dn, old_pass, new_pass)


LOG.info("Initialized LDAP PassUI {}".format(__version__))

if __name__ == '__main__':
    # Run bottle internal server when invoked directly (mainly for development).
    bottle.run(**CONF["server"])
else:
    # Run bottle in application mode (in production under WSGI server).
    application = bottle.default_app()
