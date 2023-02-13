import axios from 'axios';
import { VPS_URL } from '../../common/constants';
export default async input => {
  const response = await axios.get(VPS_URL, {
    params: {
      customerName: input,
    },
  });

  return response.data;
};
