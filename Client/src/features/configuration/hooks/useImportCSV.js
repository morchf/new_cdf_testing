import { useCallback } from 'react';
import { useGetCSVMutation } from '../api';

const useImportCSV = () => {
  const [get, getCSVResponse] = useGetCSVMutation();
  // console.log('Response: ', getCSVResponse);

  const getCSV = useCallback(
    (data, params, headers, URL) => {
      get({ data, params, headers, URL });
    },
    [get]
  );

  return {
    getCSVResponse,
    getCSV,
  };
};

export default useImportCSV;
