import { Select as AntSelect } from 'antd';
import { Make } from '../../common/enums';

export const capitalizeFirstLetter = (string) =>
  string.charAt(0).toUpperCase() + string.slice(1);

export const filterIntersections = (searchKeys) => (data) => {
  if (searchKeys.length === 0) return data;
  return data.filter(({ intersectionName, intersectionId }) => {
    const nameIdSearchKeys = searchKeys.map((sk) => [
      sk.split(' ').slice(0, -1).join(' '),
      sk.split(' ').pop(),
    ]);
    return (
      (intersectionName &&
        nameIdSearchKeys.find((sk) => sk.includes(intersectionName))) ||
      nameIdSearchKeys.find((sk) => sk.includes(intersectionId))
    );
  });
};

export const filterVehicles = (searchKeys) => (data) => {
  if (searchKeys.length === 0) return data;
  return data.filter(({ attributes }) => searchKeys.includes(attributes.name));
};

export const filterUnassignedDevices = (searchKeys) => (data) => {
  if (searchKeys.length === 0) return data;
  return data.filter(({ deviceId }) => searchKeys.includes(deviceId));
};

export const mapDataToInitialValues = (formData) => {
  if (!formData) return {};

  const initialValues = {};
  formData.forEach((data, index) => {
    Object.entries(data).forEach((entry) => {
      const [key, value] = entry;
      initialValues[`${index}-${key}`] = value;
    });
  });
  return initialValues;
};

export const generateMakeOptions = () => {
  const selectOptions = [];

  // eslint-disable-next-line no-restricted-syntax
  for (const make in Make) {
    if (make !== 'Whelen')
      selectOptions.push(
        <AntSelect.Option key={Make[make]} value={Make[make]}>
          {Make[make]}
        </AntSelect.Option>
      );
  }

  return selectOptions;
};
