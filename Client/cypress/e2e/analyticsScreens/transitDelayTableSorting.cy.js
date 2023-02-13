import RouteTable from '../../pageObjects/routeTable';

describe('TransitDelayRouteTable', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Route Table', () => {
    const table = new RouteTable();
    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    // Transit Delay L1 Screen
    cy.title().should('eq', 'GTT Smart Cities');
    cy.url().should('include', 'transit-delay');

    // Verify Avg. Signal Delay Column is sorted in descending order by default and verify down sort arrow is active
    table
      .avgSignalDelaySorters()
      .should(
        'have.class',
        'anticon anticon-caret-down ant-table-column-sorter-down active'
      );

    table.routeTable().then(($table) => {
      if ($table.find('tr').length >= 2) {
        for (let i = 1; i <= 5; i++) {
          const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[2])[1]`;

          let oldTotalInDesc = 10000;

          cy.xpath(xpathVal).each(($el) => {
            const signalDelayDesc = $el.text();
            let newTotalInDesc;

            cy.log(`metricsTotal delayTime = ${signalDelayDesc}`);
            if (signalDelayDesc.includes('m') && signalDelayDesc.includes('s')) {
              const words = signalDelayDesc.split(' ');
              const minutes = +words[0].replace('m', '');
              const seconds = +words[1].replace('s', '');
              newTotalInDesc = minutes * 60 + seconds;

              cy.log(`minues and seconds = ${newTotalInDesc}`);
            } else if (signalDelayDesc.includes('m')) {
              const minutes = +signalDelayDesc.replace('m', '');
              newTotalInDesc = minutes * 60;

              cy.log(`minues and seconds = ${newTotalInDesc}`);
            } else {
              newTotalInDesc = +signalDelayDesc.replace('s', '');
              cy.log(`total seconds = ${newTotalInDesc}`);
            }

            if (oldTotalInDesc) {
              expect(newTotalInDesc).lte(oldTotalInDesc);
            }
            oldTotalInDesc = newTotalInDesc;
          });
        }

        // Check Avg. Signal Delay column sort in ascending order
        table.avgSignalDelayAscending().should('be.visible');
        table.avgSignalDelayAscending().click({ force: true });
        table.avgSignalDelayAscending().click({ force: true });

        for (let i = 1; i <= 5; i++) {
          const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[2])[1]`;

          let oldTotalInSeconds = 0;

          cy.xpath(xpathVal).each(($el) => {
            const signalDelay = $el.text();
            let newTotalInSeconds;

            cy.log(`metricsTotal delayTime = ${signalDelay}`);
            if (signalDelay.includes('m') && signalDelay.includes('s')) {
              const words = signalDelay.split(' ');
              const minutes = +words[0].replace('m', '');
              const seconds = +words[1].replace('s', '');
              newTotalInSeconds = minutes * 60 + seconds;

              cy.log(`minues and seconds = ${newTotalInSeconds}`);
            } else if (signalDelay.includes('m')) {
              const minutes = +signalDelay.replace('m', '');
              newTotalInSeconds = minutes * 60;

              cy.log(`minues and seconds = ${newTotalInSeconds}`);
            } else {
              newTotalInSeconds = +signalDelay.replace('s', '');
              cy.log(`total seconds = ${newTotalInSeconds}`);
            }

            if (oldTotalInSeconds) {
              expect(newTotalInSeconds).gte(oldTotalInSeconds);
            }
            oldTotalInSeconds = newTotalInSeconds;
          });
        }

        // Click route name to sort in ascending order and verify up sort arrow is active
        table.routeNameAscending().should('be.visible');
        table.routeNameAscending().click({ force: true });

        for (let i = 1; i <= 5; i++) {
          const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[1])[1]`;

          let oldRouteVal = 0;

          cy.xpath(xpathVal).each(($el) => {
            const rowVal = $el.text();

            cy.log(`ROUTE BEFORE  = ${rowVal}`);
            const newRouteVal = +rowVal.replace(/[^\d.-]/g, '');
            cy.log(`ROUTE AFTER = ${newRouteVal}`);

            if (oldRouteVal) {
              expect(newRouteVal).gte(oldRouteVal);
            }
            oldRouteVal = newRouteVal;
          });
        }
        table
          .routeNameSorters()
          .should(
            'have.class',
            'anticon anticon-caret-up ant-table-column-sorter-up active'
          );

        // Click Signal Delay(% of travel time) in descending order
        table.signalDelayPercentage().should('be.visible');
        table.signalDelayPercentage().click({ force: true });
        cy.wait(3000);
        table.signalDelayPercentage().click({ force: true });

        for (let i = 1; i <= 5; i++) {
          const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[3])[1]`;

          let oldTotalInPercentage = 10000;

          cy.xpath(xpathVal).each(($el) => {
            const signalDelayPercentage = $el.text();
            let newTotalInPercentage;

            cy.log(`metricsTotal delayTime = ${signalDelayPercentage}`);
            if (
              signalDelayPercentage.includes('m') &&
              signalDelayPercentage.includes('s')
            ) {
              const words = signalDelayPercentage.split(' ');
              const minutes = +words[0].replace('m', '');
              const seconds = +words[1].replace('s', '');
              newTotalInPercentage = minutes * 60 + seconds;

              cy.log(`minues and seconds = ${newTotalInPercentage}`);
            } else if (signalDelayPercentage.includes('m')) {
              const minutes = +signalDelayPercentage.replace('m', '');
              newTotalInPercentage = minutes * 60;

              cy.log(`minues and seconds = ${newTotalInPercentage}`);
            } else {
              newTotalInPercentage = +signalDelayPercentage.replace('%', '');
              cy.log(`total seconds = ${newTotalInPercentage}`);
            }
            if (oldTotalInPercentage) {
              expect(newTotalInPercentage).lte(oldTotalInPercentage);
            }
            oldTotalInPercentage = newTotalInPercentage;
          });
        }
        
        // Sort Dwell Time in ascending order
        table.avgDwellTime().should('be.visible');
        table.avgDwellTime().click({ force: true });

        for (let i = 1; i <= 5; i++) {
          const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[4])[1]`;

          let oldDwellTime;

          cy.xpath(xpathVal).each(($el) => {
            const dwellTime = $el.text();
            let newDwellTime;

            cy.log(`metricsTotal delayTime = ${dwellTime}`);
            if (dwellTime.includes('m') && dwellTime.includes('s')) {
              const words = dwellTime.split(' ');
              const minutes = +words[0].replace('m', '');
              const seconds = +words[1].replace('s', '');
              newDwellTime = minutes * 60 + seconds;

              cy.log(`minues and seconds = ${newDwellTime}`);
            } else if (dwellTime.includes('m')) {
              const minutes = +dwellTime.replace('m', '');
              newDwellTime = minutes * 60;

              cy.log(`minues and seconds = ${newDwellTime}`);
            } else {
              newDwellTime = +dwellTime.replace('s', '');
              cy.log(`total seconds = ${newDwellTime}`);
            }

            if (oldDwellTime) {
              expect(newDwellTime).gte(oldDwellTime);
            }
            oldDwellTime = newDwellTime;
          });
        }
      }
    })
  });
});
