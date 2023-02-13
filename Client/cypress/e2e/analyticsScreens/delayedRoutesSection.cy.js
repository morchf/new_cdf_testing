import DelayedRoutesSectionPage from '../../pageObjects/delayedRoutesSection';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';
import Maps from '../../pageObjects/maps';

describe('delayedRoutesSection', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('MostDelayedRoutes', () => {
    const page = new DelayedRoutesSectionPage();
    const screen = new AnalyticScreensPage();
    const map = new Maps();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal();

    // Validate least delayed route section heading title and info tool tip
    page.mostDelayedRoutesTitle().should('be.visible');
    page.mostDelayedRoutesTitle().should('contain.text', 'Most Delayed Routes');
    page.mostDelayedRoutesInfoToolTip().should('be.visible');
    page.mostDelayedRoutesInfoToolTip().trigger('mouseover');
    page.mostDelayedRoutesInfoToolText().should('be.visible');
    page
      .mostDelayedRoutesInfoToolText()
      .should(
        'contain.text',
        'Most delayed routes based on signal delay at GTT intersections and filters'
      );

    // Validate least delayed route table contents
    page.mostDelayedRoutesTable().should('be.visible');
    page
      .mostDelayedTableRoutesText()
      .should('be.visible')
      .should('contain.text', 'Route');
    page
      .mostDelayedTableDelayText()
      .should('be.visible')
      .should('contain.text', 'Delay');
    page
      .mostDelayedTableDwellText()
      .should('be.visible')
      .should('contain.text', 'Dwell');
    page
      .mostDelayedTableDriveText()
      .should('be.visible')
      .should('contain.text', 'Drive');
    page
      .mostDelayedTableTotalText()
      .should('be.visible')
      .should('contain.text', 'Total');
    page
      .mostDelayedRouteLTimeNote()
      .should('be.visible')
      .should('contain.text', 'All Times in Minutes');

    // Verify least delayed routes table should contain 3 rows
    page.mostDelayedRouteTableBody().find('tr').should('have.length', 3);

    // Verify delay+dwell+drive time is equal to total time shown in the table
    cy.xpath('(//section[1]//tbody//tr[1]//td[2])[1]').then(($elem) => {
      const mostDelayTime = $elem.text();
      cy.wrap(mostDelayTime).as('mostDelayTime');
    });

    cy.xpath('(//section[1]//tbody//tr[1]//td[3])[1]').then(($elem) => {
      const mostDwellTime = $elem.text();
      cy.wrap(mostDwellTime).as('mostDwellTime');
    });

    cy.xpath('(//section[1]//tbody//tr[1]//td[4])[1]').then(($elem) => {
      const mostDriveTime = $elem.text();
      cy.wrap(mostDriveTime).as('mostDriveTime');
    });

    cy.xpath('(//section[1]//tbody//tr[1]//td[5])[1]').then(($elem) => {
      const mostTotalTime = $elem.text();
      cy.wrap(mostTotalTime).as('mostTotalTime');
    });

    cy.then(function () {
      const mostMertricsTotal =
        +this.mostDelayTime + +this.mostDwellTime + +this.mostDriveTime;
      expect(+mostMertricsTotal).to.equal(+this.mostTotalTime);
    });

    // Verify clicking on route link navigates to transit delay L2 screen
    page.mostDelayedRouteLink().click();
    screen.transitDelayL2ScreenHeadingTitle().should('be.visible');
    screen.transitDelayL2ScreenTabViewHeader().should('be.visible');
    map.mapContainer().should('be.visible');
  });

  it('LeastDelayedRoutes', () => {
    const page = new DelayedRoutesSectionPage();
    const screen = new AnalyticScreensPage();
    const map = new Maps();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal();

    // Validate least delayed route section heading title and info tool tip
    page.leastDelayedRoutesTitle().should('be.visible');
    page
      .leastDelayedRoutesTitle()
      .should('contain.text', 'Least Delayed Routes');
    page.leastDelayedRoutesInfoToolTip().should('be.visible');
    page.leastDelayedRoutesInfoToolTip().trigger('mouseover');
    page.leastDelayedRoutesInfoToolText().should('be.visible');
    page
      .leastDelayedRoutesInfoToolText()
      .should(
        'contain.text',
        'Least delayed routes based on signal delay at GTT intersections and filters'
      );

    // Validate least delayed route table contents
    page.leastDelayedRoutesTable().should('be.visible');
    page
      .leastDelayedTableRoutesText()
      .should('be.visible')
      .should('contain.text', 'Route');
    page
      .leastDelayedTableDelayText()
      .should('be.visible')
      .should('contain.text', 'Delay');
    page
      .leastDelayedTableDwellText()
      .should('be.visible')
      .should('contain.text', 'Dwell');
    page
      .leastDelayedTableDriveText()
      .should('be.visible')
      .should('contain.text', 'Drive');
    page
      .leastDelayedTableTotalText()
      .should('be.visible')
      .should('contain.text', 'Total');
    page
      .leastDelayedRouteLTimeNote()
      .should('be.visible')
      .should('contain.text', 'All Times in Minutes');

    // Verify least delayed routes table should contain 3 rows
    page.leastDelayedRouteTableBody().find('tr').should('have.length', 3);

    // Verify delay+dwell+drive time is equal to total time shown in the table
    cy.xpath('//section[2]//tbody//tr[1]//td[2]').then(($elem) => {
      const leastDelayTime = $elem.text();
      cy.wrap(leastDelayTime).as('leastDelayTime');
    });

    cy.xpath('//section[2]//tbody//tr[1]//td[3]').then(($elem) => {
      const leastDwellTime = $elem.text();
      cy.wrap(leastDwellTime).as('leastDwellTime');
    });

    cy.xpath('//section[2]//tbody//tr[1]//td[4]').then(($elem) => {
      const leastDriveTime = $elem.text();
      cy.wrap(leastDriveTime).as('leastDriveTime');
    });

    cy.xpath('//section[2]//tbody//tr[1]//td[5]').then(($elem) => {
      const leastTotalTime = $elem.text();
      cy.wrap(leastTotalTime).as('leastTotalTime');
    });

    cy.then(function () {
      const leastMertricsTotal =
        +this.leastDelayTime + +this.leastDwellTime + +this.leastDriveTime;
      expect(+leastMertricsTotal).to.equal(+this.leastTotalTime);

      // Verify clicking on route link navigates to transit delay L2 screen
      page.leastDelayedRouteLink().click();
      screen.transitDelayL2ScreenHeadingTitle().should('be.visible');
      screen.transitDelayL2ScreenTabViewHeader().should('be.visible');
      map.mapContainer().should('be.visible');
    });
  });
});
