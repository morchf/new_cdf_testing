import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe('analyticsSideMenu', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('sideMenuItems', () => {
    const page = new AnalyticScreensPage();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    // Validate Transit Delay L1 Screen Heading Section Elements
    page.headingTitle().should('be.visible');
    page.headingTitle().should('contain.text', 'Transit Delay');
    page.headingTitleInfoIcon().scrollIntoView();
    page.headingTitleInfoIcon().should('be.visible');
    page.headingTitleInfoIcon().trigger('mouseover');
    page.headingTitleToolTipText().should('be.visible');
    page
      .headingTitleToolTipText()
      .should('contain.text', 'Provides an overview of delays for all routes');
    page.dateRangeInfoIcon().click();
    page
      .dateRangeToolTipText()
      .should(
        'contain.text',
        'Selectable dates correspond to available data for the selected timeperiod. The date range can span a maximum of 90 days'
      );

    // Validate dropdown elements in each filter
    page.directionFilterText().should('contain.text', 'Inbound');
    page.directionFilterText().click();
    page
      .outboundDirectionText()
      .should('be.visible')
      .should('contain.text', 'Outbound');
    page.allDirectionText().should('be.visible').should('contain.text', 'All');
    page.datePickerStartDate().should('be.visible');
    page.datePickerRange().click();
    page.datePickerContainer().should('be.visible');
    page
      .timeFilterText()
      .invoke('text')
      .should('match', /Peak AM\s.(\d+)?\d+:\d+\d+ - (\d+)?\d+:\d+\d+/)
    page.timeFilterText().click()
    page
      .peakPmText()
      .invoke('text')
      .should('match', /Peak PM\s.(\d+)?\d+:\d+\d+ - (\d+)?\d+:\d+\d+/)
    page
      .offPeakText()
      .should('be.visible')
      .should('contain.text', 'Off-Peak (not peak or weekends)');
    page
      .weekendText()
      .should('be.visible')
      .should('contain.text', 'Weekends (Saturday & Sunday)');
    page.allTimeText().should('be.visible').should('contain.text', 'All');
  });
});
