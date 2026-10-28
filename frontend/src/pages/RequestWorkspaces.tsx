import {PendingPaymentReviews,DirectPaymentStatus} from '../components/DirectPayments';
import {languageName} from '../components/CareLanguages';
import CareLanguageSelect from '../components/CareLanguageSelect';
import {RequestAvailabilityCard} from '../components/RequestPresence';
import {appointmentStatus} from '../appointment-status';
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { Plus, Clock, ShieldCheck, ChevronRight } from "lucide-react";
import { journeyApi, type Disclosure } from "../journey-api";
import { api } from "../api";
import { useResource } from "../hooks/useResource";
import { useAction } from "../hooks/useAction";
import { useLocale } from "../hooks/useLocale";
import { useSession } from "../hooks/useSession";
import {
  guestDraft,
  clearGuestDraft,
  rememberReturn,
  guestTiming,
} from "../guest-intent";
import {
  PageTitle,
  money,
  date,
  DisclosurePreview,
} from "../components/Domain";
import {
  Button,
  Checkbox,
  EmptyState,
  InlineNotice,
  Select,
  Skeleton,
  TextField,
  Dialog,
  StatusBadge,
} from "../components/ui";
import { Avatar } from "../components/ProfilePhoto";
import { OfferAcceptance } from "../components/OfferAcceptance";
import {
  RequestProgress,
  RequestStageRail,
  OfferStageRail,
} from "../components/RequestProgress";
import "./RequestWorkspace.css";

type Service = { id: string; label: string };
type Offer = {
  id: string;
  clinician_name: string;
  clinician_id: string;
  specialty: string;
  start: string;
  timezone: string;
  duration_minutes: number;
  consultation_format: string;
  price_minor: number;
  price_source: string;
  state: string;
  valid_until: string;
};
type PatientRequest = {
  id: string;
  state: string;
  urgency: string;
  service: string;
  category: string;
  language: string;
  consultation_format: string;
  request_text: string;
  disclosure_snapshot: Disclosure;
  max_price_minor: number | null;
  published_at: string;
  expires_at: string;
  earliest_start?: string | null;
  latest_start?: string | null;
  timezone?: string;
  first_offer_at: string | null;
  appointment?: string | null;
  current_wave?: number;
  eligible_supply?: number | null;
  offers: Offer[];
};
type InboxRequest = {
  id: string;
  urgency: string;
  language: string;
  consultation_format: string;
  request_text: string;
  disclosure_snapshot: Disclosure;
  max_price_minor: number | null;
  earliest_start: string;
  latest_start: string;
  timezone: string;
  expires_at: string;
  category: string;
  eligible_offering_ids?: string[];
  suggested_start?: string | null;
  suggested_timezone?: string;
  own_offer_id?: string | null;
  own_offer_until?: string | null;
};
function etbToMinor(value: string) {
  if (!/^\d{1,7}(?:\.\d{1,2})?$/.test(value.trim()))
    throw new Error("Enter a price in ETB with up to two decimal places.");
  const [whole, fraction = ""] = value.trim().split(".");
  const minor = BigInt(whole) * 100n + BigInt((fraction + "00").slice(0, 2));
  if (minor < 1n || minor > 100000000n)
    throw new Error("Enter a supported positive price.");
  return Number(minor);
}
function localDateTimeInput(value: string) {
  const d = new Date(value),
    pad = (v: number) => String(v).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
const live = (r: PatientRequest) =>
  r.state === "Open" && Date.parse(r.expires_at) > Date.now();
const valid = (o: Offer) =>
  o.state === "Active" && Date.parse(o.valid_until) > Date.now();
function freshRequestKey() {
  const key = crypto.randomUUID();
  try {
    sessionStorage.setItem("teletena-open-request-retry", key);
  } catch {}
  return key;
}
function usePolling<T>(loader: () => Promise<T>, delay = 5000) {
  const current = useRef(loader);
  current.current = loader;
  const stable = useCallback(() => current.current(), []),
    resource = useResource(stable);
  useEffect(() => {
    const timer = setInterval(() => void resource.refresh(), delay);
    return () => clearInterval(timer);
  }, [delay, resource.refresh]);
  return resource;
}
const loadServices = () => journeyApi.services();
const loadPractice = () => api<any>("practice");

export function PatientRequestsWorkspace() {
  const { w } = useLocale();
  const [search, setSearch] = useSearchParams();
  const { requestId, offerId } = useParams();
  const navigate = useNavigate();
  useEffect(() => {
    if (requestId) {
      const next = new URLSearchParams({ request: requestId });
      if (offerId) next.set("offer", offerId);
      navigate("/patient/requests?" + next, { replace: true });
    }
  }, [requestId, offerId, navigate]);
  const [listView, setListView] = useState("Active");
  const location = useLocation();
  const requestDraft =
    guestDraft() ||
    (
      location.state as {
        requestDraft?: {
          request_text?: string;
          service?: string;
          service_label?: string;
          language?: string;
          format?: "audio" | "video";
        };
      } | null
    )?.requestDraft;
  const { session } = useSession();

  const services = useResource(loadServices);
  const requestResource = usePolling<PatientRequest[]>(() =>
    journeyApi.myRequests(),
  );

  const action = useAction();
  const [service, setService] = useState(() => requestDraft?.service || "");
  const [narrative, setNarrative] = useState(
    () => requestDraft?.request_text || "",
  );
  const [urgency, setUrgency] = useState<"immediate" | "scheduled">(
    guestDraft()?.urgency || "immediate",
  );
  const [language, setLanguage] = useState(
    () => requestDraft?.language || session?.profile?.preferred_care_language || "en",
  );
  const [format, setFormat] = useState<"video" | "audio">(
    requestDraft?.format || "video",
  );
  const [sharing, setSharing] = useState({
    name: !!session?.profile?.share_name,
    history: false,
  });
  const [earliest, setEarliest] = useState("");
  const [latest, setLatest] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [requestKey, setRequestKey] = useState(() => {
    try {
      return (
        sessionStorage.getItem("teletena-open-request-retry") ||
        freshRequestKey()
      );
    } catch {
      return crypto.randomUUID();
    }
  });
  const [publicationMessage, setPublicationMessage] = useState("");
  const [composerStep, setComposerStep] = useState(
    requestDraft?.request_text ? 1 : 0,
  );
  const skipSharingReview = !!session?.profile?.share_name && !!session?.profile?.share_history;
  const showSharingStep = !skipSharingReview || composerStep === 2;
  const guestPreviewPrepared = useRef(false);
  const [composerErrors, setComposerErrors] = useState<Record<string, string>>(
    {},
  );
  const [preview, setPreview] = useState<Disclosure | null>(null);
  useEffect(() => {
    if (
      guestPreviewPrepared.current ||
      !requestDraft?.request_text ||
      !service ||
      urgency !== "immediate"
    )
      return;
    guestPreviewPrepared.current = true;
    void journeyApi
      .preview(narrative, sharing)
      .then((result) => {
        setPreview(result.disclosure);
        setComposerStep(skipSharingReview ? 1 : 2);
      })
      .catch(() => {
        setComposerStep(1);
        setPublicationMessage(
          w("Review your preferences and try the sharing preview again."),
        );
      });
  }, [service, requestDraft?.request_text, urgency]);
  const continueComposer = () => {
    const errors: Record<string, string> = {};
    if (composerStep === 0 && !narrative.trim())
      errors.narrative = w("Describe the support you’re looking for.");
    if (composerStep === 1) {
      if (!service) errors.service = w("Choose a service.");
      if (maxPrice) {
        try {
          etbToMinor(maxPrice);
        } catch {
          errors.price = w(
            "Enter a positive price with at most two decimal places.",
          );
        }
      }
      if (urgency === "scheduled") {
        const start = new Date(earliest).getTime(),
          end = new Date(latest).getTime();
        if (!Number.isFinite(start))
          errors.earliest = w("Choose an earliest time.");
        if (!Number.isFinite(end)) errors.latest = w("Choose a latest time.");
        if (Number.isFinite(start) && Number.isFinite(end) && end <= start)
          errors.latest = w("The latest time must be after the earliest time.");
      }
    }
    setComposerErrors(errors);
    if (Object.keys(errors).length) return;
    if (composerStep === 1 && skipSharingReview) { publish(); return; }
    if (composerStep === 1)
      void action.run(async () => {
        const result = await journeyApi.preview(narrative, sharing);
        setPreview(result.disclosure);
        setComposerStep(2);
      });
    else setComposerStep(1);
  };
  const updateSharing = (value: typeof sharing) => {
    const next = { ...value, history: false };
    setSharing(next);
    setPreview(null);
    void action.run(async () => {
      const result = await journeyApi.preview(narrative, next);
      setPreview(result.disclosure);
    });
  };
  useEffect(() => {
    if (!service && requestDraft?.service_label && services.data) {
      const match = services.data.find(
        (item) => item.label === requestDraft.service_label,
      );
      if (match) setService(match.id);
    }
  }, [requestDraft?.service_label, service, services.data]);
  const publish = () =>
    void action.run(async () => {
      if (!service || !narrative.trim())
        throw new Error("Add a service and a short description first.");
      const payload = {
        navigation_timing: guestTiming(),
        service,
        request_text: narrative,
        urgency,
        language,
        consultation_format: format,
        sharing,
        retry_key: requestKey,
        timezone_name:
          Intl.DateTimeFormat().resolvedOptions().timeZone ||
          "Africa/Addis_Ababa",
        earliest_start:
          urgency === "scheduled" ? new Date(earliest).toISOString() : null,
        latest_start:
          urgency === "scheduled" ? new Date(latest).toISOString() : null,
        max_price_minor: maxPrice ? etbToMinor(maxPrice) : null,
      };
      let publication: any;
      try {
        publication = await journeyApi.publishRequest(payload);
      } catch (error) {
        if ((error as any)?.code !== "request_retry_changed") throw error;
        const retry = freshRequestKey();
        setRequestKey(retry);
        publication = await journeyApi.publishRequest({
          ...payload,
          retry_key: retry,
        });
      }
      clearGuestDraft();
      rememberReturn({ kind: "request", ref: publication.id });
      setPublicationMessage(
        publication?.eligible_supply === 0 && urgency === "immediate"
          ? `${w("No eligible clinician can start within")} ${publication.start_window_minutes || 30} ${w("minutes. You can keep waiting, schedule for later, or browse clinicians. Your requirements will not change automatically.")}`
          : publication?.eligible_supply === 0
            ? w(
                "Your request is saved, but no clinicians currently meet every selected requirement. Keep waiting or browse available clinicians.",
              )
            : w(
                "Your request is saved. We’ll show offers here when eligible clinicians respond. An enqueued notice does not confirm that it was seen.",
              ),
      );
      setNarrative("");
      setComposerStep(0);
      setPreview(null);
      setRequestKey(freshRequestKey());
      await requestResource.refresh();
      setSearch({ request: publication.id });
    });
  const requests = requestResource.data || [];
  const prepareForLater = (req: PatientRequest) => {
    setNarrative(req.request_text);
    setService(req.service);
    setLanguage(req.language);
    setFormat(req.consultation_format as "video" | "audio");
    setUrgency("scheduled");
    setSharing({
      name: Object.hasOwn(req.disclosure_snapshot, "name"),
      history: false,
    });
    setMaxPrice(
      req.max_price_minor === null
        ? ""
        : (req.max_price_minor / 100).toFixed(2),
    );
    setEarliest("");
    setLatest("");
    setComposerStep(1);
    setPreview(null);
    setSearch({ compose: "1" });
  };
  const isLiveRequest = (request: PatientRequest) =>
    request.state === "Open" &&
    new Date(request.expires_at).getTime() > Date.now();
  const liveRequests = requests.filter(isLiveRequest);
  const historyRequests = requests.filter((request) => !isLiveRequest(request));
  const selected = search.get("request") || requestId || "";
  const composing =
    search.get("compose") === "1" ||
    (!selected &&
      (!!requestDraft?.request_text ||
        !!narrative.trim() ||
        !liveRequests.length));
  const activeId = selected || liveRequests[0]?.id;
  useEffect(() => {
    if (!selected && !composing && activeId)
      setSearch({ request: activeId }, { replace: true });
  }, [selected, composing, activeId, setSearch]);
  const shown = listView === "Active" ? liveRequests : historyRequests;
  const choose = (id: string) => {
    setPublicationMessage("");
    setSearch({ request: id });
  };
  return (
    <section className="request-workspace" data-tour="patient-private-requests" data-tour-unsaved={!!narrative.trim()}>
      <PageTitle
        title={w("Your Private Requests")}
        description={w(
          "Post a request, compare offers and choose your clinician here.",
        )}
        action={
          <Button
            onClick={() => {
              setPublicationMessage("");
              setSearch({ compose: "1" });
            }}
          >
            <Plus size={18} />
            {w("New request")}
          </Button>
        }
      />
      <div className="request-workspace-layout">
        <aside
          className="request-workspace-index"
          aria-label={w("Your requests")}
        >
          <div
            className="request-view-switch"
            role="group"
            aria-label={w("Request views")}
          >
            {["Active", "History"].map((view) => (
              <Button
                key={view}
                variant={listView === view ? "primary" : "quiet"}
                aria-pressed={listView === view}
                onClick={() => setListView(view)}
              >
                {w(view)}
              </Button>
            ))}
          </div>
          {requestResource.error && (
            <InlineNotice tone="danger">
              {w("Requests could not be loaded.")}{" "}
              <Button
                variant="quiet"
                onClick={() => void requestResource.refresh()}
              >
                {w("Retry")}
              </Button>
            </InlineNotice>
          )}
          {!requestResource.data && !requestResource.error ? (
            <Skeleton />
          ) : shown.length ? (
            <ul className="request-compact-list">
              {shown.map((req) => (
                <li key={req.id} data-request-id={req.id}>
                  <button
                    type="button"
                    className="request-list-item"
                    aria-pressed={!composing && req.id === activeId}
                    onClick={() => choose(req.id)}
                  >
                    <strong>{req.category}</strong>
                    <span>
                      {w(
                        req.urgency === "immediate"
                          ? "As soon as possible"
                          : "Schedule for later",
                      )}
                    </span>
                    <span className="request-list-footer">
                      <span>
                        {w(
                          req.state === "Open" && !live(req)
                            ? "Expired"
                            : req.state,
                        )}
                      </span>
                      <span>
                        {req.offers.filter(valid).length} {w("Offers")}
                      </span>
                      <ChevronRight size={16} />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="request-list-empty">
              {w(
                listView === "Active"
                  ? "No open requests yet."
                  : "No previous requests.",
              )}
            </p>
          )}
          {!!narrative.trim() && !composing && (
            <Button
              variant="secondary"
              onClick={() => setSearch({ compose: "1" })}
            >
              {w("Resume draft")}
            </Button>
          )}
        </aside>
        <div className="request-workspace-main">
          {publicationMessage && (
            <InlineNotice tone="success">{publicationMessage}</InlineNotice>
          )}
          {composing ? (
            <>
              <div className="request-composer-intro">
                <h2>{w("Post a Private Request")}</h2>
                <p>
                  {w(
                    "Posting is free. Your balance is checked only when you accept an offer.",
                  )}
                </p>
                <p className="supporting">
                  {w("Open requests are not an emergency response service.")}
                </p>
              </div>
              <section
                className="open-request-composer request-guided-composer"
                id="request-composer"
                data-tour-unsaved={!!narrative.trim()}
              >
                <p className="supporting">
                  {w("Step")} {composerStep + 1} / {showSharingStep ? 3 : 2}
                </p>
                <ol
                  className="request-step-progress"
                  aria-label={w("Request steps")}
                >
                  {(showSharingStep ? [w("Describe"), w("Preferences"), w("Privacy")] : [w("Describe"), w("Preferences")]).map(
                    (label, index) => (
                      <li
                        key={label}
                        aria-current={
                          composerStep === index ? "step" : undefined
                        }
                        className={index <= composerStep ? "complete" : ""}
                      >
                        {label}
                      </li>
                    ),
                  )}
                </ol>
                {composerStep === 0 && (
                  <>
                    <h2>{w("What Would You Like Help With?")}</h2>
                    <div className="field">
                      <label htmlFor="request-narrative">
                        {w("Describe what you are looking for")}
                      </label>
                      <textarea
                        id="request-narrative"
                        rows={4}
                        maxLength={2000}
                        value={narrative}
                        onChange={(e) => setNarrative(e.target.value)}
                        placeholder={w(
                          "A few words about the support you’re seeking",
                        )}
                      />
                    </div>
                    {composerErrors.narrative && (
                      <InlineNotice tone="danger">
                        {composerErrors.narrative}
                      </InlineNotice>
                    )}
                  </>
                )}
                {composerStep === 1 && (
                  <>
                    {services.error && (
                      <InlineNotice tone="danger">
                        {w("Services could not be loaded.")}{" "}
                        <Button
                          variant="quiet"
                          onClick={() => void services.refresh()}
                        >
                          {w("Retry")}
                        </Button>
                      </InlineNotice>
                    )}
                    <Select
                      label={w("Service category")}
                      value={service}
                      onChange={(e) => setService(e.target.value)}
                    >
                      <option value="">{w("Choose a service")}</option>
                      {services.data?.map((x: Service) => (
                        <option key={x.id} value={x.id}>
                          {x.label}
                        </option>
                      ))}
                    </Select>
                    <div className="open-request-grid">
                      <Select
                        label={w("When would you like care?")}
                        value={urgency}
                        onChange={(e) =>
                          setUrgency(e.target.value as typeof urgency)
                        }
                      >
                        <option value="immediate">
                          {w("As soon as possible")}
                        </option>
                        <option value="scheduled">
                          {w("Schedule for later")}
                        </option>
                      </Select>
                      <CareLanguageSelect label={w("Consultation Language")} value={language} onChange={setLanguage} required/>
                      <Select
                        label={w("Session format")}
                        value={format}
                        onChange={(e) =>
                          setFormat(e.target.value as typeof format)
                        }
                      >
                        <option value="video">{w("Video")}</option>
                        <option value="audio">{w("Audio")}</option>
                      </Select>
                      <TextField
                        label={w("Maximum total price (ETB, optional)")}
                        inputMode="decimal"
                        value={maxPrice}
                        onChange={(e) => setMaxPrice(e.target.value)}
                      />
                    </div>
                    {urgency === "scheduled" && (
                      <div className="open-request-grid">
                        <TextField
                          label={w("Earliest time")}
                          type="datetime-local"
                          value={earliest}
                          onChange={(e) => setEarliest(e.target.value)}
                        />
                        <TextField
                          label={w("Latest time")}
                          type="datetime-local"
                          value={latest}
                          onChange={(e) => setLatest(e.target.value)}
                        />
                      </div>
                    )}
                    {Object.values(composerErrors).map((error) => (
                      <InlineNotice key={error} tone="danger">
                        {error}
                      </InlineNotice>
                    ))}
                  </>
                )}
                {composerStep === 2 && (
                  <>
                    <fieldset className="open-request-sharing">
                      <legend>{w("What clinicians will see")}</legend>
                      <Checkbox
                        label={w("Include my preferred name")}
                        checked={sharing.name}
                        disabled={action.busy}
                        onChange={(e) =>
                          updateSharing({ ...sharing, name: e.target.checked })
                        }
                      />
                      <p className="supporting">
                        {w(
                          "Saved history and files stay private until you choose a treating clinician and approve that encounter’s sharing preview.",
                        )}
                      </p>
                      <p className="supporting">
                        {w(
                          "Your request text is visible to its recipients even when your name is not shared. Avoid names and details that identify you.",
                        )}
                      </p>
                    </fieldset>
                    {preview ? (
                      <div>
                        {
                          <DisclosurePreview
                            disclosure={preview}
                            context="request"
                          />
                        }
                      </div>
                    ) : (
                      <Skeleton />
                    )}
                  </>
                )}
                {composerStep === 1 && skipSharingReview && <p className="supporting">{w('Your preferred name and request text will be shared. Saved history and files stay private until you select a treating clinician.')} <Button variant="quiet" onClick={() => {setComposerStep(2);updateSharing(sharing);}}>{w('Sharing choices')}</Button></p>}
                <div className="actions">
                  {composerStep > 0 && (
                    <Button
                      variant="secondary"
                      disabled={action.busy}
                      onClick={() => setComposerStep(composerStep - 1)}
                    >
                      {w("Back")}
                    </Button>
                  )}
                  {composerStep < 2 ? (
                    <Button loading={action.busy} onClick={continueComposer}>
                      {w(composerStep === 0 ? "Continue" : skipSharingReview ? "Publish request" : "Review privacy")}
                    </Button>
                  ) : (
                    <Button
                      loading={action.busy}
                      disabled={!preview}
                      onClick={publish}
                    >
                      {w("Publish request")}
                    </Button>
                  )}
                </div>
                {action.error && (
                  <InlineNotice tone="danger">{action.error}</InlineNotice>
                )}
              </section>
            </>
          ) : activeId ? (
            <PatientRequestThread
              key={activeId}
              requestId={activeId}
              initialOffer={search.get("offer") || offerId}
              onRefresh={requestResource.refresh}
              onLater={prepareForLater}
              onReview={(id) => setSearch({ request: activeId, offer: id })}
              onCloseOffer={() =>
                setSearch({ request: activeId }, { replace: true })
              }
            />
          ) : (
            <Skeleton />
          )}
        </div>
      </div>
    </section>
  );
}

function PatientRequestThread({
  requestId,
  initialOffer,
  onRefresh,
  onLater,
  onCloseOffer,
  onReview,
}: {
  requestId: string;
  initialOffer?: string;
  onRefresh: () => Promise<unknown>;
  onLater: (r: PatientRequest) => void;
  onCloseOffer: () => void;
  onReview: (id: string) => void;
}) {
  const { w } = useLocale(),
    resource = usePolling<PatientRequest>(() =>
      journeyApi.myRequestDetail(requestId),
    ),
    action = useAction();
  const [review, setReview] = useState(initialOffer || ""),
    [profile, setProfile] = useState<Offer | null>(null),
    [cancel, setCancel] = useState(false),
    [accepted, setAccepted] = useState(""),
    [optionsMessage, setOptionsMessage] = useState("");
  useEffect(() => setReview(initialOffer || ""), [initialOffer]);
  const request = resource.data;
  const refresh = async () => {
    await Promise.all([resource.refresh(), onRefresh()]);
  };
  if (!request)
    return resource.error ? (
      <InlineNotice tone="danger">
        {w("Request unavailable.")}{" "}
        <Button variant="quiet" onClick={() => void resource.refresh()}>
          {w("Retry")}
        </Button>
      </InlineNotice>
    ) : (
      <Skeleton />
    );
  const appointment = accepted || request.appointment,
    isLive = live(request) && !appointment,
    offers = request.offers.filter(valid),
    selected = request.offers.find((o) => o.id === review);
  return (
    <section className="request-thread" aria-label={w("Selected request")}>
      {resource.error && (
        <InlineNotice tone="danger">
          {w(
            "Updates could not be refreshed. Your last saved request is shown.",
          )}{" "}
          <Button variant="quiet" onClick={() => void resource.refresh()}>
            {w("Retry")}
          </Button>
        </InlineNotice>
      )}
      <header className="request-panel-header">
        <div>
          <h2>{request.category}</h2>
          <p>
            {w(
              request.urgency === "immediate"
                ? "As soon as possible"
                : "Schedule for later",
            )}{" "}
            · {w(request.consultation_format === "audio" ? "Audio" : "Video")} ·{" "}
            {languageName(request.language)}
          </p>
        </div>
        <StatusBadge>
          {w(
            appointment
              ? "Matched"
              : isLive
                ? "Open"
                : request.state === "Open"
                  ? "Expired"
                  : request.state,
          )}
        </StatusBadge>
      </header>
      <RequestStageRail
        state={
          appointment
            ? "Matched"
            : isLive
              ? "Open"
              : request.state === "Open"
                ? "Expired"
                : request.state
        }
        hasOffer={offers.length > 0}
      />
      <RequestProgress
        state={
          appointment
            ? "Matched"
            : isLive
              ? "Open"
              : request.state === "Open"
                ? "Expired"
                : request.state
        }
        hasOffer={offers.length > 0}
        immediate={request.urgency === "immediate"}
        eligibleSupply={request.eligible_supply}
        wave={request.current_wave}
      />
      <details className="request-context">
        <summary>
          <ShieldCheck size={18} />
          {w("Your request & sharing")}
        </summary>
        <DisclosurePreview
          disclosure={request.disclosure_snapshot}
          context="request"
        />
        <dl className="request-inline-facts">
          <div>
            <dt>{w("Published")}</dt>
            <dd>{date(request.published_at, request.timezone)}</dd>
          </div>
          <div>
            <dt>{w("Closes")}</dt>
            <dd>{date(request.expires_at, request.timezone)}</dd>
          </div>
          {request.max_price_minor !== null && (
            <div>
              <dt>{w("Maximum total price")}</dt>
              <dd>ETB {money(request.max_price_minor)}</dd>
            </div>
          )}
          {request.earliest_start && request.latest_start && (
            <div>
              <dt>{w("Requested time window")}</dt>
              <dd>
                {date(request.earliest_start, request.timezone)} –{" "}
                {date(request.latest_start, request.timezone)} ·{" "}
                {request.timezone}
              </dd>
            </div>
          )}
        </dl>
      </details>
      {appointment ? (
        <MatchedAppointmentCard appointmentId={appointment} clinician={false}/>
      ) : (
        <>
          <div className="section-line">
            <h3>
              {w("Private offers")} ({offers.length})
            </h3>
            {isLive && (
              <span className="supporting">
                {Math.max(
                  0,
                  Math.floor(
                    (Date.now() - Date.parse(request.published_at)) / 60000,
                  ),
                )}{" "}
                {w("minutes since publication")}
              </span>
            )}
          </div>
          {request.offers.length ? (
            <div className="request-offer-grid">
              {request.offers.map((offer) => {
                const available = isLive && valid(offer);
                return (
                  <article
                    className="compact-offer"
                    key={offer.id}
                    data-offer-id={offer.id}
                  >
                    <header>
                      <Avatar name={offer.clinician_name} />
                      <div>
                        <h4>{offer.clinician_name}</h4>
                        <p>{offer.specialty}</p>
                      </div>
                    </header>
                    <div className="compact-offer-price">
                      <strong>ETB {money(offer.price_minor)}</strong>
                      <span>
                        {offer.duration_minutes} {w("minutes")} ·{" "}
                        {w(
                          offer.consultation_format === "audio"
                            ? "Audio"
                            : "Video",
                        )}
                      </span>
                    </div>
                    <p>
                      <Clock size={16} />
                      <time>{date(offer.start, offer.timezone)}</time>
                    </p>
                    <small>
                      {offer.timezone} ·{" "}
                      {available
                        ? w("Offer available until") +
                          " " +
                          date(offer.valid_until, offer.timezone)
                        : w(
                            offer.state === "Active"
                              ? valid(offer)
                                ? "Offer closed"
                                : "Expired"
                              : offer.state,
                          )}
                    </small>
                    <Button variant="quiet" onClick={() => setProfile(offer)}>
                      {w("View clinician profile")}
                    </Button>
                    {available && (
                      <div className="actions">
                        <Button
                          disabled={!!resource.error || action.busy}
                          onClick={() => {
                            setReview(offer.id);
                            onReview(offer.id);
                          }}
                        >
                          {w("Review and accept")}
                        </Button>
                        <Button
                          variant="quiet"
                          loading={action.busy}
                          onClick={() =>
                            void action.run(async () => {
                              await journeyApi.respondOffer(
                                request.id,
                                offer.id,
                                "decline",
                              );
                              await refresh();
                            })
                          }
                        >
                          {w("Decline")}
                        </Button>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <EmptyState
              title={w(
                isLive
                  ? "No offers yet"
                  : "This request has no available offers.",
              )}
            >
              {w(
                isLive
                  ? "We will show eligible clinician offers here."
                  : "This outcome is retained in your history.",
              )}
            </EmptyState>
          )}
          {isLive && (!offers.length || request.eligible_supply === 0) && (
            <div className="request-next-options">
              <p>
                {w(
                  request.eligible_supply === 0
                    ? "Your request is saved, but no clinicians currently meet every selected requirement. Keep waiting or browse available clinicians."
                    : Date.now() - Date.parse(request.published_at) > 300000 &&
                        request.urgency === "immediate"
                      ? "No offer has arrived within the 3–5 minute target window. You can continue waiting, schedule for later, or browse clinicians."
                      : "No request requirements are broadened automatically.",
                )}
              </p>
              <Button variant="secondary" onClick={() => onLater(request)}>
                {w("Schedule for later")}
              </Button>
              <Link className="text-link" to="/patient/discovery">
                {w("Browse clinicians")}
              </Link>
            </div>
          )}
        </>
      )}
      {isLive && (
        <div className="request-thread-actions">
          {(request.current_wave || 1) < 3 && (
            <Button
              variant="secondary"
              loading={action.busy}
              onClick={() =>
                void action.run(async () => {
                  const result = await journeyApi.findMoreOptions(request.id);
                  await refresh();
                  setOptionsMessage(
                    !result?.notified
                      ? w(
                          "No additional clinicians currently meet your requirements. Your request remains open; you can keep waiting or browse clinicians.",
                        )
                      : "",
                  );
                })
              }
            >
              {w("Find more options")}
            </Button>
          )}
          <Button variant="quiet" onClick={() => setCancel(true)}>
            {w("Cancel request")}
          </Button>
        </div>
      )}
      {action.error && (
        <InlineNotice tone="danger">{action.error}</InlineNotice>
      )}
      {optionsMessage&&<InlineNotice>{optionsMessage}</InlineNotice>}
      {selected && isLive && valid(selected) && (
        <OfferAcceptance
          request={request}
          offer={selected}
          close={() => {
            setReview("");
            onCloseOffer();
          }}
          refresh={refresh}
          onAccepted={(result) => setAccepted(result.appointment)}
        />
      )}
      {review && (!selected || !isLive || !valid(selected)) && !appointment && (
        <InlineNotice>
          {w(
            "This offer is no longer available. Return to your request to see other options.",
          )}{" "}
          <Button
            variant="quiet"
            onClick={() => {
              setReview("");
              onCloseOffer();
            }}
          >
            {w("Close")}
          </Button>
        </InlineNotice>
      )}
      {profile && (
        <RequestClinicianPane offer={profile} close={() => setProfile(null)} />
      )}
      <Dialog
        open={cancel}
        onOpenChange={(open) => {
          if (!action.busy) setCancel(open);
        }}
        title={w("Cancel This Request?")}
        description={w(
          "Clinicians will no longer be able to respond. Existing appointments are managed separately.",
        )}
      >
        <div className="dialog-actions">
          <Button
            variant="secondary"
            disabled={action.busy}
            onClick={() => setCancel(false)}
          >
            {w("Keep request")}
          </Button>
          <Button
            variant="danger"
            loading={action.busy}
            onClick={() =>
              void action.run(async () => {
                await journeyApi.cancelRequest(request.id);
                setCancel(false);
                await refresh();
              })
            }
          >
            {w("Cancel request")}
          </Button>
        </div>
        {action.error && (
          <InlineNotice tone="danger">{action.error}</InlineNotice>
        )}
      </Dialog>
    </section>
  );
}

function RequestClinicianPane({
  offer,
  close,
}: {
  offer: Offer;
  close: () => void;
}) {
  const { w, t } = useLocale(),
    resource = useResource(
      useCallback(
        () => journeyApi.publicClinician(offer.clinician_id),
        [offer.clinician_id],
      ),
    );
  const profile = resource.data,
    metric = profile?.trust_indicators?.session_experience;
  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) close();
      }}
      title={offer.clinician_name}
      description={w("Review the clinician without leaving your request.")}
    >
      {resource.error ? (
        <InlineNotice tone="danger">
          {w("This clinician profile is unavailable or no longer approved.")}{" "}
          <Button variant="quiet" onClick={() => void resource.refresh()}>
            {w("Retry")}
          </Button>
        </InlineNotice>
      ) : !profile ? (
        <Skeleton />
      ) : (
        <>
          <div className="profile-preview-identity">
            <Avatar url={profile.photo_url} name={profile.display_name} />
            <div>
              <strong>{profile.display_name}</strong>
              <p>{profile.approval_meaning}</p>
            </div>
          </div>
          {profile.introduction && <p>{profile.introduction}</p>}
          <h3>{w("Approved Services")}</h3>
          <ul>
            {[
              ...new Set<string>(
                profile.services.map((s: any) => s.service_category || s.label),
              ),
            ].map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
          <p>
            {t("sessionExperienceMetric")}:{" "}
            {metric?.average == null
              ? t(
                  metric?.status === "new"
                    ? "sessionExperienceNew"
                    : "sessionExperienceMore",
                )
              : metric.average + " / 5"}{" "}
            · {metric?.sample_count ?? 0} {t("evidenceCount")}
          </p>
          <p className="supporting">
            {w(
              "Credential review and patient feedback are separate signals. Neither guarantees a clinical outcome.",
            )}
          </p>
        </>
      )}
      <Button variant="secondary" onClick={close}>
        {w("Back to offers")}
      </Button>
    </Dialog>
  );
}

export function ClinicianRequestsWorkspace() {
  const { w } = useLocale(),
    [search, setSearch] = useSearchParams(),
    location = useLocation(),
    navigate = useNavigate(),
    { offerId } = useParams(),
    inbox = usePolling<InboxRequest[]>(() => journeyApi.clinicianRequests()),
    practice = useResource(loadPractice),
    [view, setView] = useState(
      search.get("view") === "history"
        ? "History"
        : search.get("offer") || location.pathname.includes("/offers")
          ? "Your offers"
          : "Requests",
    ),
    [page, setPage] = useState(0);
  useEffect(() => {
    if (location.pathname.includes("/offers")) {
      const next = new URLSearchParams({
        view: search.get("view") === "history" ? "history" : "offers",
      });
      if (offerId) next.set("offer", offerId);
      navigate("/clinician/requests?" + next, { replace: true });
    }
  }, [location.pathname, offerId, navigate]);
  const offers = useResource(
    useCallback(
      () =>
        journeyApi.clinicianOffers(
          page,
          view === "History" ? "History" : "Active",
        ),
      [page, view],
    ),
  );
  useEffect(() => {
    const timer = setInterval(() => void offers.refresh(), 5000);
    return () => clearInterval(timer);
  }, [offers.refresh]);
  const selected = search.get("request") || "",
    ownOffer = search.get("offer") || offerId || "",
    fetched = useRef(new Set<string>());
  const [drafts, setDrafts] = useState<
    Record<string, { service: string; start: string; price: string }>
  >({});
  useEffect(() => {
    const ids = (inbox.data || [])
      .map((r) => r.id)
      .filter((id) => !fetched.current.has(id));
    if (ids.length)
      void journeyApi
        .acknowledgeInboxFetch(ids)
        .then(() => ids.forEach((id) => fetched.current.add(id)))
        .catch(() => undefined);
  }, [inbox.data]);
  const requests = inbox.data || [],
    current =
      requests.find((r) => r.id === selected) ||
      (!selected && !ownOffer ? requests[0] : undefined);
  useEffect(() => {
    if (view === "Requests" && !selected && !ownOffer && requests[0])
      setSearch({ request: requests[0].id }, { replace: true });
  }, [view, selected, ownOffer, requests, setSearch]);
  useEffect(() => {
    const next =
      search.get("view") === "history"
        ? "History"
        : search.get("offer") || search.get("view") === "offers"
          ? "Your offers"
          : "Requests";
    setView(next);
  }, [search]);
  const chooseView = (next: string) => {
    setView(next);
    setPage(0);
    setSearch(
      next === "Requests"
        ? {}
        : next === "History"
          ? { view: "history" }
          : { view: "offers" },
    );
  };
  return (
    <section className="request-workspace" data-tour="clinician-offers" data-tour-unsaved={Object.keys(drafts).length>0}>
      <PageTitle
        title={w("Requests & Offers")}
        description={w(
          "Review eligible requests, send a private offer and follow its outcome here.",
        )}
      />
      <RequestAvailabilityCard/><PendingPaymentReviews/>
      <div className="request-workspace-layout">
        <aside
          className="request-workspace-index"
          aria-label={w("Requests and offers")}
        >
          <div
            className="request-view-switch"
            role="group"
            aria-label={w("Offer views")}
          >
            {["Requests", "Your offers", "History"].map((tab) => (
              <Button
                key={tab}
                variant={view === tab ? "primary" : "quiet"}
                aria-pressed={view === tab}
                onClick={() => chooseView(tab)}
              >
                {w(tab)}
              </Button>
            ))}
          </div>
          {view === "Requests" ? (
            inbox.error ? (
              <InlineNotice tone="danger">
                {w("Requests could not be loaded.")}{" "}
                <Button variant="quiet" onClick={() => void inbox.refresh()}>
                  {w("Retry")}
                </Button>
              </InlineNotice>
            ) : !inbox.data ? (
              <Skeleton />
            ) : requests.length ? (
              <ul className="request-compact-list">
                {requests.map((req) => (
                  <li key={req.id} data-request-id={req.id}>
                    <button
                      type="button"
                      className="request-list-item"
                      aria-pressed={!ownOffer && current?.id === req.id}
                      onClick={() => setSearch({ request: req.id })}
                    >
                      <strong>
                        {req.disclosure_snapshot.name ||
                          req.disclosure_snapshot.alias ||
                          w("Private patient")}
                      </strong>
                      <span>{req.category}</span>
                      <span className="request-list-footer">
                        <span>
                          {w(
                            req.urgency === "immediate"
                              ? "As soon as possible"
                              : "Schedule for later",
                          )}
                        </span>
                        <ChevronRight size={16} />
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="request-list-empty">
                {w("No requests match your approved services right now.")}
              </p>
            )
          ) : (
            <>
              {offers.error ? (
                <InlineNotice tone="danger">
                  {w("Your offers could not be loaded.")}{" "}
                  <Button variant="quiet" onClick={() => void offers.refresh()}>
                    {w("Retry")}
                  </Button>
                </InlineNotice>
              ) : !offers.data ? (
                <Skeleton />
              ) : offers.data.items.length ? (
                <ul className="request-compact-list">
                  {offers.data.items.map((item) => (
                    <li key={item.id} data-offer-id={item.id}>
                      <button
                        type="button"
                        className="request-list-item"
                        aria-pressed={ownOffer === item.id}
                        onClick={() =>
                          setSearch({
                            offer: item.id,
                            view: view === "History" ? "history" : "offers",
                          })
                        }
                      >
                        <strong>{item.patient_label}</strong>
                        <span>{item.category}</span>
                        <span className="request-list-footer">
                          <span>
                            {w(
                              item.state === "Superseded"
                                ? "Not selected"
                                : item.state,
                            )}
                          </span>
                          <span>ETB {money(item.price_minor)}</span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="request-list-empty">
                  {w(
                    view === "History"
                      ? "No closed offers yet."
                      : "No active offers.",
                  )}
                </p>
              )}
              <div className="request-list-pagination">
                <Button
                  variant="quiet"
                  disabled={page === 0}
                  onClick={() => setPage(page - 1)}
                >
                  {w("Previous")}
                </Button>
                <small>
                  {w("Page")} {page + 1}
                </small>
                <Button
                  variant="quiet"
                  disabled={!offers.data?.has_more}
                  onClick={() => setPage(page + 1)}
                >
                  {w("More offers")}
                </Button>
              </div>
            </>
          )}
          <Link className="text-link request-index-help" to="/clinician">
            {w("Manage request availability")}
          </Link>
        </aside>
        <div className="request-workspace-main">
          {ownOffer ? (
            <ClinicianQuotePanel
              key={ownOffer}
              offerId={ownOffer}
              refreshLists={async () => {
                await Promise.all([inbox.refresh(), offers.refresh()]);
              }}
            />
          ) : view === "Requests" && current ? (
            <ClinicianResponsePanel
              key={current.id}
              request={current}
              offerings={practice.data?.offerings}
              practiceError={!!practice.error}
              stale={!!inbox.error}
              retryPractice={practice.refresh}
              draft={drafts[current.id]}
              setDraft={(draft) =>
                setDrafts((previous) => ({ ...previous, [current.id]: draft }))
              }
              onSubmitted={async (id) => {
                setDrafts(previous=>{const next={...previous};delete next[current.id];return next;});
                setView("Your offers");
                setSearch({ offer: id, view: "offers" });
                await Promise.all([inbox.refresh(), offers.refresh()]);
              }}
            />
          ) : selected && view === "Requests" ? (
            <InlineNotice>
              {w(
                "This request is no longer available. Only currently eligible requests are shown.",
              )}{" "}
              <Button
                variant="secondary"
                onClick={() => chooseView("Your offers")}
              >
                {w("Your offers")}
              </Button>
            </InlineNotice>
          ) : (
            <EmptyState
              title={w(
                view === "Requests"
                  ? "No requests match your approved services right now."
                  : "Choose an offer to review its outcome.",
              )}
            >
              <p>
                {w(
                  "Quotes stay private. Accepted and closed outcomes remain in your history.",
                )}
              </p>
            </EmptyState>
          )}
        </div>
      </div>
    </section>
  );
}
type ResponseDraft = { service: string; start: string; price: string };
function ClinicianResponsePanel({
  request,
  offerings,
  practiceError,
  stale,
  retryPractice,
  draft,
  setDraft,
  onSubmitted,
}: {
  request: InboxRequest;
  offerings?: { id: string; label: string; price: number; minutes: number }[];
  practiceError: boolean;
  stale: boolean;
  retryPractice: () => Promise<unknown>;
  draft?: ResponseDraft;
  setDraft: (d: ResponseDraft) => void;
  onSubmitted: (id: string) => Promise<void>;
}) {
  const { w } = useLocale(),
    action = useAction(),
    eligible = (offerings || []).filter((o) =>
      request.eligible_offering_ids?.includes(o.id),
    );
  const values = draft || {
      service: eligible[0]?.id || "",
      start: request.suggested_start
        ? localDateTimeInput(request.suggested_start)
        : "",
      price: "",
    },
    offering = eligible.find((o) => o.id === values.service);
  const [priceError, setPriceError] = useState("");
  const priceSection = useRef<HTMLDetailsElement>(null);
  return (
    <section
      className="request-thread"
      data-tour-unsaved={!request.own_offer_id && !!draft}
    >
      <header className="request-panel-header">
        <div>
          <h2>
            {request.disclosure_snapshot.name ||
              request.disclosure_snapshot.alias ||
              w("Private patient")}
          </h2>
          <p>{request.category}</p>
        </div>
        <StatusBadge>
          {w(
            request.urgency === "immediate"
              ? "As soon as possible"
              : "Schedule for later",
          )}
        </StatusBadge>
      </header>
      <div className="request-response-layout">
        <section className="request-authorized-context">
          <h3>{w("Patient Request")}</h3>
          <p className="prewrap request-authorized-narrative">{request.request_text}</p>
          <details className="request-context"><summary>{w('Patient-authorized Disclosure')}</summary><DisclosurePreview disclosure={request.disclosure_snapshot} context="received"/><p className="supporting">{w('The patient chose what to share for this request. Do not use it outside this response.')}</p></details>
          <dl className="request-inline-facts">
            <div>
              <dt>{w("Language")}</dt>
              <dd>
                {languageName(request.language)}
              </dd>
            </div>
            <div>
              <dt>{w("Session format")}</dt>
              <dd>
                {w(request.consultation_format === "audio" ? "Audio" : "Video")}
              </dd>
            </div>
            <div>
              <dt>{w("Requested time window")}</dt>
              <dd>
                {date(request.earliest_start, request.timezone)} –{" "}
                {date(request.latest_start, request.timezone)}
                <br />
                {request.timezone}
              </dd>
            </div>
            {request.max_price_minor !== null && (
              <div>
                <dt>{w("Maximum total price")}</dt>
                <dd>ETB {money(request.max_price_minor)}</dd>
              </div>
            )}
          </dl>
        </section>
        <section className="request-response-editor">
          <h3>{w("Your Private Offer")}</h3>
          {request.own_offer_id ? (
            <>
              <p>{w("Your offer is with the patient")}</p>
              <Button
                variant="secondary"
                onClick={() => void onSubmitted(request.own_offer_id!)}
              >
                {w("Review your offer")}
              </Button>
            </>
          ) : (
            <>
              {stale && (
                <InlineNotice tone="danger">
                  {w(
                    "The inbox could not be refreshed. Wait for a current eligibility check before sending.",
                  )}
                </InlineNotice>
              )}
              {practiceError ? (
                <InlineNotice tone="danger">
                  {w("Approved services could not be loaded.")}{" "}
                  <Button variant="quiet" onClick={() => void retryPractice()}>
                    {w("Retry")}
                  </Button>
                </InlineNotice>
              ) : !offerings ? (
                <Skeleton />
              ) : !eligible.length ? (
                <InlineNotice>
                  {w(
                    "No approved offering is ready for this request. Check your service scope and published offering.",
                  )}
                </InlineNotice>
              ) : (
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    let amount: number | null = null;
                    try {
                      amount = values.price ? etbToMinor(values.price) : null;
                      setPriceError("");
                    } catch {
                      setPriceError(
                        w(
                          "Enter a positive price with at most two decimal places.",
                        ),
                      );
                      if (priceSection.current) {
                        priceSection.current.open = true;
                        requestAnimationFrame(() =>
                          priceSection.current?.querySelector("input")?.focus(),
                        );
                      }
                      return;
                    }
                    void action.run(async () => {
                      if (!offering || !values.start)
                        throw new Error(
                          "Choose an approved service and proposed start time.",
                        );
                      const start = new Date(values.start);
                      if (!Number.isFinite(start.getTime()))
                        throw new Error("Choose a valid start time.");
                      const response = await journeyApi.submitOffer({
                        request_id: request.id,
                        offering: values.service,
                        start: start.toISOString(),
                        price_minor: amount,
                      });
                      await onSubmitted(response.id);
                    });
                  }}
                >
                  <Select
                    label={w("Your approved service")}
                    value={values.service}
                    disabled={action.busy}
                    onChange={(e) =>
                      setDraft({
                        ...values,
                        service: e.target.value,
                        price: "",
                      })
                    }
                  >
                    <option value="">{w("Choose a service")}</option>
                    {eligible.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.label} · {o.minutes} {w("minutes")}
                      </option>
                    ))}
                  </Select>
                  {offering && (
                    <p className="request-price-context">
                      {w("Published fee")}:{" "}
                      <strong>ETB {money(offering.price)}</strong> ·{" "}
                      {offering.minutes} {w("minutes")}
                    </p>
                  )}
                  <TextField
                    label={w("Proposed start (your device time)")}
                    type="datetime-local"
                    value={values.start}
                    required
                    disabled={action.busy}
                    onChange={(e) =>
                      setDraft({ ...values, start: e.target.value })
                    }
                  />
                  {request.suggested_start && (
                    <Button
                      variant="quiet"
                      disabled={action.busy}
                      onClick={() =>
                        setDraft({
                          ...values,
                          start: localDateTimeInput(request.suggested_start!),
                        })
                      }
                    >
                      {w("Use suggested time")}
                    </Button>
                  )}
                  <details className="request-context" ref={priceSection}>
                    <summary>{w("Custom Quote (optional)")}</summary>
                    <TextField
                      label={w("Total price (ETB)")}
                      inputMode="decimal"
                      value={values.price}
                      error={priceError || undefined}
                      placeholder={offering ? money(offering.price) : ""}
                      disabled={action.busy}
                      onChange={(e) => {
                        setPriceError("");
                        setDraft({ ...values, price: e.target.value });
                      }}
                    />
                    <p className="supporting">
                      {w(
                        "Leave blank to use your published fee. A custom quote is shown only to this patient.",
                      )}
                    </p>
                  </details>
                  <p className="supporting">
                    {w(
                      "Your quote is private. The patient selects an offer and completes the applicable payment and booking approvals.",
                    )}
                  </p>
                  <Button
                    type="submit"
                    loading={action.busy}
                    disabled={!offering || !values.start || stale}
                  >
                    {w("Send offer")}
                  </Button>
                </form>
              )}
            </>
          )}
          {action.error && (
            <InlineNotice tone="danger">{action.error}</InlineNotice>
          )}
        </section>
      </div>
    </section>
  );
}
function ClinicianQuotePanel({
  offerId,
  refreshLists,
}: {
  offerId: string;
  refreshLists: () => Promise<unknown>;
}) {
  const { w } = useLocale(),
    resource = usePolling(() => journeyApi.clinicianOffer(offerId)),
    action = useAction(),
    [withdraw, setWithdraw] = useState(false),
    item = resource.data?.items[0];
  if (!item)
    return resource.error ? (
      <InlineNotice tone="danger">
        {w("This offer is unavailable. Only your own offers can be viewed.")}{" "}
        <Button variant="quiet" onClick={() => void resource.refresh()}>
          {w("Retry")}
        </Button>
      </InlineNotice>
    ) : (
      <Skeleton />
    );
  return (
    <section className="request-thread" aria-label={w("Your offer")}>
      {resource.error && (
        <InlineNotice tone="danger">
          {w("Updates could not be refreshed. Your last saved offer is shown.")}{" "}
          <Button variant="quiet" onClick={() => void resource.refresh()}>
            {w("Retry")}
          </Button>
        </InlineNotice>
      )}
      <header className="request-panel-header">
        <div>
          <h2>{item.patient_label}</h2>
          <p>{item.category}</p>
        </div>
        <StatusBadge>
          {w(item.state === "Superseded" ? "Not selected" : item.state)}
        </StatusBadge>
      </header>
      <OfferStageRail state={item.state} />
      <RequestProgress state={item.state} clinician />
      <dl className="request-inline-facts quote-summary">
        <div>
          <dt>{w("Proposed time")}</dt>
          <dd>
            {date(item.start, item.timezone)} · {item.timezone}
          </dd>
        </div>
        <div>
          <dt>{w("Duration / format")}</dt>
          <dd>
            {item.duration_minutes} {w("minutes")} ·{" "}
            {w(item.consultation_format === "audio" ? "Audio" : "Video")}
          </dd>
        </div>
        <div>
          <dt>{w("Total fee")}</dt>
          <dd>
            <strong>ETB {money(item.price_minor)}</strong> ·{" "}
            {w(
              item.price_source === "custom" ? "Custom quote" : "Published fee",
            )}
          </dd>
        </div>
        <div>
          <dt>{w("Offer expires")}</dt>
          <dd>{date(item.valid_until, item.timezone)}</dd>
        </div>
      </dl>
      {item.state === "Accepted" && item.appointment && (
        <MatchedAppointmentCard appointmentId={item.appointment} clinician/>
      )}
      {item.state === "Active" && (
        <Button variant="secondary" onClick={() => setWithdraw(true)}>
          {w("Withdraw offer")}
        </Button>
      )}
      <Dialog
        open={withdraw}
        onOpenChange={(open) => {
          if (!action.busy) setWithdraw(open);
        }}
        title={w("Withdraw This Offer?")}
        description={w(
          "The patient will no longer be able to accept this quote.",
        )}
      >
        <div className="dialog-actions">
          <Button
            variant="secondary"
            disabled={action.busy}
            onClick={() => setWithdraw(false)}
          >
            {w("Keep offer")}
          </Button>
          <Button
            variant="danger"
            loading={action.busy}
            onClick={() =>
              void action.run(async () => {
                await journeyApi.withdrawOffer(offerId);
                setWithdraw(false);
                await Promise.all([resource.refresh(), refreshLists()]);
              })
            }
          >
            {w("Withdraw offer")}
          </Button>
        </div>
        {action.error && (
          <InlineNotice tone="danger">{action.error}</InlineNotice>
        )}
      </Dialog>
    </section>
  );
}

function MatchedAppointmentCard({appointmentId,clinician}:{appointmentId:string;clinician:boolean}){const {w}=useLocale(),resource=usePolling(()=>journeyApi.appointmentDetail(appointmentId),15000);const status=resource.data?appointmentStatus(resource.data,clinician):null;return <section className="request-success-card"><h3>{w(status?.label==='Confirmed'?'Appointment confirmed':status?.label||'Offer accepted')}</h3><p>{w('Your offer was accepted. Appointment details show its current status and next steps.')}{status?.detail?' '+w(status.detail):''}</p>{resource.data&&(clinician||(resource.data as any).you_pay)&&<DirectPaymentStatus paymentId={(resource.data as any).direct_payment_id} state={(resource.data as any).direct_payment_state} clinician={clinician}/>}
{resource.error&&<InlineNotice>{w('Appointment status could not be refreshed.')} <Button variant="quiet" onClick={()=>void resource.refresh()}>{w('Retry')}</Button></InlineNotice>}<Link className="button primary" to={(clinician?'/clinician':'/patient')+'/consultations/'+appointmentId}>{w(clinician?'Open consultation details':'View appointment')}</Link></section>;}
