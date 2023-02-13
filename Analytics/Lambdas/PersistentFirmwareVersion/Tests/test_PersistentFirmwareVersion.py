import Analytics.Lambdas.PersistentFirmwareVersion.LambdaCode.PersistentFirmewareVersion as PersistentFirmewareVersion


# check if the file is stored in the new firmware bucket and the program runs to completions.
def test_lambda_handler():
    message = PersistentFirmewareVersion.lambda_handler(None, None)
    assert message == 200
