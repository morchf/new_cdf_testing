class RouteTable {
  transitDelayRouteTableSection() {
    return cy.xpath('//div[@class="overview-content__table"]');
  }

  routeTable() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]');
  }

  transitDelayRouteTableHead() {
    return cy.xpath('//div[@class="overview-content__table"]//thead');
  }

  transitDelayRouteTableBody() {
    return cy.xpath('//div[@class="overview-content__table"]//tbody');
  }

  transitDelayRouteTitle() {
    return cy.xpath('(//section/div/h5)[3]');
  }

  scheduleDeviationRouteTable() {
    return cy.xpath(
      '//section[@class="table-card  ScheduleDevOverviewPage__table"]'
    );
  }

  scheduleDeviationRouteTitle() {
    return cy.xpath('//section/div/h5');
  }

  routeLink38R() {
    return cy.xpath(
      '//section[@class="table-card  ScheduleDevOverviewPage__table"]//tbody//a[contains(text(),"Route 38R")]'
    );
  }

  routeName() {
    return cy.xpath('//span[contains(text(),"Route Name")]');
  }

  avgSignalDelay() {
    return cy.xpath('//span[contains(text(),"Avg. Signal Delay")]');
  }

  signalDelayPercentage() {
    return cy.xpath(
      '//span[contains(text(),"Signal Delay (% of Travel Time)")]'
    );
  }

  scheduleDeviationOntimeArrivalsAscending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[2]//span[@class="anticon anticon-caret-up ant-table-column-sorter-up"]'
    );
  }

  scheduleDeviationEarlyArrivalsAscending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[3]//span[@class="anticon anticon-caret-up ant-table-column-sorter-up"]'
    );
  }

  scheduleDeviationOntimeArrivals() {
    return cy.xpath(
      '//span[contains(text(),"% On-time Arrivals")]'
    );
  }

  avgDwellTime() {
    return cy.xpath('//span[contains(text(),"Avg. Dwell Time")]');
  }

  scheduleDeviationEarlyArrivals() {
    return cy.xpath('//span[contains(text(),"% Early Arrivals")]');
  }

  scheduleDeviationLateArrivals() {
    return cy.xpath('//span[contains(text(),"% Late Arrivals")]');
  }

  avgDriveTime() {
    return cy.xpath('//span[contains(text(),"Avg. Drive Time")]');
  }

  avgRouteTime() {
    return cy.xpath('//span[contains(text(),"Avg. Route Time")]');
  }

  transitDelayFirstRouteLink() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[1]/td[1]/a');
  }

  avgSignalDelayFirstRouteLink() {
    return cy.xpath(
      '//div[@class="overview-content__table"]//tbody//tr[1]//td[2]'
    );
  }

  avgDwellTimeFirstRouteLink() {
    return cy.xpath(
      '//div[@class="overview-content__table"]//tbody//tr[1]//td[4]'
    );
  }

  avgDriveTimeFirstRouteLink() {
    return cy.xpath(
      '//div[@class="overview-content__table"]//tbody//tr[1]//td[5]'
    );
  }

  avgRouteTimeFirstRouteLink() {
    return cy.xpath(
      '//div[@class="overview-content__table"]//tbody//tr[1]//td[6]'
    );
  }

  routeNameSorters() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[1]//span[@class="ant-table-column-sorter-inner"]//span[1]'
    );
  }

  routeNameAscending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[1]//span[@class="anticon anticon-caret-up ant-table-column-sorter-up"]'
    );
  }

  routeNameDescending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[1]//span[@class="anticon anticon-caret-down ant-table-column-sorter-down"]'
    );
  }

  avgSignalDelaySorters() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[2]//span[@class="ant-table-column-sorter-inner"]//span[2]'
    );
  }

  scheduleDeviationOntimeArrivalsSorters() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[2]//span[@class="ant-table-column-sorter-inner"]//span[2]'
    );
  }

  avgSignalDelayAscending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[2]//span[@class="anticon anticon-caret-up ant-table-column-sorter-up"]'
    );
  }

  avgSignalDelayDescending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])[2]//span[@class="anticon anticon-caret-down ant-table-column-sorter-down"]'
    );
  }
}

export default RouteTable;
