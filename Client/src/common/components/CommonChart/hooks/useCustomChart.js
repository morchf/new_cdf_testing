import { useCallback } from 'react';

const useCustomChart = () => {
  const onReady = useCallback((plot) => {
    // Hover to highlight
    plot.chart.interaction('legend-highlight');

    // Click to select
    plot.chart.removeInteraction('legend-filter');
  }, []);

  return { onReady };
};

export default useCustomChart;
