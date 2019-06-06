Bodoni University Alexa Skill
=======================================================================================
The following skill is a virtual reception assistant. The main use case for this skill is to allow visitors to a building to automatically sign themselves in to a registration system and alert their host that they have arrived on site. The skill is built using the Alexa Skills Kit and AWS. The project incorporates a full CI/CD pipeline allowing for changes to be tested and integrated as soon as they are published to the Git repository. Continuous Intengration and Delivery is provided by the AWS CodeSuite (CodePipline, CodeBuild, CodeDeploy) and version control is managed by CodeCommit, an AWS-integerated private Git repositiory solution.

AWS Service Dependencies
------------------------
* **CloudFormation** — Used in conjunction with SAM to layout the project and build the associated resources.
* Serverless Application Model (SAM) - Used to create the Lambda Function. Allows testing through the SAM CLI.
* **AWS Code Suite:**
    * **CodeCommit** — A private Git repository that tracks changes to the project.
    * **CodeBuild** — Builds the deployment package and CloudFormation template for function deployment. Runs the unit tests specified within the lambda directory.
    * **CodeDeploy** — Executes the CloudFormation change sets. Deploys the skill to the Alexa Service.
    * **CodePipeline** — Automates the deployment of changes, originating from commits to the CodeCommit repository.
* **DynamoDB** — Acts as the source for employee data, allowing queries to be made for employees. Global Secondary Index is used to allow for efficent user querying when the data set is large. The allows the project to avoid read-expensive Scan operations in favour of Queries.
    * **Primary Key** — username
    * **Global Secondary Index** — surname-firstname
* **Lambda** — The serverless compute for the project. Takes in JSON events from the Alexa Service. Parses the JSON for the slot fulfillment information and makes a request to DynamoDB using this data. If the request returns a single item, the function will call SNS/SES to deliver notifications to the end user.
* **SNS** — Used for SMS mobile messaging. Uses the [E.164](https://www.twilio.com/docs/glossary/what-e164) formatted numbers. Sends message using a string template located in strings.json.
* **SES** — Used to send an email notification to the requested user.

Project Layout
-----------
* **[skill.json](https://developer.amazon.com/docs/smapi/skill-manifest.html)** — contains the skill manifest that provides Alexa with the skill's metadata. Contains parameters such as:
* **[interactionModels](https://developer.amazon.com/docs/alexa-voice-service/interaction-model.html)** — contains interaction model files in JSON format. The interaction model defines the functionality of the skill, listing the invocation names, the intents and the slots accepted in utterances. The interactionModels directory contains the localization model for specific languages. Currently this skill only supports "en-US" as seen in the en-US.json file
* **lambda/** — the parent folder that contains the code of all Lambda functions of this skill. This tracks the files that will be added to the Lambda function's deployment package.
    * **aws_client.py** — contains the clients for interactions with AWS services, such as DynamoDB (bodoni-employees), SNS (SMS messaging) and SES (email deliverability).
    * **aws_client_test.py** — [Python Unit tests](https://docs.python.org/3/library/unittest.html) implementation for aws_client.py.
    * **requirements.txt** — contains a list of dependencies to be installed.
    * **skill_handler.py** — contains the function code that will be executed once the Alexa service has filled the elicit intent slots. Calls the aws_client if the data passes validation.
    * **skill_handler_test.py** — [Python Unit tests](https://docs.python.org/3/library/unittest.html) implementation for skill_handler.py.
    * **strings.json** — contains locale-friendly strings for supported languages.
    * **tests.json** — contains input and expected output for the unit tests.
* **buildspec.yml** — used by AWS CodeBuild to package the Lambda function code to be deployed by CodePipeline using CloudFormation.
* **template.yml** — the template with reference to Lambda function code to be deployed by CloudFormation.
* **README.md** — this file.

Setup
-----
* Create an AWS account in order to host the back end infrastructure.
* Create an Alexa Developer account to allow for skill deployment and hosting.
* Create an AWS CodeStar project using the Alexa Skills template. This will automatically create a repository, build stage and deployment stage within your pipeline.
* Clone the project into an CodeStar project.
    * Ensure that your CodeDeploy stage has access to your Alexa Developer account.
* Create a static [Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html) to host the Alexa Skills Kit and Boto3/Botocore. The purpose of the Lambda Layer is to avoid re-deploying these dependencies for every commit to the project. Using a Lambda Layer increases the efficiency of your Lambda environment's code repository.
    * Alternatively, remove the Lambda Layer from the function configuration in the template.yml
    * In the buildspec.yml, change the PIP command to install the requirements.txt to the lambda directory.
        ```
        pip install -r lambda/requirements.txt -t lambda/
        ```
* Once deployed, the skill should be available from your Alexa Developer account. Head to the [Alexa Skills Development Console](https://developer.amazon.com/alexa/console/ask/) to test.

Cost Analysis
-------------


Usage
------------------
* Invoke the skill using the invocation name of "reception"
    * **User →** "Alexa, open reception"
* The Alexa service will invoke the [LaunchRequest](https://developer.amazon.com/docs/custom-skills/request-types-reference.html#launchrequest) intent, which will be passed to the AWS Lambda function backed. The function will respond with a localized greeting, stored in strings.json.
    * **Alexa →** "Welcome to Bodoni University. How can I help?"
* The user can now either state that they have a meeting or inform Alexa of their name. This is dynamic slot fulfillment. As the slots are elicit, they need to be assigned before the Alexa Service can pass the request to the Lambda backend. See [here](https://developer.amazon.com/blogs/alexa/post/5fe7565a-9547-4e03-be36-6c62ed356d57/dynamically-elicit-slots-during-dialog-management-based-on-previously-given-slot-values) for more information on dynamic elicit slots.
    * **User →** "I have a meeting with *Dan*"
* Without needing to invoke the Lambda function, the Alexa service will fill the slot {employee} as the customer has just supplied this in the opening statement. Alexa will then try to fulfill the rest of the required slots to fulfill the intent. In order of Alexa's preference, they are {customer}, {company}, {employee_last_name} and {department}.
    * **Alexa →** "Okay, What's your name and which company are you from?"
* The user can reply to this question either by fulfilling one or both slots requested (what's your name) and (which company are you from). A response to this might be:
    * **User →** "My name is *Alice* and I work for *ABC*"
* As the three primary slots (customer, employee and company) have been fulfilled. Alexa will continue to flow the slot fulfillment strategy outlined in the interaction model.
    * **Alexa →** "Okay *Alice*. Can I get *Dan's* last name and their department?"
* Here the user can respond with either the last name, the department or both. Again these are elicit slots which can be dynamically filled in the order favoured by the end user.
    * **User →** "his last name is *Woods* and he is from *Premium Support*"
* At this stage, Alexa has filled all the required slot values. The execution can now pass to the Lambda function backend for processing. Here, the Lambda function's skills_handler.py will create a DynamoDB database connection (through the aws_client.py interface). If the query returns a single item, the skill will parse the JSON, pulling the email address and mobile number. If this succeeds, the skill will make requests to both SNS and SES to deliver the messages to both the mobile and email address.
    * **Alexa →** "Okay John from Amazon, I've contacted Dan Woods from Premium Support. Bye!"

Further Reading
---------------
**AWS Documentation** — Set Up a CI/CD Pipeline on AWS <br>
https://aws.amazon.com/getting-started/projects/set-up-ci-cd-pipeline/ <br>
**Alexa Skills Kit** — Request and Response JSON Reference <br>
https://developer.amazon.com/docs/custom-skills/request-and-response-json-reference.html <br>
**Alexa Skills Kit** — Dialog Interface Reference: Elicit Slots<br>
https://developer.amazon.com/docs/custom-skills/dialog-interface-reference.html#elicitslot <br>
**DynamoDB** — Best Practices for Querying and Scanning Data <br>
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html <br>
**DynamoDB** — General Guidelines for Secondary Indexes in DynamoDB <br>
https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes-general.html <br>
