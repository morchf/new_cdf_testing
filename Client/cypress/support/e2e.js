/* eslint-disable import/no-extraneous-dependencies */
// ***********************************************************
// This example support/e2e.js is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can change the location of this file or turn off
// automatically serving support files with the
// 'supportFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

import './commands';
import chaiJsonSchema from 'chai-json-schema';
 
chai.use(chaiJsonSchema);

const registerCypressGrep = require('@cypress/grep')

registerCypressGrep()

require('cypress-xpath');
require('cypress-mochawesome-reporter/register');

Cypress.on('uncaught:exception', (err, runnable) => false);
