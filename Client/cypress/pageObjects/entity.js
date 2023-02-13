class EntityPage {
  constructor() {
    this.elements = {
      createButton: () => cy.xpath('//span[text()="Create New"]'),
      inputName: () => cy.xpath('//input[@name="name"]'),
      inputDescription: () => cy.xpath('//input[@name="description"]'),
      submitButton: () => cy.xpath('//span[text()="Submit"]'),
      deleteButton: () => cy.xpath('//span[text()="Delete"]'),
      deleteSubmitButton: () => cy.xpath('//span[contains(text(),"Submit")]'),
      deleteOkButton: () => cy.xpath('//span[contains(text(),"Ok")]'),
      regionBreadcrumb: () => cy.xpath('//a[contains(text(),"Regions")]'),
      deleteSearch: () =>
        cy.xpath(
          '//span[@class="anticon anticon-close-circle ant-input-clear-icon"]'
        ),
      regionTableContents: () => cy.xpath('//tbody[@class="ant-table-tbody"]'),
      agencyTableTitle: () => cy.xpath('//div//h5[contains(text(), "Agency")]'),
      agencyTable: () => cy.xpath('//div[@class="ant-table-content"]'),
      agencyTableContents: () => cy.xpath('//tbody[@class="ant-table-tbody"]'),
      deleteAgency: () =>
        cy.xpath(
          '//span[@class="anticon anticon-close-circle ant-input-clear-icon"]'
        ),
      editPropertiesButton: () =>
        cy.xpath('//button[text()="Edit Properties"]'),
      editRegionDescription: () => cy.xpath('//input[@name="description"]'),
      newRegionDescription: () =>
        cy.xpath('//tbody[@class="ant-table-tbody"]//tr//td[2]'),
      agencyPriority: () => cy.xpath('//div[@name="priority"]'),
      agencyPriorityLow: () => cy.xpath('//div[@title="Low"]'),
      agencyPriorityHigh: () => cy.xpath('//div[@title="High"]'),
      agencyCode: () => cy.xpath('//input[@name="agencyCode"]'),
      agencyCity: () => cy.xpath('//input[@name="city"]'),
      agencyState: () => cy.xpath('//div[@name="state"]'),
      agencyStateAL: () => cy.xpath('//div[@title="AL"]'),
      agencyStateCA: () => cy.xpath('//div[@title="CA"]'),
      agencyTimezone: () => cy.xpath('//div[@name="timezone"]'),
      agencyTimezoneCentral: () => cy.xpath('//div[@title="Central"]'),
      agencyTimezonePacific: () => cy.xpath('//div[@title="Pacific"]'),
      agencyPropertiesTableTitle: () =>
        cy.xpath('//div//h5[contains(text(), "Agency Properties")]'),
      agencyPropertiesTable: () => cy.xpath('//div[@class="AgencyTable"]'),
      updatedAgencyDescription: () =>
        cy.xpath('(//tbody[@class="ant-table-tbody"])[2]//td[3]'),
      updatedAgencyCity: () =>
        cy.xpath('(//tbody[@class="ant-table-tbody"])[2]//td[4]'),
      updatedAgencyPriority: () =>
        cy.xpath('(//tbody[@class="ant-table-tbody"])[2]//td[8]'),
      updatedAgencyCode: () =>
        cy.xpath('(//tbody[@class="ant-table-tbody"])[2]//td[7]'),
      updatedAgencyState: () =>
        cy.xpath('(//tbody[@class="ant-table-tbody"])[2]//td[5]'),
      updatedAgencyTimezone: () =>
        cy.xpath('(//tbody[@class="ant-table-tbody"])[2]//td[6]'),
      agencyCmsId: () =>
        cy.xpath('(//tbody[@class="ant-table-tbody"])[2]//td[9]'),
      regionUITestBreadcrumb: () =>
        cy.xpath('//a[contains(text(),"regionuitest")]'),
      addIntersectionButton: () =>
        cy.xpath('//button[contains(text(),"+ Add Intersection")]'),
      addIntersectionModal: () => cy.xpath('//div[@class="ant-modal-content"]'),
      intersectionModalTitle: () =>
        cy.xpath('//div[@class="ant-modal-content"]//h5'),
      enterIntersectionName: () =>
        cy.xpath('//input[@name="intersectionName"]'),
      enterLatitudeValue: () => cy.xpath('//input[@name="latitude"]'),
      enterLongitudeValue: () => cy.xpath('//input[@name="longitude"]'),
      generalIntersectionInformationTab: () =>
        cy.xpath('//div[@class="ant-tabs-content-holder"]'),
      intersectionNameonL2Screen: () =>
        cy.xpath('//input[@id="intersectionName"]'),
      locationTypeonL2Screen: () => cy.xpath('//span[@title="NTCIP"]'),
      latitudeValueonL2Screen: () => cy.xpath('//input[@id="latitude"]'),
      longitudeValueonL2Screen: () => cy.xpath('//input[@id="longitude"]'),
      intersectionDeleteButton: () => cy.xpath('//button[text()="Delete"]'),
      intersectionTable: () => cy.xpath('//div[@class="ant-table-container"]'),
      intersectionSearch: () => cy.xpath('//div[@class="search-row"]'),
      intersectionSearchPlaceholderText: () =>
        cy.xpath('//span[@class="ant-select-selection-placeholder"]'),
      intersectionTableContents: () =>
        cy.xpath('//tbody[@class="ant-table-tbody"]'),
      searchedIntersectionName: () =>
        cy.xpath('//span[@class="intersection"]//a'),
      clearIntersectionSearch: () =>
        cy.xpath('//span[@class="ant-select-clear"]'),
    };
  }
}

export default EntityPage;
