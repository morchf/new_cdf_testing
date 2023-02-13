const vpssExample = [
  {
    customerName: 'GLOBALINFRA',
    deviceStatus: 'RESTART',
    serverName: 'GLOBALINFRA2',
    vpsAvailability: 'AVAILABLE',
    primaryKey: '224754297012507',
    VPS: 'V764MM0283',
    markToDelete: 'YES',
    GTTmac: 'CC:69:B0:09:01:1B',
  },
  {
    customerName: 'GLOBALINFRA',
    deviceStatus: 'ACTIVE',
    serverName: 'GLOBALINFRA1',
    vpsAvailability: 'INUSE',
    markToDelete: 'NO',
    lastCheck: '06-25-2020T14:04:57.514789',
    dockerFinished: '0001-01-01T00:00:00Z',
    dockerStatus: 'running',
    dockerPort: '2000',
    dockerIP: '172.31.84.243',
    dockerStart: '2020-06-25T14:04:57.495931165Z',
    primaryKey: '224754297012393',
    VPS: 'V764MM0169',
    GTTmac: 'CC:69:B0:09:00:A9',
  },
];
export default async () => {
  return await new Promise((resolve) => {
    resolve(vpssExample);
  });
};
