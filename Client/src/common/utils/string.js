/**
 * Compare two strings with `localeCompare` favoring strings closer to the term
 * @param {string} string1 String 1
 * @param {string} string2 String 2
 * @param {string} term Matching term
 * @return {number} Comparison value
 */
export const compareWithTerm = (string1, string2, term) => {
  const s1 = `${string1}`;
  const s2 = `${string2}`;

  if (term) {
    const s1TermComparison = term.localeCompare(s1);
    const s2TermComparison = term.localeCompare(s2);

    if (s1 === term) return -1;
    if (s2 === term) return 1;

    if (term && s1TermComparison < s2TermComparison) return -1;
    if (term && s1TermComparison > s2TermComparison) return 1;
  }

  return s1.localeCompare(s2);
};

/**
 * Pluralize a string based on a number
 * @param {string} s Base string
 * @param {number} n Number of items
 * @param {string?} pluralForm Override for specific plural form of string
 * @return {string} Pluralized string
 */
export const pluralize = (s, n, pluralForm) => {
  if (n === 1) return s;

  return pluralForm || `${s}s`;
};
