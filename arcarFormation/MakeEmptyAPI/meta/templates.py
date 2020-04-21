#!/usr/bin/python3
# -*- encoding:utf-8 -*-


template_properties_lambda_default = {
    "Runtime": "python3.7",
    "Timeout": 30,
    "Role": {
        "Ref": "PrincipalRole"
    },
    "VpcConfig": {
        "SecurityGroupIds": [
            {
                "Ref": "PrincipalSecurityGroupIds"
            }
        ],
        "SubnetIds": [{
            "Ref": "SubNetsIds"
        }]
    },
    "Layers": [
        {
            "Fn::Select": [
                "0",
                {
                    "Ref": "Layers"
                }
            ]
        },
        {
            "Fn::Select": [
                "1",
                {
                    "Ref": "Layers"
                }
            ]
        },
        {
            "Fn::Select": [
                "2",
                {
                    "Ref": "Layers"
                }
            ]
        }
    ],
    "Tags": [
        {
            "Key": "Product",
            "Value": "Bontu"
        }
    ],
    "Environment": {
        "Variables": {
            "ENVIRONMENT": {
                "Ref": "Environ"
            },
            "BUCKET": {
                "Ref": "BucketDocuments"
            },
            "LOG_LEVEL": "2",
            "TREND_AP_READY_TIMEOUT": 30,
            "TREND_AP_TRANSACTION_FINISH_TIMEOUT": 10,
            "TREND_AP_MIN_REPORT_SIZE": 1,
            "TREND_AP_INITIAL_DELAY_MS": 1,
            "TREND_AP_MAX_DELAY_MS": 100,
            "TREND_AP_HTTP_TIMEOUT": 5,
            "TREND_AP_PREFORK_MODE": False,
            "TREND_AP_CACHE_DIR": "/tmp/trend_cache",
            "TREND_AP_LOG_FILE": "STDERR"
        }
    }
}

parameter_default = {
    "BucketName": {
        "Type": "String",
        "Description": "Name of principal bucket"
    },
    "BucketDocuments": {
        "Type": "String",
        "Description": "Name of bucket where is stored the documents"
    },
    "Environ": {
        "Type": "String",
        "Description": "Name of the environ stage"
    },
    "PrincipalRole": {
        "Type": "String",
        "Description": "Arn of the principal role"
    },
    "PrincipalSecurityGroupIds": {
        "Type": "String",
        "Description": "Id of security group"
    },
    "SubNetsIds": {
        "Type": "CommaDelimitedList",
        "Description": "Id of sub nets"
    },
    "Layers": {
        "Type": "CommaDelimitedList"
    }
}

master_template = {}

api_cloud_formation_template = {}

method_template = {
    "post": {
        "consumes": [
            "application/json"
        ],
        "produces": [
            "application/json"
        ],
        "parameters": [
            {
                "in": "body",
                "name": "Empty",
                "required": True,
                "schema": {
                    "$ref": "#/definitions/Empty"
                }
            }
        ],
        "responses": {
            "200": {
                "description": "200 response",
                "schema": {
                    "$ref": "#/definitions/Empty"
                },
                "headers": {
                    "Access-Control-Allow-Origin": {
                        "type": "string"
                    },
                    "Access-Control-Allow-Methods": {
                        "type": "string"
                    },
                    "Access-Control-Allow-Headers": {
                        "type": "string"
                    }
                }
            }
        },
        "security": [
            {
                "auth_users": []
            },
            {
                "api_key": []
            }
        ],
        "x-amazon-apigateway-integration": {
            "uri": {
                "Fn::Join": [
                    "",
                    [
                        "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/",
                        {
                            "Fn::GetAtt": [
                                "ApiCLient",
                                "Outputs.registroArchivosArn"
                            ]
                        },
                        "/invocations"
                    ]
                ]
            },
            "credentials": {
                "Fn::Join": [
                    "",
                    [
                        "arn:aws:iam::",
                        {
                            "Ref": "AWS::AccountId"
                        },
                        ":role/RolApiGetewayInvoke"
                    ]
                ]
            },
            "responses": {
                "default": {
                    "statusCode": "200",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Methods": "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,authorizationtoken,usertype,Userid,Client,user,Solicitud'",
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                }
            },
            "passthroughBehavior": "when_no_match",
            "httpMethod": "POST",
            "contentHandling": "CONVERT_TO_TEXT",
            "type": "aws_proxy"
        }
    },
    "options": {
        "consumes": [
            "application/json"
        ],
        "produces": [
            "application/json"
        ],
        "responses": {
            "200": {
                "description": "200 response",
                "schema": {
                    "$ref": "#/definitions/Empty"
                },
                "headers": {
                    "Access-Control-Allow-Origin": {
                        "type": "string"
                    },
                    "Access-Control-Allow-Methods": {
                        "type": "string"
                    },
                    "Access-Control-Allow-Headers": {
                        "type": "string"
                    }
                }
            }
        },
        "x-amazon-apigateway-integration": {
            "responses": {
                "default": {
                    "statusCode": "200",
                    "responseParameters": {
                        "method.response.header.Access-Control-Allow-Methods": "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'",
                        "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,authorizationtoken,usertype,Userid,Client,user,Solicitud'",
                        "method.response.header.Access-Control-Allow-Origin": "'*'"
                    }
                }
            },
            "passthroughBehavior": "when_no_match",
            "requestTemplates": {
                "application/json": "{\"statusCode\": 200}"
            },
            "type": "mock"
        }
    }
}

new_lambda_template = {
    "template": "baseTemplate.json",
    "function_config": {
        "Code": "",
        "FunctionName": "",
        "Handler": "lambda_function.lambda_handler"
    }
}

CODE_LAMBDA_TEMPLATE = '''
#!/usr/bin/python3
# -*- encoding:utf-8 -*-

import tools_lambda
import traceback


LOGGER = tools_lambda.get_logger("{name_lambda}")


@tools_lambda.LambdaResponseWebDefault
@tools_lambda.NotificationError
def lambda_handler(event, context):
    try:
        result = "some result"
    except Exception as details:
        LOGGER.warning(details)
        LOGGER.warning(traceback.format_exc())
        return None, 500
    else:
        return result, 200

'''
