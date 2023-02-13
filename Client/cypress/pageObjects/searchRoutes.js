class SearchRoute {
  searchRow() {
    return cy.xpath('//div[@class="search-row"]');
  }

  searchBox() {
    return cy.xpath(
      '//div[@class="overview-content__table"]//div[@class="table-card__header "]//div[@class="ant-select-selector"]'
    );
  }

  searchPlaceholderText() {
    return cy.get('.ant-select-selection-placeholder');
  }

  routeLabel1() {
    return cy.xpath('//div[@label="1"]');
  }

  l1RouteName() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[1]/td[1]/a');
  }

  l1RouteName2() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[2]/td[1]/a');
  }

  l1RouteName3() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[3]/td[1]/a');
  }

  l1RouteName4() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[4]/td[1]/a');
  }

  l1RouteName5() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[5]/td[1]/a');
  }

  routeLabel22() {
    return cy.xpath(`//div[@label="22"]`);
  }

  routeLabel38R() {
    return cy.xpath('//div[@label="38R"]');
  }

  routeLabel14R() {
    return cy.xpath('//div[@label="14R"]');
  }

  routeLabel9R() {
    return cy.xpath('//div[@label="9R"]');
  }

  routeLabel7() {
    return cy.xpath('//div[@label="7"]');
  }

  routeLink22() {
    return cy.xpath(
      `//div[@class="overview-content__table"]//tbody[@class="ant-table-tbody"]//a[contains(text(),"Route 22")]`
    );
  }

  routeLink38R() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[2]/tr[1]/td[1]/a');
  }

  firstRouteLink() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[2]/tr[1]/td[1]/a');
  }

  routeLink14R() {
    return cy.xpath(
      '//div[@class="overview-content__table"]//tbody[@class="ant-table-tbody"]//a[contains(text(),"Route 14R")]'
    );
  }

  routeLink9R() {
    return cy.xpath(
      '//div[@class="overview-content__table"]//tbody[@class="ant-table-tbody"]//a[contains(text(),"Route 9R")]'
    );
  }

  routeLink7() {
    return cy.xpath(
      '//div[@class="overview-content__table"]//tbody[@class="ant-table-tbody"]//a[contains(text(),"Route 7")]'
    );
  }

  multipleRoutesSearch() {
    return cy.xpath('//div[@class="ant-select-selection-overflow"]');
  }

  deleteRoute14R() {
    return cy.xpath(
      '//span[contains(text(),"14R")]//following-sibling::span[contains(@class, "ant-select-selection-item-remove")]'
    );
  }

  deleteAllRoutes() {
    return cy.xpath('//span[@class="ant-select-clear"]');
  }

  routeTable() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]');
  }

  paginationTotalText() {
    return cy.get('.ant-pagination-total-text');
  }

  backButton() {
    return cy.xpath('//div[@class="back-button"]');
  }
}

export default SearchRoute;
