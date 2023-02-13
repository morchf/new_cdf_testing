class Maps {
  mapContainer() {
    return cy.xpath('//div[@class="map-container"]');
  }

  mapZoomIn() {
    return cy.xpath('//button[@title="Zoom in"]');
  }

  mapZoomOut() {
    return cy.xpath('//button[@title="Zoom out"]');
  }
}

export default Maps;
