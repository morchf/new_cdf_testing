import cert_rotation_lambda


event = {'try':'one'}
context = 'something'
cert_rotation_lambda.cert_rotation_lambda(event, context)
