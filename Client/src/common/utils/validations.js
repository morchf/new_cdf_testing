// numeric validator for input fields 
export const numericValidator =
  ({ min, max, errorMessage }) =>
  () => ({
    validator(_, value) {
      if (!value) {
        return Promise.reject();
      }
      if (value > max || value < min) {
        return Promise.reject(new Error(errorMessage));
      }
      return Promise.resolve();
    },
  });