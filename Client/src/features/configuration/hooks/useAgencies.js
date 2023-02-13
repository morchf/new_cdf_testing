import { useMemo, useCallback } from 'react';
import {
  useGetAgenciesQuery,
  useCreateAgencyMutation,
  useDeleteAgencyMutation,
} from '../api';

// Returns list of all Agencies
const useAgencies = ({ params }) => {
  const {
    data: agencies,
    isLoading,
    isError,
    error,
  } = useGetAgenciesQuery({ params });

  const agenciesList = useMemo(
    () =>
      agencies?.results?.map((agency) => ({
        description: agency.description,
        Name: agency.name,
        city: agency.attributes.city,
        state: agency.attributes.state,
        CMSId: agency.attributes.CMSId,
        timezone: agency.attributes.timezone,
        agencyCode: agency.attributes.agencyCode,
        priority: agency.attributes.priority,
        agencyID:agency.attributes.agencyID,
      })),
    [agencies]
  );

  const [create, createAgencyResponse] = useCreateAgencyMutation();

  // Invalidates Agency cache upon Agency creation
  const createAgency = useCallback(
    (data) => {
      create(data);
    },
    [create]
  );

  const [deleteAgencyHook, deleteAgencyResponse] = useDeleteAgencyMutation();

  // Invalidates Agency cache upon delete
  const deleteAgency = useCallback(
    (data) => {
      deleteAgencyHook(data);
    },
    [deleteAgencyHook]
  );

  return {
    agencies,
    agenciesList,
    isLoading,
    isError,
    error,
    createAgencyResponse,
    createAgency,
    deleteAgencyResponse,
    deleteAgency,
  };
};

export default useAgencies;
