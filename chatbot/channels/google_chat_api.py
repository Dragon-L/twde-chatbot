import logging

from flask import Flask, request, json

from chatbot.channels import middlewares
from chatbot.config import CONF
from chatbot.nlp_models import dialog

logger = logging.getLogger(__name__)
app = Flask(__name__)


def get_success_response(message):
    logger.debug("sending %s", message)
    return json.jsonify({'text': message})


SCHEMA = {
    "type": "object",
    "required": ["type", "token"],
    "properties": {
        "type": {"type": "string"},
        "token": {"type": "string"},
        "message": {
            "type": "object",
            "required": ["text", "thread", "sender"],
            "properties": {
                "text": {"type": "string"},
                "sender": {
                    "type": "object",
                    "required": ["email"],
                    "properties": {
                        "email": {"type": "string", "minLength": 1},
                    },
                },
                "thread": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                    }
                }
            }
        }
    }
}


@app.route("/" + CONF.get_value("messenger-endpoint"), methods=['POST'])
@middlewares.is_json
@middlewares.authenticate
@middlewares.validate(SCHEMA)
@middlewares.fill_session
def on_event():
    """Handles an event from Hangouts Chat."""
    event = request.get_json()

    if event.get('type') == 'ADDED_TO_SPACE':
        logger.debug('Retrieve and send welcome text')

        message = dialog.get_welcome_message(
            dialog.get_agent(),
        )
        response = get_success_response(message)
    elif event.get('type') == 'MESSAGE':
        message_text = event['message']['text']
        sender_id = event['message']['thread']['name']

        logger.debug('Retrieve response for: %s', message_text)
        message = dialog.handle_message_input(
            dialog.get_agent(),
            message_text,
            sender_id=sender_id,
        )
        response = get_success_response(message)
    else:
        response = middlewares.get_error_response('unknown message type {}'.format(event["type"]))
    return response


@app.route("/health", methods=['GET'])
def health():
    logger.info("health checked received")
    return json.jsonify({})
