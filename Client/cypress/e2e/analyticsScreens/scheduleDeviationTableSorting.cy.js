import RouteTable from '../../pageObjects/routeTable';
import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';

describe('ScheduleDeviationRouteTable', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Route Table Sorting', () => {
    const table = new RouteTable();
    const page = new AnalyticsSideMenuPage();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    // Clicking on Schedule Deviation link in sidemenu navigates to Schedule Deviation L1 screen
    page.sideMenuScheduleDeviation().click();
    page.scheduleDeviationBreadcrumb().should('be.visible');
    page.scheduleDeviationBreadcrumb().should('contain.text', 'Schedule Deviation');
    page.headingTitle().should('contain.text', 'Schedule Deviation');

    // Verify OntimeArrivals Column is sorted in descending order by default and verify down sort arrow is active
    table
      .scheduleDeviationOntimeArrivalsSorters()
      .should(
        'have.class',
        'anticon anticon-caret-down ant-table-column-sorter-down active'
      );

    table.routeTable().then(($table) => {
      if ($table.find('tr').length >= 2) {
        for (let i = 1; i <= 5; i++) {
          const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[2])[1]`;
          const nextxpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i + 1}]//td[2])[1]`;

          cy.xpath(xpathVal).each(($el) => {
            let OnTimeArrivalsPercentage = $el.text().match(/(\d+)/)[0];
            cy.log(`On-time Arrival Percentage = ${OnTimeArrivalsPercentage}`)
            cy.xpath(nextxpathVal).each(($elm) => {
              i++
              const newOnTimeArrivalsPercentage = $elm.text().match(/(\d+)/)[0];
              cy.log(`New On-time Arrival Percentage = ${newOnTimeArrivalsPercentage}`);
              expect(+newOnTimeArrivalsPercentage).lte(+OnTimeArrivalsPercentage);
              OnTimeArrivalsPercentage = newOnTimeArrivalsPercentage;
            })
          });
        }
      }

      // Check % On-time Arrivals column sort in ascending order
      table.scheduleDeviationOntimeArrivalsAscending().should('be.visible');
      table.scheduleDeviationOntimeArrivalsAscending().click({ force: true });
      table.scheduleDeviationOntimeArrivalsAscending().click({ force: true });

      for (let i = 1; i <= 5; i++) {
        const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[2])[1]`;
        const nextxpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i + 1}]//td[2])[1]`;

        cy.xpath(xpathVal).each(($el) => {
          let OnTimeArrivals = $el.text().match(/(\d+)/)[0];
          cy.log(`Old On-Time Arrivals pecentage= ${OnTimeArrivals}`);
          cy.xpath(nextxpathVal).each(($el) => {
            i++;
            const newOnTimeArrivals = $el.text().match(/(\d+)/)[0];
            cy.log(`New On-Time Arrivals pecentage = ${newOnTimeArrivals}`);
            expect(+newOnTimeArrivals).gte(+OnTimeArrivals);
            OnTimeArrivals = newOnTimeArrivals;
          })
        });
      }

      // Click route name to sort in ascending order and verify up sort arrow is active
      table.routeNameAscending().should('be.visible');
      table.routeNameAscending().click({ force: true });

      for (let i = 1; i <= 5; i++) {
        const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[1])[1]`;
        const nextxpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i + 1}]//td[1])[1]`;

        cy.xpath(xpathVal).each(($el) => {
          let rowVal = $el.text().replace(/[^\d.-]/g, '');
          cy.log(`ROUTE BEFORE  = ${rowVal}`);
          cy.xpath(nextxpathVal).each(($elm) => {
            i++;
            const newRouteVal = $elm.text().replace(/[^\d.-]/g, '');
            cy.log(`ROUTE AFTER = ${newRouteVal}`);
            expect(+newRouteVal).gte(+rowVal);
            rowVal = newRouteVal;
          })
        });
      }

      table
        .routeNameSorters()
        .should(
          'have.class',
          'anticon anticon-caret-up ant-table-column-sorter-up active'
        );

      // Sort % Early Arrivals in descending order
      table.scheduleDeviationEarlyArrivals().should('be.visible');
      table.scheduleDeviationEarlyArrivals().click({ force: true });
      cy.wait(3000);
      table.scheduleDeviationEarlyArrivals().click({ force: true });

      for (let i = 1; i <= 5; i++) {
        const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[3])[1]`;
        const nextxpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i + 1}]//td[3])[1]`;

        cy.xpath(xpathVal).each(($el) => {
          let earlyArrivalPercentage = $el.text().match(/(\d+)/)[0];
          cy.log(`Early Arrival Percentage = ${earlyArrivalPercentage}`);
          cy.xpath(nextxpathVal).each(($el) => {
            i++;
            const newEarlyArrivalPercentage = $el.text().match(/(\d+)/)[0];
            cy.log(`New Early Arrival Percentage = ${newEarlyArrivalPercentage}`);
            expect(+newEarlyArrivalPercentage).lte(+earlyArrivalPercentage);
            earlyArrivalPercentage = newEarlyArrivalPercentage;
          })
        });
      }

      // Sort % Late Arrivals in ascending order
      table.scheduleDeviationLateArrivals().should('be.visible');
      table.scheduleDeviationLateArrivals().click({ force: true });

      for (let i = 1; i <= 5; i++) {
        const xpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[4])[1]`;
        const nextxpathVal = `((//div[@class="ant-table-content"])[3]//tbody//tr[${i}]//td[4])[1]`;

        cy.xpath(xpathVal).each(($el) => {
          let LateArrivals = $el.text().match(/(\d+)/)[0];
          cy.log(`Late Arrivals Percentage = ${LateArrivals}`);
          cy.xpath(nextxpathVal).each(($el) => {
            let newLateArrivals = $el.text().match(/(\d+)/)[0];
            newLateArrivals = +LateArrivals;
            cy.log(`New Late Arrivals Percentage = ${newLateArrivals}`);
            expect(+newLateArrivals).gte(+LateArrivals);
            LateArrivals = newLateArrivals;
          })
        })
      }
    })
  })
})
