/** A care query is transient UI intent, never a URL or persisted browser record.
 * It deliberately disappears after a full reload and is cleared on sign-out.
 * Nothing here sends text to the backend, analytics, or browser storage.
 */
let pendingQuery = '';
export function rememberCareQuery(value: string): void {
  pendingQuery = value.slice(0, 2000);
}
export function pendingCareQuery(): string {
  return pendingQuery;
}
export function clearCareQuery(): void {
  pendingQuery = '';
}
