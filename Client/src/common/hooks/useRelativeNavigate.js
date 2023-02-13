import { useCallback } from 'react';
import { useHistory, useRouteMatch } from 'react-router-dom';

const useRelativeNavigate = () => {
  const history = useHistory();
  const { url } = useRouteMatch();

  const navigate = useCallback(
    (to) => {
      history.push(`${url.toString().replace(/\/*$/g, '')}/${to}`);
    },
    [history, url]
  );

  return navigate;
};

export default useRelativeNavigate;
