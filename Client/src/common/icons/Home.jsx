import React from 'react';

const Home = ({ width = 16, height = 17, fill = '#323140', ...props }) => (
  <svg
    width={width}
    height={height}
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <path
      d="M14.666 8.945a.445.445 0 01-.315-.13L8 2.46 1.649 8.816a.444.444 0 01-.627-.627l6.667-6.667a.444.444 0 01.626 0l6.667 6.667a.444.444 0 01-.316.756z"
      fill={fill}
    />
    <path
      d="M8 3.962L2.667 9.313v5.41a.889.889 0 00.889.888h3.111v-4.444h2.667v4.444h3.11a.889.889 0 00.89-.889v-5.44L8 3.962z"
      fill={fill}
    />
  </svg>
);

export default Home;
