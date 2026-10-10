import { useRef, useState } from "react";
import { api } from "../api";
import { useAction } from "../hooks/useAction";
import { useLocale } from "../hooks/useLocale";
import { Button, Dialog, InlineNotice, TextField } from "./ui";
export function AddFundsDialog({ open, close, refresh }: { open: boolean; close: () => void; refresh: () => Promise<void> }) {
  const { w } = useLocale();
  const [amount, setAmount] = useState('100');
  const [validation, setValidation] = useState('');
  const retry = useRef<{ amount: number; key: string } | null>(null);
  const action = useAction();
  const submit = () => {
    if (!/^\d{1,7}(\.\d{1,2})?$/.test(amount.trim())) { setValidation(w("Enter a positive amount with at most two decimal places.")); return; }
    const [whole, fraction = ''] = amount.trim().split('.');
    const minor = BigInt(whole) * 100n + BigInt((fraction + '00').slice(0, 2));
    if (minor < 1n || minor > 100000000n) { setValidation(w("Enter an amount between ETB 0.01 and ETB 1,000,000.")); return; }
    setValidation('');
    if (retry.current?.amount !== Number(minor)) retry.current = { amount: Number(minor), key: crypto.randomUUID() };
    const selected = retry.current!;
    void action.run(async () => { await api('simulated_deposit', { amount: selected.amount, retry_key: selected.key }, true); retry.current = null; await refresh(); close(); }, w("Funds added to your balance."));
  };
  return <Dialog open={open} onOpenChange={value => { if (!action.busy && !value) close(); }} title={w("Add funds")} description={w("Choose the amount you need for your appointments.")}><form onSubmit={event => { event.preventDefault(); submit(); }}><TextField label={w("Amount (ETB)")} inputMode="decimal" value={amount} onChange={event => setAmount(event.target.value)} error={validation} required /><InlineNotice>{w("This adds demonstration funds only. No external payment is processed.")}</InlineNotice>{action.error && <InlineNotice tone="danger">{action.error}</InlineNotice>}<div className="actions"><Button variant="secondary" disabled={action.busy} onClick={close}>{w("Cancel")}</Button><Button type="submit" loading={action.busy}>{w("Add funds")}</Button></div></form></Dialog>;
}
