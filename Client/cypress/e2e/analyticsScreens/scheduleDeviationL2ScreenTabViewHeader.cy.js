import RouteTable from '../../pageObjects/routeTable';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';
import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';

describe('scheduleDeviationL2ScreenTabViewHeader', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('schedule Deviation e2e', () => {
    const table = new RouteTable();
    const screens = new AnalyticScreensPage();
    const page = new AnalyticsSideMenuPage();


    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    cy.title().should('eq', 'GTT Smart Cities');

    // Clicking on Schedule Deviation link in sidemenu navigates to Schedule Deviation L1 screen
    page.sideMenuScheduleDeviation().click();
    page.scheduleDeviationBreadcrumb().should('be.visible');
    page.scheduleDeviationBreadcrumb().should('contain.text', 'Schedule Deviation');
    page.headingTitle().should('contain.text', 'Schedule Deviation');

    // Click on first route link from route table to navigate to L2 screen
    table.scheduleDeviationRouteTable().should('be.visible');
    table.scheduleDeviationRouteTitle().should('contain.text', 'Routes');
    screens.scheduleDeviationFirstRouteLink().click();

    // verify breadcrumbs and title L2 screen.
    page.scheduleDeviationBreadcrumb().should('be.visible');
    page.scheduleDeviationBreadcrumb().should('contain.text', 'Schedule Deviation');
    page.headingTitle().should('contain.text', 'Route');

    // Verify tab view header is visible
    screens.l2OnTimePercentageSection().should('be.visible');
    screens.l2ScheduleDeviationSection().should('be.visible');

    // Validate On-Time Arrival Percentage Tab
    cy.wait(5000);
    screens
      .l2OnTimePercentageSectionText()
      .should('be.visible')
      .should('contain.text', 'On-Time Percentage');
    screens.l2LeastOnTimeArrivalPercentage().contains(/\d+%/);
    screens
      .l2RouteEarlyLateArrivalsPercentage()
      .contains(/Early \d+?% - Late \d+?%/);
    screens.l2OnTimePercentageToolTip().trigger('mouseover').invoke('show')
    screens
      .l2OnTImePercentageToolTipText()
      .should('contain', 'On-Time, Early and Late percentages considering deviation for all stops on route');
    screens.l2scheduleDeviationGraph1H3().should('contain.text', 'On-Time Percentage by Day');
    screens.l2scheduleDeviationGraph2H3().should('contain.text', 'On-Time Percentage by Stop');

    // Validate Schedule Deviation Tab
    screens.l2ScheduleDeviationSection().click({ force: true })
    screens
      .l2ScheduleDeviationTitle()
      .should('be.visible')
      .should('contain.text', 'Schedule Deviation');
    screens.l2ScheduleDeviationTime().contains(/(\d+\w?)?(\d+\w?)?(\Wahead)?(\Wbehind)?/);
    screens.l2scheduleDeviationToolTip().trigger('mouseover');
    screens
      .l2scheduleDeviationToolTipText()
      .should(
        'contain.text',
        'Average time deviated either ahead or behind schedule considering all the stops'
      );
    screens.l2scheduleDeviationGraph1H3().should('contain.text', 'Schedule Deviation by Day');
    screens.l2scheduleDeviationGraph2H3().should('contain.text', 'Schedule Deviation by Stop');
  });
});
