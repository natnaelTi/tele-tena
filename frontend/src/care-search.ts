/** Local lexical relevance from published metadata. No diagnostic classification. */
const filler = new Set('i me my am im have been feel feeling need want would like help support someone some with for about a an the and to of in on at please looking find talk talking deeggarsa barbaada koo ani naaf waliin waaee kan ስለ ለ እኔ ድጋፍ እፈልጋለሁ'.split(' '));
const normalize = (value: string) => value.normalize('NFKC').toLocaleLowerCase().replace(/[’']/g, '').replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
export function careSearchScore(query: string, values: string[]) {
  const text = normalize(values.join(' '));
  const phrase = normalize(query);
  if (!phrase) return 1;
  if (text.includes(phrase)) return 100;
  const words = [...new Set(phrase.split(' ').filter(word => !filler.has(word) && word.length > 1))];
  if (!words.length) return 1;
  const metadata = new Set(text.split(' '));
  return words.reduce((score, word) => score + (metadata.has(word) ? 1 : 0), 0);
}
