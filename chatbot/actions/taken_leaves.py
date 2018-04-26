import datetime
import logging
from functools import reduce

from rasa_core.actions import Action

from chatbot.actions import employee
from chatbot.backend import backend_api
from chatbot.backend.errors import BackendError

logger = logging.getLogger(__name__)
VALID_LEAVES = ['Annual Leave', 'Personal Development Leave']


def _leave_is_within_year(leave, year):
    start_within_year = datetime.datetime.strptime(leave['period']['startsOn'], '%d-%m-%Y').year == year
    end_within_year = datetime.datetime.strptime(leave['period']['endsOn'], '%d-%m-%Y').year == year
    is_valid_leave = leave['type'] in VALID_LEAVES
    return is_valid_leave and (start_within_year or end_within_year)


def _leave_duration_days(leave, year):
    start = datetime.datetime.strptime(leave['period']['startsOn'], '%d-%m-%Y')
    if start.year < year:
        start = datetime.datetime(year, 1, 1)

    end = datetime.datetime.strptime(leave['period']['endsOn'], '%d-%m-%Y')
    if end.year > year:
        end = datetime.datetime(year, 12, 31)

    delta = (end - start)
    return delta.days + 1


def get_leaves_taken(employee, year):
    valid_leaves = list(filter(lambda leave: _leave_is_within_year(leave, year),
                               backend_api.get_leaves(employee.get('employeeId'))))
    return reduce(lambda acc, leave: acc + _leave_duration_days(leave, year), valid_leaves, 0)


class ActionLeaveTaken(Action):
    def name(self):
        return 'action_leave_annual_taken'

    def run(self, dispatcher, tracker, domain):
        employee_info = employee.get_employee(tracker.sender_id, dispatcher)
        if not employee_info:
            return []

        current_year = datetime.datetime.now().year

        try:
            taken_leaves = get_leaves_taken(employee_info, current_year)
            dispatcher.utter_template(
                "utter_leave_annual_taken",
                taken_leaves=taken_leaves,
            )
        except BackendError as ex:
            logger.warning("Leave Backend not available %s", ex)
            dispatcher.utter_template('utter_backend_not_running')
