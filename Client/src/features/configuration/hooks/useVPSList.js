import { useCallback } from 'react';
import {
  useGetVPSSQuery,
  useRefreshVPSSMutation,
  useEditVPSSMutation,
} from '../api';

const useVPSList = ({ agyname }) => {
  const { data: vpss, isLoading } = useGetVPSSQuery({ agyname });
  const [editVPSS, editVPSSResponse] = useEditVPSSMutation();

  // Invalidates Agency cache upon edit
  const edit = useCallback(
    (data) => {
      editVPSS(data);
    },
    [editVPSS]
  );

  // Invalidates intersections cache
  const [refreshVPSS] = useRefreshVPSSMutation();

  const refresh = useCallback(() => {
    refreshVPSS();
  }, [refreshVPSS]);

  return {
    vpss,
    isLoading,
    edit,
    editVPSSResponse,
    refresh,
  };
};

export default useVPSList;
