import { useCallback, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useCreateIntersectionMutation } from '../api';
import { setIntersection } from '../store/slice';

const useCreateIntersection = () => {
  const dispatch = useDispatch();
  const [
    createIntersection,
    { data: newIntersection, error, isSuccess, isLoading },
  ] = useCreateIntersectionMutation();

  const create = useCallback(
    (i) => {
      createIntersection({ intersection: i });
    },
    [createIntersection]
  );

  useEffect(() => {
    if (newIntersection) {
      dispatch(setIntersection(newIntersection));
    }
  }, [dispatch, newIntersection]);

  return {
    create,
    newIntersection,
    error: error?.message?.error,
    isSuccess,
    isLoading,
  };
};

export default useCreateIntersection;
