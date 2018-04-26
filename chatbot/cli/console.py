#!/usr/bin/env python3
from rasa_core.channels.console import ConsoleInputChannel

from chatbot.nlp_models import dialog, train


def run():
    classificator = train.load_classificator()
    agent = dialog.load_agent(classificator)
    agent.handle_channel(ConsoleInputChannel())


if __name__ == '__main__':
    run()
