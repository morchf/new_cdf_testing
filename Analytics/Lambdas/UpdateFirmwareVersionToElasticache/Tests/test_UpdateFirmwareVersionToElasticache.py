import Analytics.Lambdas.UpdateFirmwareVersionToElasticache.LambdaCode.UpdateFirmwareVersionToElasticache as UpdateFirmwareVersionToElasticache

# If the lambda executes completely it will log "Updating the elasticache with firmware version and date is complete".
# If there is any exception it will log "There is an Exception while running the lambda" on failure.

# test success
def test_lambda_handler():
    status = UpdateFirmwareVersionToElasticache.lambda_handler(None, None)
    assert status == 200
