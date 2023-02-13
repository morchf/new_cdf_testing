import { useEffect, useRef } from 'react';

const useChartResize = () => {
  // Resize chart on window resize
  const chart = useRef();
  const handleResize = () => {
    if (chart?.current?.getChart) {
      const currentChart = chart.current.getChart();

      if (currentChart.triggerResize) {
        currentChart.triggerResize();
      }
    }
  };

  useEffect(() => {
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return chart;
};

export default useChartResize;
