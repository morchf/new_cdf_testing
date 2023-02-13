class AnalyticScreensPage {
  headingTitle() {
    return cy.get('.heading-section__title');
  }

  headingTitleInfoIcon() {
    return cy.xpath(
      '//div[contains(@class, "heading-wrapper")]//div[contains(@class,"info-tooltip")][1]//*[local-name() = "svg"]'
    );
  }

  headingTitleToolTipText() {
    return cy.xpath(
      '//div[contains(text(),"Provides an overview of delays for all routes")]'
    );
  }

  filtersSection() {
    return cy.get('.filters-container');
  }

  directionLabel() {
    return cy.xpath('//span[contains(text(),"Direction" )]');
  }

  dateRangeLabel() {
    return cy.xpath('//span[contains(text(),"Date Range" )]');
  }

  dateRangeInfoIcon() {
    return cy.xpath(
      '//div[@class="filters-container"]//div[@class="info-tooltip "]'
    );
  }

  dateRangeToolTipText() {
    return cy.xpath(
      '//div[contains(text(),"Selectable dates correspond to available data for the selected timeperiod. The date range can span a maximum of 90 days")]'
    );
  }

  timeLabel() {
    return cy.xpath(
      '//div[@class="labeled-select filters-container__time filters-container__time--single-value"]'
    );
  }

  directionFilterText() {
    return cy.xpath(
      '//div[@class="ant-select-selector"]//span[@title="Inbound"]'
    );
  }

  directionOutboundFilterText() {
    return cy.xpath(
      '(//div[@class="ant-select-item-option-content"])[2]'
    );
  }

  scheduleDeviationMap() {
    return cy.xpath(
      '//div[@class="tab-view__wrapper"]'
    );
  }

  inboundDirectionText() {
    return cy.xpath('//div[contains(text(),"Inbound")]');
  }

  outboundDirectionText() {
    return cy.xpath('//div[contains(text(),"Outbound")]');
  }

  allDirectionText() {
    return cy.xpath('//div[contains(text(),"All")]');
  }

  datePickerRange() {
    return cy.xpath('//div[@class="ant-picker ant-picker-range"]');
  }

  datePickerContainer() {
    return cy.xpath('//div[@class="ant-picker-panel-container"]');
  }

  datePickerStartDate() {
    return cy.xpath('//input[@placeholder="Start date"]');
  }

  datePickerEndDate() {
    return cy.xpath('//input[@placeholder="End date"]');
  }

  timeFilterText() {
    return cy.xpath(
      '//div[@class="labeled-select filters-container__time filters-container__time--single-value"]//span[@class="ant-select-selection-item"]'
    );
  }

  peakAmText() {
    return cy.xpath('//div[contains(text(),"Peak AM (06:00 - 09:00) ")]');
  }

  peakPmText() {
    return cy.xpath('//div[contains(text(),"Peak PM (16:00 - 19:00)")]');
  }

  offPeakText() {
    return cy.xpath(
      '//div[contains(text(),"Off-Peak (not peak or weekends)")]'
    );
  }

  weekendText() {
    return cy.xpath('//div[contains(text(),"Weekends (Saturday & Sunday)")]');
  }

  allTimeText() {
    return cy.xpath('//div[contains(text(),"All")]');
  }

  breadcrumb38R() {
    return cy.xpath(
      '(//span[@class="ant-breadcrumb-link"])[3]'
    );
  }

  breadcrumbRouteName() {
    return cy.xpath(
      '(//span[@class="ant-breadcrumb-link"])[3]'
    );
  }

  l2ScreenHeadingTitle() {
    return cy.xpath('//section[@class="heading-section"]//h2');
  }

  l2ScreenTabViewHeader() {
    return cy.xpath('//div[@class="tab-view__header"]');
  }

  scheduleDeviationFirstRouteLink() {
    return cy.xpath(
      '(//section[@class="table-card  ScheduleDevOverviewPage__table"]//table//tbody//tr//a)[1]'
    );
  }

  signalDelay() {
    return cy.xpath('//div[contains(text(),"Signal Delay (avg)")]');
  }

  l2OnTimePercentageSectionText() {
    return cy.xpath('//div[contains(text(),"On-Time Percentage")]');
  }

  dwellTime() {
    return cy.xpath('//div[contains(text(),"Dwell Time (avg)")]');
  }

  l2ScheduleDeviationTitle() {
    return cy.xpath('//div[contains(text(),"Schedule Deviation")]');
  }

  driveTime() {
    return cy.xpath('//div[contains(text(),"Drive Time (avg)")]');
  }

  travelTime() {
    return cy.xpath('//div[contains(text(),"Travel Time (avg)")]');
  }

  signalDelayTabActive() {
    return cy.xpath(
      '//div[contains(text(),"Signal Delay (avg)")]//ancestor::label//span'
    );
  }

  dwellTimeTabActive() {
    return cy.xpath(
      '//div[contains(text(),"Dwell Time (avg)")]//ancestor::label//span'
    );
  }

  driveTimeTabActive() {
    return cy.xpath(
      '//div[contains(text(),"Drive Time (avg)")]//ancestor::label//span'
    );
  }

  travelTimeTabActive() {
    return cy.xpath(
      '//div[contains(text(),"Travel Time (avg)")]//ancestor::label//span'
    );
  }

  chartsSection() {
    return cy.xpath('//section[@class="common-chart"]//canvas');
  }

  chartsTitle() {
    return cy.xpath('//section[@class="common-chart"]//h3');
  }

  transitDelayL2ScreenHeadingTitle() {
    return cy.xpath('//section[@class="heading-section"]//h2');
  }

  transitDelayL2ScreenTabViewHeader() {
    return cy.xpath(
      '//section[@class="route-details"]//div[@class="tab-view__header"]'
    );
  }

  l2SignalDelayMetrics() {
    return cy.xpath(
      '//div[contains(text(),"Signal Delay (avg)")]//preceding::div[@class="avg-metrics_item-header"]'
    );
  }

  l2SignalDelayPercentageRouteTime() {
    return cy.xpath(
      '//div[contains(text(),"Signal Delay (avg)")]//preceding::div[@class="avg-metrics_item-label1"]'
    );
  }


  l2SignalDelayL2Label() {
    return cy.xpath(
      '//div[contains(text(),"Signal Delay (avg)")]//ancestor::span//div[@class="avg-metrics_item-content_left"]//div[2]'
    );
  }


  l2SignalDelayToolTip() {
    return cy.xpath(
      '//div[contains(text(),"Signal Delay (avg)")]//ancestor::label[contains(@class, "avg-metrics-item")]//div[contains(@class,"info-tooltip")]'
    );
  }

  l2OnTimePercentageToolTip() {
    return cy.xpath(
      '(*//div[@class="info-tooltip "])[2]'
    );
  }

  l2scheduleDeviationToolTip() {
    return cy.xpath(
      '(*//div[@class="info-tooltip "])[3]'
    );
  }

  l2SignalDelayToolTipText() {
    return cy.xpath(
      '(//div[@class="ant-tooltip-inner"])[1]'
    );
  }

  l2scheduleDeviationGraph1H3() {
    return cy.xpath(
      '(//h3)[1]'
    );
  }

  l2scheduleDeviationGraph2H3() {
    return cy.xpath(
      '(//h3)[2]'
    );
  }

  l2scheduleDeviationToolTipText() {
    return cy.xpath(
      '(//div[@class="ant-tooltip-inner"])[2]'
    );
  }

  l2DwellTimeMetrics() {
    return cy.xpath(
      '//div[contains(text(),"Dwell Time (avg)")]//ancestor::label[contains(@class, "avg-metrics-item")]//div[contains(@class,"avg-metrics_item-header")]'
    );
  }

  l2ScheduleDeviationTime() {
    return cy.xpath(
      '(//div[@class="avg-metrics_item-header"])[2]'
    );
  }

  l2DwellTimePercentageRouteTime() {
    return cy.xpath(
      '//div[contains(text(),"Dwell Time (avg)")]//preceding::div[@class="avg-metrics_item-label1"]'
    );
  }

  l2DwellTimeL2Label() {
    return cy.xpath(
      '//div[contains(text(),"Dwell Time (avg)")]//ancestor::span//div[@class="avg-metrics_item-content_left"]//div[2]'
    );
  }

  l2OnTImePercentageToolTipText() {
    return cy.xpath(
      '(//div[@class="ant-tooltip-inner"])[1]'
    );
  }

  l2DwellTimeToolTip() {
    return cy.xpath(
      '//div[contains(text(),"Dwell Time (avg)")]//ancestor::label[contains(@class, "avg-metrics-item")]//div[contains(@class,"info-tooltip")]'
    );
  }

  l2DwellTimeToolTipText() {
    return cy.xpath(
      '(//div[@class="ant-tooltip-inner"])[2]'
    );
  }

  l2DriveTimeMetrics() {
    return cy.xpath(
      '//div[contains(text(),"Drive Time (avg)")]//ancestor::label[contains(@class, "avg-metrics-item")]//div[contains(@class,"avg-metrics_item-header")]'
    );
  }

  l2DriveTimePercentageRouteTime() {
    return cy.xpath(
      '//div[contains(text(),"Drive Time (avg)")]//preceding::div[@class="avg-metrics_item-label1"]'
    );
  }

  l2DriveTimeL2Label() {
    return cy.xpath(
      '//div[contains(text(),"Drive Time (avg)")]//ancestor::span//div[@class="avg-metrics_item-content_left"]//div[2]'
    );
  }

  l2DriveTimeToolTip() {
    return cy.xpath(
      '//div[contains(text(),"Drive Time (avg)")]//ancestor::label[contains(@class, "avg-metrics-item")]//div[contains(@class,"info-tooltip")]'
    );
  }

  l2DriveTimeToolTipText() {
    return cy.xpath(
      '(//div[@class="ant-tooltip-inner"])[3]'
    );
  }

  l2TravelTimeMetrics() {
    return cy.xpath(
      '//div[contains(text(),"Travel Time (avg)")]//ancestor::label[contains(@class, "avg-metrics-item")]//div[contains(@class,"avg-metrics_item-header")]'
    );
  }

  l2TravelTimePercentageRouteTime() {
    return cy.xpath(
      '//div[contains(text(),"Travel Time (avg)")]//preceding::div[@class="avg-metrics_item-label1"]'
    );
  }

  l2TravelTimeL2Label() {
    return cy.xpath(
      '//div[contains(text(),"Travel Time (avg)")]//ancestor::span//div[@class="avg-metrics_item-content_left"]//div[2]'
    );
  }

  l2TravelTimeToolTip() {
    return cy.xpath(
      '//div[contains(text(),"Travel Time (avg)")]//ancestor::label[contains(@class, "avg-metrics-item")]//div[contains(@class,"info-tooltip")]'
    );
  }

  l2TravelTimeToolTipText() {
    return cy.xpath(
      '//div[contains(text(),"Total time elapsed between the start and the end of the route including dwell time, drive time and signal delay")]'
    );
  }

  l2Delaymetrics() {
    return cy.xpath('(//div[@class="avg-metrics_item-content_left"])[1]')
  }

  l2Dwellmetrics() {
    return cy.xpath('(//div[@class="avg-metrics_item-content_left"])[2]')
  }

  l2Drivemetrics() {
    return cy.xpath('(//div[@class="avg-metrics_item-content_left"])[3]')
  }

  l2Travelmetrics() {
    return cy.xpath('(//div[@class="avg-metrics_item-content_left"])[4]')
  }

  // SD Route Table
  l1RouteTable() {
    return cy.xpath('//div[@class="table-card__table"]');
  }

  l1RouteHeading() {
    return cy.xpath('//h5[@class="ant-typography table-card__title"]');
  }

  l1RouteTableHeadingsCount() {
    return cy.xpath('//span[@class="ant-table-column-title"]');
  }

  l1RouteTableRow() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[1]');
  }

  l1RouteTableRowsCount() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr');
  }

  l1RouteName() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[1]/td[1]/a');
  }

  l1RouteOnTimeArrivalsPercentage() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[1]/td[2]');
  }

  l1RouteEarlyArrivalsPercentage() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[1]/td[3]');
  }

  l1RouteLateArrivalsPercentage() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[1]/td[4]');
  }

  l1RouteAverageScheduleDeviation() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[3]/tr[1]/td[5]');
  }

  l2OnTimePercentageSection() {
    return cy.xpath('//span[@class="ant-radio-button ant-radio-button-checked"]');
  }

  l2ScheduleDeviationSectionChart1() {
    return cy.xpath('(//section[@class="common-chart"])[1]');
  }

  l2ScheduleDeviationSectionChart2() {
    return cy.xpath('(//section[@class="common-chart"])[2]');
  }

  l2ScheduleDeviationSection() {
    return cy.xpath('//span[@class="ant-radio-button"]');
  }

  l2RouteName() {
    return cy.xpath('//h2[@class="ant-typography heading-section__title"]');
  }

  l2RouteOnTimeArrivalsPercentage() {
    return cy.xpath('(//div[@class="avg-metrics_item-header"])[1]');
  }

  l2RouteEarlyArrivalsPercentage() {
    return cy.xpath('//div[@class="avg-metrics_item-label3"]');
  }

  l2RouteLateArrivalsPercentage() {
    return cy.xpath('//div[@class="avg-metrics_item-label3"]');
  }

  l2RouteAverageScheduleDeviation() {
    return cy.xpath('(//div[@class="avg-metrics_item-header"])[2]');
  }

  l2BackButton() {
    return cy.xpath('//*[@class="back-button"]');
  }

  searchRegionButton() {
    return cy.xpath('//span[@class="ant-input-group-addon"]');
  }

  selectRegion() {
    return cy.xpath('//a[@href="/region/sfmtademo"]');
  }

  selectAgency() {
    return cy.xpath('//a[@href="/region/sfmtademo/agency/sfmta"]');
  }

  metricsSideMenu() {
    return cy.xpath('//span[@class="ant-menu-title-content"]');
  }

  l2RouteEarlyLateArrivalsPercentage() {
    return cy.xpath('//div[@class="avg-metrics_item-label3"]');
  }

  // Performance Card
  overallPerformanceHeader() {
    return cy.xpath('//h3[@class="ant-typography"]');
  }

  onTimeP1() {
    return cy.get('.ontime-col > .p1');
  }

  lateP1() {
    return cy.get('.late-col > .p1');
  }

  earlyP1() {
    return cy.get('.early-col > .p1');
  }

  onTimeP2() {
    return cy.get('.ontime-col > .p2');
  }

  lateP2() {
    return cy.get('.late-col > .p2');
  }

  earlyP2() {
    return cy.get('.early-col > .p2');
  }

  onTimeP3() {
    return cy.get('.ontime-col > .p3');
  }

  lateP3() {
    return cy.get('.late-col > .p3');
  }

  earlyP3() {
    return cy.get('.early-col > .p3');
  }

  // tooltip
  infoToolTip() {
    return cy.xpath('//div[contains(@class, "title-row")]//div[contains(@class,"info-tooltip")][1]//*[local-name() = "svg"]');
  }

  infoToolTipMessage() {
    return cy.xpath('//div[contains(text(),"Provides % and number of routes that are on-time, early and late")]');
  }

  // Schedule Deviation Heading Section

  scheduleDeviationHeadingToolTipText() {
    return cy.xpath('//div[contains(text(),"Provides an overview for all routes in accordance with the schedule")]');
  }

  scheduleDeviationHeadingDateInfoIcon() {
    return cy.xpath('//div[contains(@class, "labeled-select undefined")]//div[contains(@class,"info-tooltip")][1]//*[local-name() = "svg"]');
  }

  scheduleDeviationHeadingDateToolTipText() {
    return cy.xpath('//div[contains(text(),"Selectable dates correspond to available data for the selected timeperiod. The date range can span a maximum of 90 days")]');
  }

  scheduleDeviationHeadingDirectionFilter() {
    return cy.xpath('//div[@class="filters-container"]/div[1]');
  }

  scheduleDeviationHeadingDateRangeFilter() {
    return cy.xpath('//div[@class="filters-container"]/div[2]');
  }

  scheduleDeviationHeadingPeakAmText() {
    return cy.xpath('(//div[@class="ant-select-selector"])[2]//span[2]');
  }

  scheduleDeviationHeadingPeakPmText() {
    return cy.xpath('//div[@class="ant-select-item ant-select-item-option"][1]');
  }

  scheduleDeviationHeadingTimeFilter() {
    return cy.xpath('//div[@class="filters-container"]/div[3]');
  }


  // scheduleDeviationLeast/MostOnTimeRoutesTable

  mostOntimeInfoIcon() {
    return cy.xpath(
      '(//div[contains(@class, "top-row")])[3]//div[contains(@class,"info-tooltip")][1]//*[local-name() = "svg"]'
    );
  }

  leastOntimeInfoIcon() {
    return cy.xpath(
      '(//div[contains(@class, "top-row")])[3]//div[contains(@class,"info-tooltip")][1]//*[local-name() = "svg"]'
    );
  }

  mostOntimeToolTipText() {
    return cy.xpath(
      '//div[contains(text(),"Routes with the lowest percentage of on-time performance")]'
    );
  }

  leastOntimeToolTipText() {
    return cy.xpath(
      '//div[contains(text(),"Routes with the lowest percentage of on-time performance")]'
    );
  }

  mostOntimeRoutesSection() {
    return cy.xpath('(//div[@class="ant-table-content"])[1]');
  }

  leastOntimeRoutesSection() {
    return cy.xpath('(//div[@class="ant-table-content"])[2]');
  }

  mostOntimeRoutesHeading() {
    return cy.xpath('(//div[@class="top-row"])[1]/span');
  }

  leastOntimeRoutesHeading() {
    return cy.xpath('(//div[@class="top-row"])[2]/span');
  }

  mostOnTimeColumn() {
    return cy.xpath('(//thead[@class="ant-table-thead"])[1]/tr/th[2]');
  }

  onTimeColumn() {
    return cy.xpath('(//thead[@class="ant-table-thead"])[2]/tr/th[2]');
  }

  mostAvgDeviationColumn() {
    return cy.xpath('(//thead[@class="ant-table-thead"])[1]/tr/th[3]');
  }

  avgDeviationColumn() {
    return cy.xpath('(//thead[@class="ant-table-thead"])[2]/tr/th[3]');
  }

  l1MostOnTimeRouteName() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[1]/tr[1]/td[1]/a');
  }

  l1LeastOnTimeRouteName() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[2]/tr[1]/td[1]/a');
  }

  l1MostOnTimeArrivalPercentage() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[1]/tr[1]/td[2]');
  }

  l1LeastOnTimeArrivalPercentage() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[2]/tr[1]/td[2]');
  }

  l1MostOnTimeAvgDeviation() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[1]/tr[1]/td[3]');
  }

  l1LeastOnTimeAvgDeviation() {
    return cy.xpath('(//tbody[@class="ant-table-tbody"])[2]/tr[1]/td[3]');
  }

  l2MostOnTimeRouteNameHeading() {
    return cy.xpath('//h2[@class="ant-typography heading-section__title"]');
  }

  l2LeastOnTimeRouteNameHeading() {
    return cy.xpath('//h2[@class="ant-typography heading-section__title"]');
  }

  l2MostOntimeRoutesSection() {
    return cy.xpath('//span[@class="ant-radio-button ant-radio-button-checked"]');
  }

  l2LeastOntimeRoutesSection() {
    return cy.xpath('//span[@class="ant-radio-button ant-radio-button-checked"]');
  }

  l2MostScheduleDeviationSection() {
    return cy.xpath('//span[@class="ant-radio-button"]');
  }

  l2LeastScheduleDeviationSection() {
    return cy.xpath('//span[@class="ant-radio-button"]');
  }

  l2MostOnTimeArrivalPercentage() {
    return cy.xpath('(//div[@class="avg-metrics_item-header"])[1]');
  }

  l2LeastOnTimeArrivalPercentage() {
    return cy.xpath('(//div[@class="avg-metrics_item-header"])[1]');
  }

  l2MostRouteAverageScheduleDeviation() {
    return cy.xpath('(//div[@class="avg-metrics_item-header"])[2]');
  }

  l2LeastRouteAverageScheduleDeviation() {
    return cy.xpath('(//div[@class="avg-metrics_item-header"])[2]');
  }

  // Schedule Deviation L1 page chart

  l1ScheduleDeviationChartSection() {
    return cy.xpath('//section[@class="deviation-category"]');
  }

  l1ScheduleDeviationChartsHeading() {
    return cy.xpath('(//h3)[2]');
  }

  l1ScheduleDeviationChartsLateRadio() {
    return cy.xpath('//section//button[@value="Late"]');
  }

  l1ScheduleDeviationChartsOnTimeRadio() {
    return cy.xpath('//section//button[@value="On-time"]');
  }

  l1ScheduleDeviationChartsEarlyRadio() {
    return cy.xpath('//section//button[@value="Early"]');
  }

}

export default AnalyticScreensPage;
