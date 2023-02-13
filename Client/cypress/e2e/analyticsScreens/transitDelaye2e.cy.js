
import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe('TransitDelay', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Transit Delay e2e', () => {
    const page = new AnalyticScreensPage();

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

    // Select Direction
    page.headingTitle().should('be.visible');
    page.headingTitle().should('contain.text', 'Transit Delay');
    cy.xpath('//span[@title="Inbound"]').click();
    cy.xpath('//div[contains(text(),"Outbound")]').click();
    cy.xpath('//span[contains(text(),"Outbound")]').should(
      'contain.text',
      'Outbound'
    );

    // Select start and end date
    cy.fixture(`transitDelay.${Cypress.env('environment')}`).then(
      ({ startDate, endDate }) => {
        cy.datepicker(startDate, endDate);
      }
    );

    // Performance Summary Tab
    cy.get('.performance-summary').should('be.visible');
    cy.xpath('(//section/div/h5)[1]').should(
      'contain.text',
      'Most Delayed Routes'
    );
    cy.xpath('(//section/div/h5/div)[1]').should('be.visible');
    cy.xpath('(//section/div/h5/div)[1]').scrollIntoView();
    cy.xpath('(//section/div/h5/div)[1]').trigger('mouseover');
    cy.get('.ant-tooltip-inner').should(
      'contain.text',
      'Most delayed routes based on signal delay at GTT intersections and filters'
    );

    // Route Table
    // Collect data from L1 Screen
    page.l1RouteName().then(($elem) => {
      const l1RouteName = $elem.text()
      cy.wrap(l1RouteName).as('l1RouteName');
    })

    cy.then(() => {
      cy.get('.overview-content__table').should('be.visible');
      cy.xpath('(//section/div/h5)[3]').should('contain.text', 'Routes');
      page.l1RouteName().scrollIntoView();
      page.l1RouteName().click();
    })

    // TD L2 Screen - Validate Breadcrumb and Title for Route 38R
    page.l2RouteName().then(($elem) => {
      const l2RouteName = $elem.text().trim()
      cy.wrap(l2RouteName).as('l2RouteName');
    })
    cy.then(() => {
      page.l2RouteName().should('be.visible');
      cy.xpath('//section[@class="heading-section"]//h2').should('be.visible');
    })

    // Validate Direction, DateRange and Time filter is same as selected on L1 Screen
    cy.xpath('//span[contains(text(),"Outbound")]').should(
      'contain.text',
      'Outbound'
    );

    cy.fixture(`transitDelay.${Cypress.env('environment')}`).then(
      ({ startDate, endDate }) => {
        cy.xpath('//input[@placeholder="Start date"]').should(
          'contain.value',
          startDate
        );
        cy.xpath('//input[@placeholder="End date"]').should(
          'contain.value',
          endDate
        );
      }
    );

    page
      .timeFilterText()
      .invoke('text')
      .should('match', /Peak AM\s.(\d+)?\d+:\d+\d+ - (\d+)?\d+:\d+\d+/)

    // TD L2 Screen Details Header
    cy.xpath(
      '//section[@class="route-details"]//div[@class="tab-view__header"]'
    ).should('be.visible');

    // TD L2 Screen - Validate Signal Delay Tab
    cy.wait(5000);
    cy.xpath('//div[contains(text(),"Signal Delay (avg)")]').should(
      'be.visible'
    );
    cy.xpath('//div[contains(text(),"Signal Delay (avg)")]').should(
      'contain.text',
      'Signal Delay (avg)'
    );
    cy.xpath(
      '//div[contains(text(),"Signal Delay (avg)")]//ancestor::label[contains(@class, "avg-metrics-item")]//div[contains(@class,"avg-metrics_item-header")]'
    ).contains(/^(\d+m\s\d+s)|\d+s$/);
    cy.xpath(
      '//div[contains(text(),"Signal Delay (avg)")]//preceding::div[@class="avg-metrics_item-label1"]'
    ).contains(/^\d+?% of Route Time$/);
    cy.xpath(
      '//div[contains(text(),"Signal Delay (avg)")]//ancestor::span//div[@class="avg-metrics_item-content_left"]//div[2]'
    ).contains(
      /^(\d+?m)?\s?(\d+?s)?\s?((better)?(worse)?)\sthan\sthe\slast\speriod$/
    );
    page.l2SignalDelayToolTip().trigger('mouseover').invoke('show')
    page.l2SignalDelayToolTipText().should('contain', 'Average trip time elapsed while stopped at GTT intersections on route. Includes all (enabled and disabled) channels')

    // TD L2 Screen Map Container
    cy.xpath('//div[@class="map-container"]').should('be.visible');
    cy.xpath('//button[@title="Zoom in"]').click();
    cy.xpath('//div[@class="map-container"]').should('be.visible');
    cy.wait(2000);
    cy.xpath('//button[@title="Zoom out"]').click();
    cy.xpath('//div[@class="map-container"]').should('be.visible');
    cy.wait(2000);
    cy.xpath('//div[@class="map-container"]').dblclick();
    cy.xpath('//div[@class="map-container"]').should('be.visible');
    cy.wait(2000);

    // TD L2 Screen Dwell Time Chart
    cy.then(function () {
      cy.xpath('//div[contains(text(),"Dwell Time (avg)")]').click();
      cy.xpath('//section[@class="common-chart"]//canvas').should('be.visible');
      cy.xpath('//section[@class="common-chart"]//canvas').scrollIntoView();
      cy.xpath('//section[@class="common-chart"]//h3').should(
        'contain.text',
        `Dwell Time for ${this.l2RouteName}`
      );
    })
  });
});
