# example tests. To run these tests, uncomment this file along with the example
# resource in cdk/cdk_stack.py
def test_sqs_queue_created():
    pass
    # app = core.App()
    # stack = CdkStack(app, "cdk")
    # template = assertions.Template.from_stack(stack)


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
