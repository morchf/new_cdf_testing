import axios from 'axios';
import VPS_URL from './constants';

export default async () => {
  const response = await axios.get(VPS_URL, {
    params: {
      customerName: 'GLOBALINFRA',
    },
  });

  return response.data;
};
