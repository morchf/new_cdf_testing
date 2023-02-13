import RouteTable from '../../pageObjects/routeTable';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe('TransitDelayRouteTable', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Route Table', () => {
    const table = new RouteTable();
    const screen = new AnalyticScreensPage();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal();

    // Transit Delay L1 Screen
    cy.title().should('eq', 'GTT Smart Cities');
    cy.url().should('include', 'transit-delay');

    // Route Table
    table.transitDelayRouteTableSection().should('be.visible');
    table.transitDelayRouteTitle().should('contain.text', 'Routes');
    table.transitDelayRouteTableHead().find('th').should('have.length', 6);
    table
      .transitDelayRouteTableBody()
      .find('tr')
      .should('have.length.least', 1);

    // Validate Route Table Header
    table
      .avgSignalDelay()
      .should('be.visible')
      .should('contain.text', 'Avg. Signal Delay');
    table
      .signalDelayPercentage()
      .should('be.visible')
      .should('contain.text', 'Signal Delay (% of Travel Time)');
    table
      .avgDwellTime()
      .should('be.visible')
      .should('contain.text', 'Avg. Dwell Time');
    table
      .avgDriveTime()
      .should('be.visible')
      .should('contain.text', 'Avg. Drive Time');
    table
      .avgRouteTime()
      .should('be.visible')
      .should('contain.text', 'Avg. Route Time');

    // Verify signal delay, dwell, drive, travel time metrics values for a route on L1 screen is equal to metrics values on L2 screen
    let l1SignalDelay;
    let l1DwellTime;
    let l1DriveTime;
    let l1TravelTime;

    cy.scrollTo(0, -500);
    cy.wait(250);
    table.avgSignalDelayFirstRouteLink().each(($value) => {
      l1SignalDelay = $value.text();
    });

    table.avgDwellTimeFirstRouteLink().each(($value) => {
      l1DwellTime = $value.text();
    });

    table.avgDriveTimeFirstRouteLink().each(($value) => {
      l1DriveTime = $value.text();
    });

    table.avgRouteTimeFirstRouteLink().each(($value) => {
      l1TravelTime = $value.text();
    });

    // Clicking on route from route table to navigate to L2 screen
    table.transitDelayFirstRouteLink().click();

    let l2SignalDelay;
    let l2DwellTime;
    let l2DriveTime;
    let l2TravelTime;

    screen.l2SignalDelayMetrics().each(($value) => {
      l2SignalDelay = $value.text();
      expect(l1SignalDelay).to.equal(l2SignalDelay);
    });

    screen.l2DwellTimeMetrics().each(($value) => {
      l2DwellTime = $value.text();
      expect(l1DwellTime).to.equal(l2DwellTime);
    });

    screen.l2DriveTimeMetrics().each(($value) => {
      l2DriveTime = $value.text();
      expect(l1DriveTime).to.equal(l2DriveTime);
    });

    screen.l2TravelTimeMetrics().each(($value) => {
      l2TravelTime = $value.text();
      expect(l1TravelTime).to.equal(l2TravelTime);
    });

    // Navigate back to transit delay L1 screen by clicking on browser back button and verify route table is visible
    cy.go('back');
    table.transitDelayRouteTableSection().should('be.visible');
    table
      .transitDelayRouteTableBody()
      .find('tr')
      .should('have.length.least', 1);
  });
});
