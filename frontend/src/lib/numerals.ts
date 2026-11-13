const ROMAN: [number, string][] = [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']];

/** 1 -> I, 4 -> IV: IEEE numbers sections and tables with roman numerals. */
export function roman(n: number) {
  let out = '';
  for (const [value, numeral] of ROMAN) while (n >= value) { out += numeral; n -= value; }
  return out;
}
