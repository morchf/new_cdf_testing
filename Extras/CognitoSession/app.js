var createError = require('http-errors');
var express = require('express');
var path = require('path');
var logger = require('morgan');
var session = require('express-session');
var passport = require('passport');
var OAuth2CognitoStrategy = require('./OAuth2CognitoStrategy');

var env = process.env;

var app = express();
var views = require('./routes/views');
var api = require('./routes/api');

// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'hbs');

// app-level middleware
app.use(logger('dev'));
app.use(express.static(path.join(__dirname, 'public')));
app.use(session({
  secret: env.EXPRESS_SESSION_SECRET,
  saveUninitialized: true,
  resave: false
}));

// passport (authentication middleware)
passport.use('cognito', new OAuth2CognitoStrategy({
  authorizationURL: env.OAUTH_AUTHZ_URL,
  tokenURL: env.OAUTH_TOKEN_URL,
  clientID: env.OAUTH_CLIENT_ID,
  clientSecret: env.OAUTH_CLIENT_SECRET,
  callbackURL: `http://localhost:${env.EXPRESS_PORT || 3000}/login`,
  state: true
},
function(accessToken, refreshToken, profile, done) {
  done(null, profile);
}));

// put user into session
passport.serializeUser(function(user, done) {
  done(null, user);
});

// retrieve user from session
passport.deserializeUser(function(user, done) {
  done(null, user);
});

app.use(passport.initialize());
app.use(passport.session());

// routes for authentication
app.get('/login',
  passport.authenticate('cognito', {
    successRedirect: '/',
    failureRedirect: '/'
  })
)

app.get('/logout', function (req, res) {
  req.logout();
  res.redirect('/');
})

// routes that serve pages
app.use('/', views);

// routes that make up the API
app.use('/api', api)

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;
