import RouteTable from '../../pageObjects/routeTable';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe('TransitDelay', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Transit Delay e2e', () => {
    const table = new RouteTable();
    const screens = new AnalyticScreensPage();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    // Select start and end date
    cy.fixture(`transitDelay.${Cypress.env('environment')}`).then(
      ({ startDate, endDate }) => {
        cy.datepicker(startDate, endDate);
      }
    );

    // Transit Delay L1 Screen
    cy.title().should('eq', 'GTT Smart Cities');
    cy.url().should('include', 'transit-delay');

    // Click on first route link from route table to navigate to L2 screen
    table.transitDelayRouteTableSection().should('be.visible');
    table.transitDelayRouteTitle().should('contain.text', 'Routes');
    table.transitDelayFirstRouteLink().click();

    // Verify tab view header is visible
    screens.transitDelayL2ScreenTabViewHeader().should('be.visible');

    // Validate Signal Delay Tab
    cy.wait(5000);
    screens
      .signalDelay()
      .should('be.visible')
      .should('contain.text', 'Signal Delay (avg)');
    screens.l2SignalDelayMetrics().contains(/^\d+m\s\d+s|\d+s$/);
    screens
      .l2SignalDelayPercentageRouteTime()
      .contains(/^\d+?% of Route Time$/);
    screens.l2Delaymetrics().then(($ele) => {
      if ($ele.find('div').length > 1) {
        screens
          .l2SignalDelayL2Label()
          .contains(
            /^(\d+?m|\d+s?)\s?(\d+?s)?\s?((better)?(worse)?)\sthan\sthe\slast\speriod$/
          );
      }
    })
    screens.l2SignalDelayToolTip().trigger('mouseover').invoke('show')
    screens
      .l2SignalDelayToolTipText()
      .should('contain', 'Average trip time elapsed while stopped at GTT intersections on route. Includes all (enabled and disabled) channels');

    // Validate Dwell Time Tab
    screens
      .dwellTime()
      .should('be.visible')
      .should('contain.text', 'Dwell Time (avg)');
    screens.l2DwellTimeMetrics().contains(/^\d+m\s\d+s$/);
    screens.l2DwellTimePercentageRouteTime().contains(/^\d+?% of Route Time$/);
    screens
      .l2DwellTimeL2Label()
      .contains(
        /^(\d+?m)?\s?(\d+?s)?\s?((better)?(worse)?)\sthan\sthe\slast\speriod$/
      );

    screens.l2DwellTimeToolTip().trigger('mouseover');
    screens
      .l2DwellTimeToolTipText()
      .should(
        'contain.text',
        'Total time elapsed between arriving and departing at a bus stop'
      );

    // Validate Drive Time Tab
    screens
      .driveTime()
      .should('be.visible')
      .should('contain.text', 'Drive Time (avg)');
    screens.l2DriveTimeMetrics().contains(/^\d+m\s\d+s$/);
    screens.l2DriveTimePercentageRouteTime().contains(/^\d+?% of Route Time$/);
    screens.l2Drivemetrics().then(($ele) => {
      screens
        .l2DriveTimeL2Label()
        .contains(
          /^(\d+?m)?\s?(\d+?s)?\s?((better)?(worse)?)\sthan\sthe\slast\speriod$/
        );
      screens.l2DriveTimeToolTip().trigger('mouseover');
      screens
        .l2DriveTimeToolTipText()
        .should(
          'contain.text',
          'Time elapsed between two stops including signal delay at non-GTT intersections. Excludes time spent at stops, segments and GTT intersections. Red map segments indicate an increase in drive time compared to previous date range.'
        );

      // Validate Travel Time Tab
      screens
        .travelTime()
        .should('be.visible')
        .should('contain.text', 'Travel Time (avg)');
      screens.l2TravelTimeMetrics().contains(/^\d+m\s\d+s$/);
      screens.l2TravelTimePercentageRouteTime().contains(/^\d+?% of Route Time$/);
      screens
        .l2TravelTimeL2Label()
        .contains(
          /^(\d+?m)?\s?(\d+?s)?\s?((better)?(worse)?)\sthan\sthe\slast\speriod$/
        );
      screens.l2TravelTimeToolTip().trigger('mouseover');
      screens
        .l2TravelTimeToolTipText()
        .should(
          'contain.text',
          'Total time elapsed between the start and the end of the route including dwell time, drive time and signal delay'
        );
    });
  });
});
