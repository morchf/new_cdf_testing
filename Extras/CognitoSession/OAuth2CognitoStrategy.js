const OAuth2Strategy = require('passport-oauth').OAuth2Strategy;
const AWS = require('aws-sdk');

const cognito = new AWS.CognitoIdentityServiceProvider();

class OAuth2CognitoStrategy extends OAuth2Strategy {
  userProfile(accessToken, done) {
    cognito.getUser(
      { AccessToken: accessToken },
      function (err, data) {
        if (err) {
          done(err, null);
        } else {
          const profile = {
            username: data.Username,
            attributes: data.UserAttributes
          }

          done(null, profile);
        }
      }
    );
  }
}

module.exports = OAuth2CognitoStrategy;
