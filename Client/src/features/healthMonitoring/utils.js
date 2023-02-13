export const filterVehicles = (searchKeys) => (data) => {
  if (searchKeys.length === 0) return data;
  return data.filter(({ name }) => searchKeys.includes(name));
};
