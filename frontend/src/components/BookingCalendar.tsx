import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./ui";
import { useLocale } from "../hooks/useLocale";
import "./BookingCalendar.css";
type Slot = { start: string; local_time: string };
type Day = { date: string; slots: Slot[] };
/** Dates and slots come exclusively from the authorized scheduling API. */
export function BookingCalendar({ days, fromDate, selectedDate, selectedStart, duration, onMonth, onDate, onStart }: {
  days: Day[]; fromDate: string; selectedDate: string; selectedStart: string; duration: number;
  onMonth: (date: string) => void; onDate: (date: string) => void; onStart: (start: string) => void;
}) {
  const { w, locale } = useLocale();
  const language = locale === "am" ? "am-ET" : locale === "om" ? "om-ET" : "en-GB";
  // Date-only navigation must not shift a calendar date through UTC/local conversion.
  const month = new Date(fromDate + "T12:00:00Z");
  const y = month.getUTCFullYear(), m = month.getUTCMonth();
  const dateKey = (d: Date) => d.toISOString().slice(0, 10);
  const first = new Date(Date.UTC(y, m, 1, 12));
  const count = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
  const offset = (first.getUTCDay() + 6) % 7;
  const activeDate = selectedDate || days.find(d => d.slots.length)?.date || "";
  const slots = days.find(d => d.date === activeDate)?.slots || [];
  const displayDate = (date: string, options: Intl.DateTimeFormatOptions) => new Date(date + "T12:00:00Z").toLocaleDateString(language, { ...options, timeZone: "UTC" });
  return <div className="booking-calendar">
    <section aria-label={w("Choose an available date")}>
      <div className="booking-month-heading">
        <h2>{month.toLocaleDateString(language, { month: "long", year: "numeric", timeZone: "UTC" })}</h2>
        <div><Button variant="quiet" aria-label={w("Previous month")} onClick={() => onMonth(dateKey(new Date(Date.UTC(y, m - 1, 1, 12))))}><ChevronLeft size={20} /></Button><Button variant="quiet" aria-label={w("Next month")} onClick={() => onMonth(dateKey(new Date(Date.UTC(y, m + 1, 1, 12))))}><ChevronRight size={20} /></Button></div>
      </div>
      <div className="booking-month-grid">
        {Array.from({ length: 7 }, (_, i) => <span className="booking-weekday" key={'weekday' + i}>{new Date(Date.UTC(2026, 0, 5 + i, 12)).toLocaleDateString(language, { weekday: "short", timeZone: "UTC" })}</span>)}
        {Array.from({ length: offset }, (_, i) => <span key={'blank' + i} aria-hidden="true" />)}
        {Array.from({ length: count }, (_, i) => {
          const date = dateKey(new Date(Date.UTC(y, m, i + 1, 12)));
          const available = !!days.find(d => d.date === date)?.slots.length;
          return <button type="button" key={date} disabled={!available} aria-label={displayDate(date, { dateStyle: "full" })} aria-pressed={activeDate === date} onClick={() => onDate(date)}>{i + 1}</button>;
        })}
      </div>
      <p className="supporting">{w("Only dates with available sessions can be selected.")}</p>
    </section>
    <section aria-label={w("Available times")}>
      <h2>{activeDate ? displayDate(activeDate, { weekday: "long", day: "numeric", month: "long" }) : w("Choose an available date")}</h2>
      <p>{duration} {w("minutes")}</p>
      <div className="booking-slot-grid">{slots.map(slot => <Button key={slot.start} variant={selectedStart === slot.start ? "primary" : "secondary"} aria-pressed={selectedStart === slot.start} onClick={() => onStart(slot.start)}>{slot.local_time}</Button>)}</div>
      {!slots.length && <p role="status">{w("No open times are available in this booking window.")}</p>}
    </section>
  </div>;
}
