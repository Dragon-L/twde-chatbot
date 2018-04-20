import functools
import logging

from flask import request, json
import jsonschema

from chatbot.config import CONF


logger = logging.getLogger(__name__)


def get_error_response(message, status_code=400):
    response = json.jsonify({'error': message})
    response.status_code = status_code
    return response


def is_json(func):
    @functools.wraps(func)
    def _is_json(*args, **kw):
        if not request.get_json():
            return get_error_response('request is not JSON')
        return func(*args, **kw)
    return _is_json


def authenticate(func):
    @functools.wraps(func)
    def _auth(*args, **kw):
        event = request.get_json()
        logger.debug("received %s", event)
        logger.debug("configuratioon token: %s", CONF.get_value("hangouts-api-key"))

        if event.get('token') != CONF.get_value("hangouts-api-key"):
            return get_error_response('Wrong token', 401)
        return func(*args, **kw)
    return _auth


def validate(schema):
    def _inner(func):
        @functools.wraps(func)
        def _validate(*args, **kw):
            body = request.get_json()
            try:
                jsonschema.validate(body, schema)
            except jsonschema.ValidationError as ex:
                response = get_error_response(str(ex))
                return response
            return func(*args, **kw)
        return _validate
    return _inner