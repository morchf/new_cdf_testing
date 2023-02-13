from App import ConfigureIntersections

ConfigureIntersections(
    customerName="exampleCustomerName",
    intersections=["exampleVPSNames", "V764HKMS0221", "V764HKMS0226"],
    deviceCert="path/to/device/certificate/file",
    deviceKey="path/to/private/key/file",
    rootCa="path/to/root/ca/file",
    iotEndpoint="example-ats.iot.region-name.amazonaws.com",
    approachMaps=True,
)
