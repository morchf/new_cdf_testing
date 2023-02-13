class Pagination {
  paginationSection() {
    return cy.get('.ant-table-pagination-right');
  }

  paginationTotalText() {
    return cy.get('.ant-pagination-total-text');
  }

  routeTable() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]');
  }

  previousPage() {
    return cy.xpath('//li[@title="Previous Page"]');
  }

  nextPage() {
    return cy.xpath('//li[@title="Next Page"]');
  }

  page1() {
    return cy.xpath('//li[@title="1"]');
  }

  page2() {
    return cy.xpath('//li[@title="2"]');
  }

  page3() {
    return cy.xpath('//li[@title="3"]');
  }

  pageSizeText() {
    return cy.xpath(
      '//li[@class="ant-pagination-options"]//span[@class="ant-select-selection-item"]'
    );
  }

  pageSize10() {
    return cy.xpath('//div[contains(text(),"10 / page")]');
  }

  pageSize20() {
    return cy.xpath('//div[contains(text(),"20 / page")]');
  }

  regionsTable() {
    return cy.xpath('//div[@class="ant-table-container"]//tbody');
  }

  goToPage() {
    return cy.xpath('//div[@class="ant-pagination-options-quick-jumper"]');
  }

  goToPageText() {
    return cy.xpath(
      '//ul[@class="ant-pagination ant-table-pagination ant-table-pagination-right"]//input[@type="text"]'
    );
  }
}

export default Pagination;
