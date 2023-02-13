import './style.css';

const TopMarker = ({ children, ...props }) => (
  <svg
    width="54"
    height="75"
    viewBox="0 0 54 75"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <g filter="url(#filter0_d)">
      <g clipPath="url(#clip0)">
        <path
          d="M7 11C7 9.89543 7.89543 9 9 9H45C46.1046 9 47 9.89543 47 11V47C47 48.1046 46.1046 49 45 49H7V11Z"
          fill="white"
        />
        <text
          className="marker__text"
          x="50%"
          y="42%"
          dominantBaseline="middle"
          textAnchor="middle"
          fill="currentColor"
        >
          {children}
        </text>
      </g>
      <path d="M7 66V46H27L7 66Z" fill="white" />
    </g>
    <defs>
      <filter
        id="filter0_d"
        x="0"
        y="-5"
        width="54"
        height="80"
        filterUnits="userSpaceOnUse"
        colorInterpolationFilters="sRGB"
      >
        <feFlood floodOpacity="0" result="BackgroundImageFix" />
        <feColorMatrix
          in="SourceAlpha"
          type="matrix"
          values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
          result="hardAlpha"
        />
        <feOffset dy="2" />
        <feGaussianBlur stdDeviation="3.5" />
        <feColorMatrix
          type="matrix"
          values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.1 0"
        />
        <feBlend
          mode="normal"
          in2="BackgroundImageFix"
          result="effect1_dropShadow"
        />
        <feBlend
          mode="normal"
          in="SourceGraphic"
          in2="effect1_dropShadow"
          result="shape"
        />
      </filter>
      <clipPath id="clip0">
        <path
          d="M7 11C7 9.89543 7.89543 9 9 9H45C46.1046 9 47 9.89543 47 11V47C47 48.1046 46.1046 49 45 49H7V11Z"
          fill="white"
        />
      </clipPath>
    </defs>
  </svg>
);

const BottomMarker = ({ children, ...props }) => (
  <svg
    className="marker"
    width="51"
    height="95"
    viewBox="0 0 51 74"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    {...props}
  >
    <g filter="url(#filter0_d)">
      <path
        d="M7 25H42C43.1046 25 44 25.8954 44 27V63C44 64.1046 43.1046 65 42 65H9C7.89543 65 7 64.1046 7 63V25Z"
        fill="white"
      />
      <text
        className="marker__text"
        x="50%"
        y="60%"
        dominantBaseline="middle"
        textAnchor="middle"
        fill="currentColor"
      >
        {children}
      </text>
      <path d="M27 25L7 25L7 5L27 25Z" fill="white" />
    </g>
    <defs>
      <filter
        id="filter0_d"
        x="0"
        y="-3"
        width="51"
        height="95"
        filterUnits="userSpaceOnUse"
        colorInterpolationFilters="sRGB"
      >
        <feFlood floodOpacity="0" result="BackgroundImageFix" />
        <feColorMatrix
          in="SourceAlpha"
          type="matrix"
          values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
          result="hardAlpha"
        />
        <feOffset dy="2" />
        <feGaussianBlur stdDeviation="3.5" />
        <feColorMatrix
          type="matrix"
          values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.1 0"
        />
        <feBlend
          mode="normal"
          in2="BackgroundImageFix"
          result="effect1_dropShadow"
        />
        <feBlend
          mode="normal"
          in="SourceGraphic"
          in2="effect1_dropShadow"
          result="shape"
        />
      </filter>
    </defs>
  </svg>
);

const Marker = ({ label, children, placement = 'bottom', ...props }) => {
  // Map labels to different lines
  const labels =
    label && typeof label === 'string'
      ? label.split('\n').map((value, index) => (
          <tspan x="50%" dy={`${index * 0.85}rem`} key={`${value}-${index}`}>
            {value}
          </tspan>
        ))
      : null;

  return placement === 'bottom' ? (
    <BottomMarker {...props}>
      {labels}
      {children}
    </BottomMarker>
  ) : (
    <TopMarker {...props}>
      {labels}
      {children}
    </TopMarker>
  );
};
export default Marker;
