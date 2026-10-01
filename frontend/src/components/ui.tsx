import { useId } from "react";
import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  LoaderCircle,
  X,
} from "lucide-react";
export function Button({
  variant = "primary",
  loading,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "quiet" | "danger";
  loading?: boolean;
}) {
  return (
    <button
      type="button"
      {...props}
      disabled={loading || props.disabled}
      className={`button ${variant} ${props.className || ""}`}
      aria-busy={loading || undefined}
    >
      {loading && <LoaderCircle className="spin" size={20} />}
      {children}
    </button>
  );
}
export function IconButton({
  label,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <Button
      {...props}
      variant="quiet"
      className="icon-button"
      aria-label={label}
      title={label}
    >
      {children}
    </Button>
  );
}
export function TextField({
  label,
  hint,
  error,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
}) {
  const uid = useId();
  const id = props.id || uid;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error || hint ? id + "-note" : undefined}
      />
      {(error || hint) && (
        <p className={error ? "field-error" : "field-hint"} id={id + "-note"}>
          {error || hint}
        </p>
      )}
    </div>
  );
}
export function PhoneField(
  props: Omit<Parameters<typeof TextField>[0], "type">,
) {
  return (
    <TextField
      {...props}
      type="tel"
      autoComplete="tel"
      inputMode="tel"
      placeholder="+251 9…"
    />
  );
}
export function OTPInput(props: Omit<Parameters<typeof TextField>[0], "type">) {
  return (
    <TextField
      {...props}
      type="text"
      inputMode="numeric"
      autoComplete="one-time-code"
      pattern="[0-9]{6}"
      maxLength={6}
      className="otp-input"
    />
  );
}
export function Select({
  label,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select {...props} id={id}>
        {children}
      </select>
    </div>
  );
}
export function Checkbox({
  label,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: ReactNode }) {
  return (
    <label className="check-field">
      <input {...props} type="checkbox" />
      <span>{label}</span>
    </label>
  );
}
export function Switch(props: Parameters<typeof Checkbox>[0]) {
  return <Checkbox {...props} role="switch" />;
}
export function RadioGroup({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  const name = useId();
  return (
    <fieldset>
      <legend>{label}</legend>
      {options.map((option) => (
        <label className="check-field" key={option}>
          <input
            type="radio"
            name={name}
            checked={value === option}
            onChange={() => onChange(option)}
          />
          {option}
        </label>
      ))}
    </fieldset>
  );
}
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`card ${className}`}>{children}</section>;
}
export function StatusBadge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
export function InlineNotice({
  children,
  tone = "info",
}: {
  children: ReactNode;
  tone?: "info" | "danger" | "success";
}) {
  return (
    <div
      className={`notice ${tone}`}
      role={tone === "danger" ? "alert" : "status"}
    >
      {tone === "success" ? (
        <CheckCircle2 size={20} />
      ) : (
        <AlertCircle size={20} />
      )}
      <div>{children}</div>
    </div>
  );
}
export function Skeleton() {
  return (
    <div className="skeleton" role="status" aria-label="Loading">
      <span />
      <span />
      <span />
    </div>
  );
}
export function EmptyState({
  title,
  children,
  action,
}: {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <div className="empty-symbol">
        <ArrowRight size={24} />
      </div>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}
export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
  drawer = false,
}: {
  open: boolean;
  onOpenChange: (value: boolean) => void;
  title: string;
  description: string;
  children: ReactNode;
  drawer?: boolean;
}) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="dialog-overlay" />
        <DialogPrimitive.Content
          className={drawer ? "dialog drawer" : "dialog"}
        >
          <DialogPrimitive.Title>{title}</DialogPrimitive.Title>
          <DialogPrimitive.Description>
            {description}
          </DialogPrimitive.Description>
          {children}
          <DialogPrimitive.Close asChild>
            <IconButton label="Close dialog" className="dialog-close">
              <X size={20} />
            </IconButton>
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
export function Toast({ children }: { children: ReactNode }) {
  return (
    <div className="toast">
      <InlineNotice tone="success">{children}</InlineNotice>
    </div>
  );
}

export function Tabs({
  items,
  value,
  onChange,
}: {
  items: { id: string; label: string; content: ReactNode }[];
  value: string;
  onChange: (id: string) => void;
}) {
  function keydown(event: React.KeyboardEvent<HTMLDivElement>) {
    const current = items.findIndex((item) => item.id === value);
    const next =
      event.key === "ArrowRight"
        ? (current + 1) % items.length
        : event.key === "ArrowLeft"
          ? (current - 1 + items.length) % items.length
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? items.length - 1
              : -1;
    if (next < 0) return;
    event.preventDefault();
    onChange(items[next].id);
    requestAnimationFrame(() =>
      document.getElementById("tab-" + items[next].id)?.focus(),
    );
  }
  const selected = items.find((item) => item.id === value) || items[0];
  return (
    <>
      <div role="tablist" className="tabs" onKeyDown={keydown}>
        {items.map((item) => (
          <button
            key={item.id}
            id={"tab-" + item.id}
            type="button"
            role="tab"
            aria-selected={item.id === selected.id}
            aria-controls="tab-panel"
            tabIndex={item.id === selected.id ? 0 : -1}
            onClick={() => onChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div
        id="tab-panel"
        role="tabpanel"
        aria-labelledby={"tab-" + selected.id}
        tabIndex={0}
      >
        {selected.content}
      </div>
    </>
  );
}
