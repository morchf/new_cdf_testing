var express = require('express');
var router = express.Router();

router.get('/profile', function(req, res, next) {
  if (req.isAuthenticated()) {
    res.json(req.user)
  } else {
    res.sendStatus(401);
  }
});

module.exports = router;
