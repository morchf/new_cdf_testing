const findAbsMax = (data) => {
  let absMax;

  data.forEach((item) => {
    const floatItem = parseFloat(item);
    const absItem = Math.abs(floatItem);
    if (!absMax) {
      absMax = absItem;
    } else {
      absMax = absItem > absMax ? absItem : absMax;
    }
  });

  return absMax;
};

export { findAbsMax };
