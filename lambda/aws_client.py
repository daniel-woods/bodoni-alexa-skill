import boto3
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def convert_dynamo_response_to_json(data):
    # Parse the DDB Json into a Python Dict without type specifications
    if 'Item' in data:
        key = "Item"
    elif "Items" in data:
        key = "Items"
    else:
        return None, "error"
    boto3.resource('dynamodb')
    deserializer = boto3.dynamodb.types.TypeDeserializer()
    resp = []
    for i in range(data["Count"]):
        resp.append({k: deserializer.deserialize(v) for k, v in data[key][i].items()})
    return resp


class BodoniDynamoHelper:
    def __init__(self):
        self.region = "eu-west-1"
        self.table_name = "bodoni-employees"
        self.client = boto3.client("dynamodb", region_name=self.region)

    def query_table_by_gsi(self, attributes):
        table_name = self.table_name
        filter_expression = 'department = :department'
        key_condition_expression = 'surname = :surname AND firstname = :firstname'
        expression_attribute_values = {
            ":surname": {
                "S": attributes["employee_last_name"].title()
            },
            ":firstname": {
                "S": attributes["employee"].title()
            },
            ":department": {
                "S": attributes["department"].title()
            }
        }
        scan_index_forward = False

        logger.debug("DynamoDB Expressions Object")
        logger.debug(expression_attribute_values)

        response = self.client.query(
            TableName=table_name,
            IndexName="surname-firstname-index",
            KeyConditionExpression=key_condition_expression,
            ExpressionAttributeValues=expression_attribute_values,
            FilterExpression=filter_expression,
            ScanIndexForward=scan_index_forward
        )
        list_of_responses = convert_dynamo_response_to_json(data=response)
        logger.debug("DynamoDB Response Object")
        logger.debug(list_of_responses)
        return list_of_responses


class BodoniEngagementHelper:
    def __init__(self):
        self.region = "eu-west-1"
        self.sns_client = boto3.client("sns", region_name=self.region)
        self.ses_client = boto3.client("ses", region_name=self.region)

    def send_alert_to_phone(self, phone_number, message):
        logger.debug("SMS Parameters:")
        logger.debug(dict({"phone_number": phone_number, "message": message}))

        response = self.sns_client.publish(PhoneNumber=phone_number,
                                           Message=message)
        logger.debug("SMS Response:")
        logger.debug(response)
        return response

    def send_alert_to_email(self, message_dictionary):
        SENDER = message_dictionary['from']
        RECIPIENT = message_dictionary['to']
        SUBJECT = message_dictionary['subject']
        BODY_TEXT = message_dictionary['text']
        CHARSET = "UTF-8"

        logger.debug("SES Parameters:")
        logger.debug(message_dictionary)

        response = self.ses_client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )

        logger.debug("SES Response:")
        logger.debug(response)
        return response


