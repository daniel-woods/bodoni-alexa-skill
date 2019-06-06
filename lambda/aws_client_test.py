import unittest
import aws_client
import random

SEND_SMS = True
SEND_EMAIL = True


class BodoniDynamoHelper(unittest.TestCase):
    def sample_output(self):
        return {
            "firstname": "Dan",
            "department": "It",
            "surname": "Woods",
        }

    def sample_query(self):
        input_data = {
            "employee_last_name": "woods",
            "company": "amazon",
            "employee": "Dan",
            "department": "it",
            "customer": "Juan"
        }
        dynamo_interface = aws_client.BodoniDynamoHelper()
        resp = dynamo_interface.query_table_by_gsi(input_data)
        if len(resp) == 1:
            resp = resp[0]
        return resp

    def test_query_table_by_gsi(self):
        class_name = self.__class__.__name__
        print("START: {}".format(class_name))
        resp = self.sample_query()
        output = self.sample_output()
        if len(resp) == 1:
            resp = resp[0]
        print(resp)
        self.assertEqual(resp['firstname'], output['firstname'])
        self.assertEqual(resp['department'], output['department'])
        self.assertEqual(resp['surname'], output['surname'])
        self.dynamo_response = resp
        print("END: {}".format(class_name))

    def test_send_alert_to_phone(self):
        if SEND_SMS:
            class_name = self.__class__.__name__
            print("START: {}".format(class_name))
            dynamo_resp = self.sample_query()
            random_str = str(random.randint(99999, 999999))
            phone_number = dynamo_resp["mobile"]
            contact_interface = aws_client.BodoniEngagementHelper()
            resp = contact_interface.send_alert_to_phone(
                phone_number=phone_number,
                message="Unittest message. Please ignore. {}".format(random_str))
            print(resp)
            self.assertEqual(("MessageId" in resp), True)
            class_name = self.__class__.__name__
            print("END: {}".format(class_name))

    def test_send_email(self):
        if SEND_EMAIL:
            class_name = self.__class__.__name__
            print("START: {}".format(class_name))
            dynamo_resp = self.sample_query()
            random_str = str(random.randint(99999, 999999))
            message_dict = dict({
                "text": "Hi {employee},\n\n{customer}, from {company} is waiting for you in the reception. Please come "
                        "and pick your visitor for your meeting.\n\nRegards,\nVirtual Assistant" + "  " + random_str,
                "from": "Virtual Assistant <dan@woodz.ie>",
                "subject": "Alert - Your guest has arrived!"
            })
            message_dict["to"] = dynamo_resp["email"]
            contact_interface = aws_client.BodoniEngagementHelper()
            resp = contact_interface.send_alert_to_email(
                message_dictionary=message_dict)
            print(resp)
            self.assertEqual(("MessageId" in resp), True)
            print("END: {}".format(class_name))


if __name__ == '__main__':
    unittest.main()
