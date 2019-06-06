# -*- coding: utf-8 -*-

# This is a simple Hello World Alexa Skill, built using
# the decorators approach in skill builder.
import logging
import json
import aws_client

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name, request_util
from ask_sdk_model.ui import SimpleCard

sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

with open('strings.json') as f:
    strings = json.loads(f.read())


def keys_in_dict(o, k):
    """
    :param o: object to be assessed
    :param k: keys to be found in the object
    :return: True/False, based on if object contains all keys of k
    """
    return all(_ in o for _ in k)


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """
    Handler for Skill Launch.
    :param handler_input:
    :return:
    """
    object_type = handler_input.request_envelope.request.object_type
    intent_strings = strings[object_type][handler_input.request_envelope.request.locale]
    speech_text = intent_strings["welcome"]["content"]
    card_title = intent_strings["welcome"]["title"]
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr["last_request"] = {
        "retry_title": card_title,
        "retry_speech": intent_strings["welcome"]["retry"]
    }
    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard(card_title, speech_text)).set_should_end_session(False).response


@sb.request_handler(can_handle_func=is_intent_name("MeetingIntent"))
def meeting_intent_handler(handler_input):
    """
    Handler for MeetingIntent. This is the main functionality handler for this skill.
    Interacts with DynamoDB "bodoni-employees" via aws_client.BodoniDynamoHelper
    Sends SNS SMS message via aws_client.BodoniEngagementHelper().send_alert_to_phone
    SES messages via aws_client.BodoniEngagementHelper().send_alert_to_email

    :param handler_input:
    :return: response_object
    """

    # References used to improve readability of code. Using these aliases means we don't need to reference long object
    # paths throughout the code, such as session_attr[slot].
    intent_name = handler_input.request_envelope.request.intent.name
    intent_strings = strings[intent_name][handler_input.request_envelope.request.locale]
    session_attr = handler_input.attributes_manager.session_attributes
    end_session = True

    # On every invocation of the intent, check to see if a new slot has been fulfilled.
    slots = ["customer", "company", "employee", "department", "employee_last_name"]
    for key in slots:
        if request_util.get_slot(handler_input, key).value:
            session_attr[key] = request_util.get_slot(handler_input, key).value

    logging.info(session_attr)
    dynamo_interface = aws_client.BodoniDynamoHelper()
    resp = dynamo_interface.query_table_by_gsi(session_attr)

    logging.info("DynamoDB Response:")
    logging.info(resp)

    if len(resp) == 1:
        # If the length of the response is 1, only one employee was returned from Dynamo.

        # SNS SMS Delivery
        resp = resp[0]
        sms_params = dict({
            "text": intent_strings["sms"]["text"].format(
                customer=session_attr["customer"].title(),
                company=session_attr["company"].title()),
            "number": resp["mobile"]
        })
        contact_interface = aws_client.BodoniEngagementHelper()
        contact_interface.send_alert_to_phone(
            phone_number=sms_params["number"],
            message=sms_params["text"])

        # SES Email Delivery
        message_dict = intent_strings["ses"]
        message_dict["to"] = resp["email"]
        message_dict["text"] = message_dict["text"].format(
            employee=session_attr["employee"].title(),
            customer=session_attr["customer"].title(),
            company=session_attr["company"].title())
        contact_interface.send_alert_to_email(message_dictionary=message_dict)
        card_title = intent_strings["intent_fulfilled"]["title"]
        speech_text = intent_strings["intent_fulfilled"]["content"].format(
            customer=session_attr["customer"].title(),
            company=session_attr["company"].title(),
            employee=session_attr["employee"].title(),
            employee_last_name=session_attr["employee_last_name"].title(),
            department=session_attr["department"])
    elif len(resp) == 0:
        # Employee not found
        card_title = intent_strings["err_employee_not_found"]["title"]
        speech_text = intent_strings["err_employee_not_found"]["content"].format(
            employee=session_attr["employee"],
            employee_last_name=session_attr["employee_last_name"])
    else:
        # More than one entry was returned from DDB.
        # This could happen if there was multiple people with the same name and department.
        card_title = intent_strings["err_employee_not_found"]["title"]
        speech_text = intent_strings["err_employee_not_found"]["content"].format(
            employee=session_attr["employee"],
            employee_last_name=session_attr["employee_last_name"])

    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard(card_title, speech_text)).set_should_end_session(end_session).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """
    Handler for Help Intent.
    :param handler_input:
    :return:
    """
    intent_strings = strings["GeneralIntent"][handler_input.request_envelope.request.locale]["hello"]
    return handler_input.response_builder.speak(intent_strings["content"])\
        .ask(intent_strings["content"])\
        .set_card(SimpleCard(intent_strings["title"], intent_strings["content"]))\
        .response


@sb.request_handler(can_handle_func=lambda handler_input:
                    is_intent_name("AMAZON.CancelIntent")(handler_input)
                    or is_intent_name("AMAZON.StopIntent")(handler_input))
def cancel_and_stop_intent_handler(handler_input):
    """
    Single handler for Cancel and Stop Intent.
    :param handler_input:
    :return:
    """
    speech_text = "Goodbye!"
    return handler_input.response_builder.speak(speech_text).set_card(
        SimpleCard("Bodoni University", speech_text)).response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    """
    AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    :param handler_input:
    :return:
    """
    intent_strings = strings["FallbackIntent"][handler_input.request_envelope.request.locale]["error"]
    handler_input.response_builder.speak(intent_strings["content"]).ask(intent_strings["reprompt"])
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """
    Handler for Session End.
    :param handler_input:
    :return:
    """
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """
    Catch all exception handler, log exception and
    respond with custom message.
    :param handler_input:
    :param exception:
    :return:
    """
    logger.error(exception, exc_info=True)
    speech = "Sorry, there was some problem. Please try again!"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


handler = sb.lambda_handler()
