class AnalyticsSideMenuPage {
  sideMenuIcon() {
    return cy.get('.ant-menu-item-icon');
  }

  sideMenuTitle() {
    return cy.xpath(
      '//div[@class="ant-menu-submenu-title"]//span[@class="ant-menu-title-content"]'
    );
  }

  sideSubMenu() {
    return cy.get('.ant-menu-inline');
  }

  sideMenuTransitDelay() {
    return cy.xpath(
      '//span[@class="ant-menu-title-content"]//a[text()="Transit Delay"]'
    );
  }

  transitDelayBreadcrumb() {
    return cy.xpath(
      '//span[@class="ant-breadcrumb-link"]//a[contains(text(),"Transit Delay")]'
    );
  }

  sideMenuScheduleDeviation() {
    return cy.xpath(
      '//span[@class="ant-menu-title-content"]//a[text()="Schedule Deviation"]'
    );
  }

  scheduleDeviationBreadcrumb() {
    return cy.xpath(
      '//span[@class="ant-breadcrumb-link"]//a[contains(text(),"Schedule Deviation")]'
    );
  }

  scheduleDeviationRouteNameBreadcrumb() {
    return cy.xpath(
      '(//span[@class="ant-breadcrumb-link"])[3]'
    );
  }

  headingTitle() {
    return cy.get('.heading-section__title');
  }
}

export default AnalyticsSideMenuPage;
