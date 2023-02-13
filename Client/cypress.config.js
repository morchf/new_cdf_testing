/* eslint-disable import/no-extraneous-dependencies */
const { defineConfig } = require('cypress');
const {
  beforeRunHook,
  afterRunHook,
} = require('cypress-mochawesome-reporter/lib');

module.exports = defineConfig({
  reporter: 'cypress-multi-reporters',
  reporterOptions: {
    reporterEnabled: 'cypress-mochawesome-reporter, mocha-junit-reporter',
    cypressMochawesomeReporterReporterOptions: {
      reportDir: 'cypress/reports/html',
      charts: true,
      reportPageTitle: 'My Test Suite',
      embeddedScreenshots: true,
      inlineAssets: true,
    },
    mochaJunitReporterReporterOptions: {
      mochaFile: 'cypress/reports/junit/results-[hash].xml',
    },
  },
  video: false,
  chromeWebSecurity: false,
  e2e: {
    defaultCommandTimeout: 8000,
    experimentalSessionAndOrigin: true,
    viewportWidth: 1280,
    viewportHeight: 720,
    retries: 2,

    setupNodeEvents(on, config) {
      require('cypress-mochawesome-reporter/plugin')(on);
      
      on('before:run', async (details) => {
        await beforeRunHook(details);
      });

      on('after:run', async () => {
        await afterRunHook();
      });

      require('@cypress/grep/src/plugin')(config);
      return config;
      
    },
  },
});
