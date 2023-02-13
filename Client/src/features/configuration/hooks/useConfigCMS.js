import { useCallback, useMemo } from 'react';
import { useSetCMSMutation } from '../api';

const useConfigCMS = () => {
  const [config, configCMSResponse] = useSetCMSMutation();
  const { isLoading, isUninitialized, isError, status } = configCMSResponse;

  const message = useMemo(() => {
    if (isError) {
      return configCMSResponse.error.message;
    }
    return configCMSResponse.status;
  }, [configCMSResponse, isError]);

  const configCMS = useCallback(
    (data, headers) => {
      config(data, headers);
    },
    [config]
  );

  return {
    configCMSResponse,
    isLoading,
    isUninitialized,
    status,
    message,
    configCMS,
  };
};

export default useConfigCMS;
