import AnalyticScreens from '../../pageObjects/analyticScreens';

describe('TransitDelay', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Transit Delay e2e', () => {
    const delay = new AnalyticScreens();
    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    delay.l1RouteName().then(($elem) => {
      const l1RouteName = $elem.text()
      cy.wrap(l1RouteName).as('l1RouteName');
    })

    // Click on Route to navigate to TD L2 screen
    delay.l1RouteName().click();

    cy.then(function () {
      // TD L2 Screen - Validate heading title for Route 38R
      cy.xpath('//section[@class="heading-section"]//h2').should('be.visible');
      cy.xpath('//section[@class="heading-section"]//h2').should(
        'contain.text',
        this.l1RouteName
      );
    })

    // TD L2 Screen Details Header
    cy.xpath(
      '//section[@class="route-details"]//div[@class="tab-view__header"]'
    ).should('be.visible');

    cy.then(function () {
      // TD L2 Screen - Validate Signal Delay Tab is active by default and chart is visible
      delay.signalDelay().should('be.visible');
      delay.signalDelay().should('contain.text', 'Signal Delay (avg)');
      delay
        .signalDelayTabActive()
        .should('have.class', 'ant-radio-button-checked');
      delay.chartsSection().scrollIntoView().should('be.visible');
      delay.chartsTitle().should('contain.text', this.l1RouteName);

      // TD L2 Screen - Validate Dwell Time Tab is active and chart is visible
      delay.dwellTime().click();
      cy.wait(1000);
      delay.dwellTimeTabActive().should('have.class', 'ant-radio-button-checked');
      delay.chartsSection().should('be.visible').scrollIntoView();
      delay.chartsTitle().should('contain.text', this.l1RouteName);

      // TD L2 Screen - Validate Drive Time Tab is active and chart is visible
      delay.driveTime().click();
      cy.wait(1000);
      delay.driveTimeTabActive().should('have.class', 'ant-radio-button-checked');
      delay.chartsSection().should('be.visible').scrollIntoView();
      delay.chartsTitle().should('contain.text', this.l1RouteName);

      // TD L2 Screen - Validate Total Time Tab is active and chart is visible
      delay.travelTime().click();
      cy.wait(1000);
      delay
        .travelTimeTabActive()
        .should('have.class', 'ant-radio-button-checked');
      delay.chartsSection().should('be.visible').scrollIntoView();
      delay.chartsTitle().should('contain.text', this.l1RouteName);
    })
  });
});
