import AnalyticScreens from '../../pageObjects/analyticScreens';
import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';

describe('scheduleDeviationCharts', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Schedule Deviation Charts', () => {
    const AnalyticScreensPage = new AnalyticScreens();
    const page = new AnalyticsSideMenuPage();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal();

    // Clicking on Schedule Deviation link in sidemenu navigates to Schedule Deviation L1 screen
    page.sideMenuScheduleDeviation().click();
    page.scheduleDeviationBreadcrumb().should('be.visible');
    page
      .scheduleDeviationBreadcrumb()
      .should('contain.text', 'Schedule Deviation');
    page.headingTitle().should('contain.text', 'Schedule Deviation');

    // Verify Schedule Deviation chart section
    AnalyticScreensPage.l1ScheduleDeviationChartSection().should('be.visible');
    AnalyticScreensPage.l1ScheduleDeviationChartsHeading().should(
      'contain.text',
      'Schedule Deviation'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsLateRadio().should(
      'be.visible'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsOnTimeRadio().should(
      'be.visible'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsEarlyRadio().should(
      'be.visible'
    );

    // Click on 1st radio and check other radio buttons are not active
    AnalyticScreensPage.l1ScheduleDeviationChartsLateRadio().click();
    AnalyticScreensPage.l1ScheduleDeviationChartsLateRadio().should(
      'have.class',
      'active'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsOnTimeRadio().should(
      'not.have.class',
      'active'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsEarlyRadio().should(
      'not.have.class',
      'active'
    );

    // Click on 2nd radio and check other radio buttons are not active
    AnalyticScreensPage.l1ScheduleDeviationChartsOnTimeRadio().click();
    AnalyticScreensPage.l1ScheduleDeviationChartsOnTimeRadio().should(
      'have.class',
      'active'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsLateRadio().should(
      'not.have.class',
      'active'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsEarlyRadio().should(
      'not.have.class',
      'active'
    );

    // Click on 3rd radio and check other radio buttons are not active
    AnalyticScreensPage.l1ScheduleDeviationChartsEarlyRadio().click();
    AnalyticScreensPage.l1ScheduleDeviationChartsEarlyRadio().should(
      'have.class',
      'active'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsLateRadio().should(
      'not.have.class',
      'active'
    );
    AnalyticScreensPage.l1ScheduleDeviationChartsOnTimeRadio().should(
      'not.have.class',
      'active'
    );
  });
});
