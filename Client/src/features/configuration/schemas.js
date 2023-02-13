import * as yup from 'yup';

const MAC_ADDRESS_REGEX = '^(([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))?$';

const regionSchema = yup.object({
  name: yup
    .string()
    .matches(
      '^[A-Za-z0-9]+$',
      'Must be alphanumeric without spaces or underscores.'
    )
    .max(1000, 'Must be 1000 characters or less')
    .required('Name is a required field'),
  description: yup.string().max(1000, 'Must be 1000 characters or less'),
});

const editRegionSchema = yup.object({
  name: yup.string().max(1000, 'Must be 1000 characters or less').required(),
  description: yup.string().max(1000, 'Must be 1000 characters or less'),
});

const agencySchema = yup.object({
  name: yup
    .string()
    .matches(
      '^[A-Za-z0-9]+$',
      'Must be alphanumeric without spaces or underscores.'
    )
    .max(50, 'Must be 50 characters or less')
    .required('Name is a required field'),
  description: yup.string().max(1000, 'Must be 1000 characters or less'),
  city: yup.string().max(50, 'Must be 50 characters or less').required(),
  state: yup.string().required(),
  timezone: yup
    .string()
    .oneOf(['Central', 'Mountain', 'Eastern', 'Pacific', 'Arizona'])
    .required(),
  agencyCode: yup
    .number()
    .integer()
    .min(1, 'Must be between 1 to 254')
    .max(254, 'Must be between 1 to 254')
    .required(),
  priority: yup.string().oneOf(['Low', 'High']).required(),
  CMSId: yup.string(),
});

const vehicleSchema = yup.object({
  name: yup
    .string()
    .max(100, 'Must be 100 characters or less')
    .required('Name is a required field'),
  description: yup.string().max(500, 'Must be 500 characters or less'),
  type: yup.string().max(100, 'Must be 100 characters or less'),
  class: yup
    .number()
    .integer()
    .min(1, 'Must be  in between 1 to 10')
    .max(10, 'Must be in between 1 to 10')
    .required('Class is a required field'),
  VID: yup
    .number()
    .integer()
    .min(1, 'Must be between 1 to 9999')
    .max(9999, 'Must be between 1 to 9999')
    .required('VID is a required field'),
  priority: yup
    .string()
    .oneOf(['Low', 'High'])
    .required('Priority is a required field'),
});

const editVehicleSchema = yup.object({
  name: yup
    .string()
    .max(1000, 'Must be 1000 characters or less')
    .required('Name is a required field'),
  description: yup.string().max(1000, 'Must be 1000 characters or less'),
  type: yup.string().max(50, 'Must be 50 characters or less'),
  VID: yup
    .number()
    .integer()
    .min(1, 'Must be between 1 to 9999')
    .max(9999, 'Must be between 1 to 9999')
    .required('VID is a required field'),
  class: yup
    .number()
    .integer()
    .min(1, 'Must be  in between 1 to 10')
    .max(10, 'Must be in between 1 to 10')
    .required('Class is a required field'),
  priority: yup
    .string()
    .oneOf(['Low', 'High'], 'Must select a priority level')
    .required('Priority is a required field'),
});

const deviceSchema = yup.object({
  description: yup.string().max(500, 'Must be 500 characters or less'),
  gttSerial: yup
    .string()
    .max(50, 'Must be 50 characters or less')
    .required('GTT Serial is a required field'),
  serial: yup
    .string()
    .max(50, 'Must be 50 characters or less')
    .required('Serial is a required field'),
  addressMAC: yup.string().when('make', {
    is: (make) => /^(Cradlepoint|Sierra Wireless)$/.test(make),
    then: yup
      .string()
      .matches(MAC_ADDRESS_REGEX, 'Must be valid MAC address')
      .required('MAC Address is a required field'),
  }),
  addressLAN: yup
    .string()
    .matches(/(^(\d{1,3}\.){3}(\d{1,3})$)/, {
      message: 'Invalid IP address',
      excludeEmptyString: true,
    })
    .test('ip', 'Invalid IP address', (value) =>
      value === undefined || value.trim() === ''
        ? true
        : value.split('.').find((i) => parseInt(i, 10) > 255) === undefined
    )
    .required('LAN Address is a required field'),
  addressWAN: yup
    .string()
    .matches(/(^(\d{1,3}\.){3}(\d{1,3})$)/, {
      message: 'Invalid IP address',
      excludeEmptyString: true,
    })
    .test('ip', 'Invalid IP address', (value) =>
      value === undefined || value.trim() === ''
        ? true
        : value.split('.').find((i) => parseInt(i, 10) > 255) === undefined
    )
    .required('WAN Address is a required field'),
  IMEI: yup.string().when('make', {
    is: 'GTT',
    then: yup.string().matches('[0-9]{15}$', 'Must be 15 digits'),
    otherwise: yup
      .string()
      .matches('[0-9]{15}$', 'Must be 15 digits')
      .required('IMEI is a required field'),
  }),
  make: yup
    .string()
    .oneOf(['GTT', 'Sierra Wireless', 'Cradlepoint'])
    .required('Make is a required field'),
  model: yup.string().when('make', {
    is: 'GTT',
    then: yup
      .string()
      .oneOf(['2100', '2101'])
      .required('Model is a required field'),
    otherwise: yup
      .string()
      .oneOf(['MP-70', 'IBR900', 'IBR1700', 'R1900'])
      .required('Model is a required field'),
  }),
});

const editDeviceSchema = yup.object({
  description: yup.string().max(1000, 'Must be 1000 characters or less'),
  gttSerial: yup
    .string()
    .max(50, 'Must be 50 characters or less')
    .required('GTT Serial is a required field'),
  serial: yup.string().max(50, 'Must be 50 characters or less'),
  addressMAC: yup
    .string()
    .matches(
      '[0-9a-fA-F]{2}([-:]?)[0-9a-fA-F]{2}(\\1[0-9a-fA-F]{2}){4}$',
      'Must be valid MAC address'
    )
    .when('make', {
      is: 'GTT',
      then: yup.string(),
      otherwise: yup.string().required('MAC Address is a required field'),
    }),
  addressLAN: yup
    .string()
    .matches(/(^(\d{1,3}\.){3}(\d{1,3})$)/, {
      message: 'Invalid IP address',
      excludeEmptyString: true,
    })
    .test('ip', 'Invalid IP address', (value) =>
      value === undefined || value.trim() === ''
        ? true
        : value.split('.').find((i) => parseInt(i, 10) > 255) === undefined
    )
    .required('LAN Address is a required field'),
  addressWAN: yup
    .string()
    .matches(/(^(\d{1,3}\.){3}(\d{1,3})$)/, {
      message: 'Invalid IP address',
      excludeEmptyString: true,
    })
    .test('ip', 'Invalid IP address', (value) =>
      value === undefined || value.trim() === ''
        ? true
        : value.split('.').find((i) => parseInt(i, 10) > 255) === undefined
    )
    .required('WAN Address is a required field'),
  IMEI: yup.string().when('make', {
    is: 'GTT',
    then: yup.string().matches('[0-9]{15}$', 'Must be 15 digits'),
    otherwise: yup
      .string()
      .matches('[0-9]{15}$', 'Must be 15 digits')
      .required('IMEI is a required field'),
  }),
  make: yup
    .string()
    .oneOf(['GTT', 'Sierra Wireless', 'Cradlepoint'])
    .required('Make is a required field'),
  model: yup.string().when('make', {
    is: 'GTT',
    then: yup
      .string()
      .oneOf(['2100', '2101'])
      .required('Model is a required field'),
    otherwise: yup
      .string()
      .oneOf(['MP-70', 'IBR900', 'IBR1700', 'R1900'])
      .required('Model is a required field'),
  }),
});

const intersectionSchema = yup.object({
  intersectionName: yup
    .string()
    .matches(
      '^[A-Za-z0-9\\s\\w]+$',
      'Must contain alphanumeric characters, spaces or underscores.'
    )
    .max(50, 'Must be 50 characters or less')
    .required('Name is a required field'),
  longitude: yup
    .number()
    .test('is-decimal', 'Invalid longitude, must contain 6 digits after decimal', (value) =>
      `${value}`.match(/^-?\d*\.\d{6}$/)
    )
    .min(-180)
    .max(180)
    .required('Longitude is a required field'),
  latitude: yup
    .number()
    .test('is-decimal', 'Invalid latitude, must contain 6 digits after decimal', (value) =>
      `${value}`.match(/^-?\d*\.\d{6}$/)
    )
    .min(-90)
    .max(90)
    .required('Latitude is a required field'),
});

export {
  regionSchema,
  editRegionSchema,
  agencySchema,
  vehicleSchema,
  editVehicleSchema,
  deviceSchema,
  editDeviceSchema,
  intersectionSchema,
};
