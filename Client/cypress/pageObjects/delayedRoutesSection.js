class DelayedRoutesSectionPage {
  mostDelayedRoutesTitle() {
    return cy.xpath('(//section/div/h5)[1]');
  }

  mostDelayedRoutesInfoToolTip() {
    return cy.xpath('(//section/div/h5/div[@class="info-tooltip "])[1]');
  }

  mostDelayedRoutesInfoToolText() {
    return cy.xpath(
      '//div[contains(text(), "Most delayed routes based on signal delay at GTT intersections and filters")]'
    );
  }

  mostDelayedRoutesTable() {
    return cy.xpath('(//section/div[2])[1]');
  }

  mostDelayedTableRoutesText() {
    return cy.xpath('(//th[contains(text(),"Route")])[1]');
  }

  mostDelayedTableDelayText() {
    return cy.xpath('(//th[contains(text(),"Delay")])[1]');
  }

  mostDelayedTableDwellText() {
    return cy.xpath('(//th[contains(text(),"Dwell")])[1]');
  }

  mostDelayedTableDriveText() {
    return cy.xpath('(//th[contains(text(),"Drive")])[1]');
  }

  mostDelayedTableTotalText() {
    return cy.xpath('(//th[contains(text(),"Total")])[1]');
  }

  mostDelayedRouteTableBody() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[1]');
  }

  mostDelayedRouteLink() {
    return cy.xpath('(//section[1]//tbody//tr[1]//td[1]//a)[1]');
  }

  mostDelayedRouteLTimeNote() {
    return cy.xpath(
      '(//span[contains(@class, "performance-table__time-note")])[1]'
    );
  }

  leastDelayedRoutesTitle() {
    return cy.xpath('(//section/div/h5)[2]');
  }

  leastDelayedRoutesInfoToolTip() {
    return cy.xpath('(//section/div/h5/div[@class="info-tooltip "])[2]');
  }

  leastDelayedRoutesInfoToolText() {
    return cy.xpath(
      '//div[contains(text(), "Least delayed routes based on signal delay at GTT intersections and filters")]'
    );
  }

  leastDelayedRoutesTable() {
    return cy.xpath('(//section/div[2])[2]');
  }

  leastDelayedTableRoutesText() {
    return cy.xpath('(//th[contains(text(),"Route")])[2]');
  }

  leastDelayedTableDelayText() {
    return cy.xpath('(//th[contains(text(),"Delay")])[2]');
  }

  leastDelayedTableDwellText() {
    return cy.xpath('(//th[contains(text(),"Dwell")])[2]');
  }

  leastDelayedTableDriveText() {
    return cy.xpath('(//th[contains(text(),"Drive")])[2]');
  }

  leastDelayedTableTotalText() {
    return cy.xpath('(//th[contains(text(),"Total")])[2]');
  }

  leastDelayedRouteTableBody() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[2]');
  }

  leastDelayedRouteLink() {
    return cy.xpath('//section[2]//tbody//tr[2]//td[1]//a');
  }

  leastDelayedRouteLTimeNote() {
    return cy.xpath(
      '(//span[contains(@class, "performance-table__time-note")])[2]'
    );
  }
}

export default DelayedRoutesSectionPage;
