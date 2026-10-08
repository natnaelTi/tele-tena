import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import { journeyApi } from "../journey-api";
import { Button, Card, EmptyState, InlineNotice, Skeleton, TextField } from "../components/ui";
import { PageTitle } from "../components/Domain";
import { useResource } from "../hooks/useResource";
import { useLocale } from "../hooks/useLocale";

const DEFAULT_TIMEZONE = "Africa/Addis_Ababa";
type SharedAppointment = NonNullable<Awaited<ReturnType<typeof journeyApi.clinicScheduleWeek>>>["appointments"][number];

function dateInZone(instant: Date, zone: string) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: zone, year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(instant);
  const get = (type: string) => parts.find(part => part.type === type)?.value || "";
  return `${get("year")}-${get("month")}-${get("day")}`;
}

function shiftDate(value: string, amount: number) {
  const date = new Date(`${value}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + amount);
  return date.toISOString().slice(0, 10);
}

function monday(value: string) {
  const weekday = new Date(`${value}T12:00:00Z`).getUTCDay();
  return shiftDate(value, -((weekday + 6) % 7));
}

function humanDate(value: string, locale: string) {
  return new Intl.DateTimeFormat(locale, {
    timeZone: "UTC", weekday: "long", month: "short", day: "numeric",
  }).format(new Date(`${value}T12:00:00Z`));
}

function clockTime(value: string, zone: string, locale: string) {
  return new Intl.DateTimeFormat(locale, {
    timeZone: zone, hour: "numeric", minute: "2-digit",
  }).format(new Date(value));
}

function displayRange(start: string, zone: string, locale: string) {
  const end = shiftDate(start, 6);
  const fmt = new Intl.DateTimeFormat(locale, { timeZone: "UTC", month: "short", day: "numeric", year: "numeric" });
  return `${fmt.format(new Date(`${start}T12:00:00Z`))} – ${fmt.format(new Date(`${end}T12:00:00Z`))} · ${zone}`;
}

export default function ClinicCalendar() {
  const { w, locale } = useLocale();
  const today = useMemo(() => dateInZone(new Date(), DEFAULT_TIMEZONE), []);
  const [timezone, setTimezone] = useState(DEFAULT_TIMEZONE);
  const [timezoneDraft, setTimezoneDraft] = useState(DEFAULT_TIMEZONE);
  const [timezoneError, setTimezoneError] = useState("");
  const [weekStart, setWeekStart] = useState(() => monday(today));
  const preferences = useResource(journeyApi.preferences);

  useEffect(() => {
    const saved = preferences.data?.timezone;
    if (saved) {
      try {
        new Intl.DateTimeFormat("en", { timeZone: saved });
        setTimezone(saved);
        setTimezoneDraft(saved);
        setWeekStart(monday(dateInZone(new Date(), saved)));
      } catch { /* Ignore a stale invalid preference; user can choose a valid zone. */ }
    }
  }, [preferences.data?.timezone]);

  const load = useCallback(
    () => journeyApi.clinicScheduleWeek(weekStart, timezone),
    [weekStart, timezone],
  );
  const calendar = useResource(load);
  const days = useMemo(() => Array.from({ length: 7 }, (_, index) => shiftDate(weekStart, index)), [weekStart]);
  const eventsByDay = useMemo(() => {
    const groups = new Map<string, SharedAppointment[]>();
    for (const day of days) groups.set(day, []);
    for (const appointment of calendar.data?.appointments || []) {
      const day = dateInZone(new Date(appointment.start), timezone);
      groups.get(day)?.push(appointment);
    }
    for (const events of groups.values()) events.sort((a, b) => a.start.localeCompare(b.start));
    return groups;
  }, [calendar.data?.appointments, days, timezone]);

  const changeTimezone = () => {
    try {
      new Intl.DateTimeFormat("en", { timeZone: timezoneDraft });
      setTimezoneError("");
      setTimezone(timezoneDraft.trim());
    } catch {
      setTimezoneError(w("Enter a valid IANA timezone, such as Africa/Addis_Ababa."));
    }
  };

  const currentWeek = monday(dateInZone(new Date(), timezone));
  return <div className="clinic-calendar-page">
    <PageTitle eyebrow={w("CLINIC OPERATIONS")} title={w("Clinic calendar")}
      description={w("Appointments appear here only when a patient has shared their schedule with this verified clinic.")}
      action={<Button variant="secondary" onClick={() => setWeekStart(currentWeek)}><CalendarDays size={18}/>{w("Today")}</Button>} />
    <div className="clinic-calendar-toolbar">
      <div className="clinic-calendar-period" aria-label={w("Calendar week controls")}>
        <Button variant="quiet" aria-label={w("Previous week")} onClick={() => setWeekStart(value => shiftDate(value, -7))}><ChevronLeft size={20}/></Button>
        <strong>{displayRange(weekStart, timezone, locale)}</strong>
        <Button variant="quiet" aria-label={w("Next week")} onClick={() => setWeekStart(value => shiftDate(value, 7))}><ChevronRight size={20}/></Button>
      </div>
      <div className="clinic-calendar-zone">
        <TextField label={w("Display timezone")} placeholder="Africa/Addis_Ababa" value={timezoneDraft}
          error={timezoneError || undefined} onChange={event => { setTimezoneDraft(event.target.value); setTimezoneError(""); }} />
        <Button variant="secondary" onClick={changeTimezone}>{w("Update calendar")}</Button>
      </div>
    </div>
    {calendar.error && <InlineNotice tone="danger">{w("Clinic calendar could not be loaded. Check your clinic access and timezone.")} <Button variant="secondary" onClick={() => void calendar.refresh()}>{w("Try again")}</Button></InlineNotice>}
    {!calendar.error && !calendar.data && <Skeleton />}
    {calendar.data && calendar.data.appointments.length === 0 && <EmptyState title={w("No patient-shared appointments this week.")}>{w("Appointments appear only after a patient shares a future booking with this clinic.")}</EmptyState>}
    {calendar.data && calendar.data.appointments.length > 0 && <div className="clinic-week-grid" aria-label={w("Patient-shared appointment week")}>
      {days.map(day => {
        const appointments = eventsByDay.get(day) || [];
        const isToday = day === dateInZone(new Date(), timezone);
        return <section className="clinic-week-day" key={day} aria-labelledby={`clinic-day-${day}`}>
          <h2 id={`clinic-day-${day}`} className={isToday ? "is-today" : undefined}>{humanDate(day, locale)}</h2>
          {appointments.length === 0
            ? <p className="clinic-day-empty">{w("No shared appointments")}</p>
            : appointments.map((appointment, index) => <Card className="clinic-calendar-event" key={`${appointment.start}-${index}`}>
                <p className="clinic-calendar-event-time">{clockTime(appointment.start, timezone, locale)} – {clockTime(appointment.end, timezone, locale)}</p>
                <h3>{appointment.patient_label}</h3>
                <p className="supporting">{appointment.clinic_name}</p>
                <p>{appointment.service}</p>
                <p className="supporting">{appointment.minutes} {w("minutes")} · {w(appointment.format === "video" ? "Video" : "Audio")} · {appointment.appointment_timezone}</p>
                <span className="status-pill status-booked">{w(appointment.status)}</span>
              </Card>)}
        </section>;
      })}
    </div>}
  </div>;
}
