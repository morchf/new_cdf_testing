var express = require('express');
var router = express.Router();

// the "landing" page
router.get('/', function(req, res, next) {
  var loggedIn = req.isAuthenticated()
  res.render('index', { title: 'Express', loggedIn });
});

// a public page that doesn't require authentication
router.get('/public', function(req, res, next) {
  res.render('public', { title: 'Express' });
});

// a private page that requires authentication
router.get('/user', function(req, res, next) {
  if (req.isAuthenticated()) {
    res.render('user', { title: 'Express' });
  } else {
    res.redirect('/')
  }
});

module.exports = router;
