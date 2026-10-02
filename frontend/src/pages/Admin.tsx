import { useState } from "react";
import { journeyApi } from "../journey-api";
import { PageTitle } from "../components/Domain";
import {
  Button,
  Card,
  EmptyState,
  InlineNotice,
  Select,
  Skeleton,
  StatusBadge,
  TextField,
} from "../components/ui";
import { useAction } from "../hooks/useAction";
import { useResource } from "../hooks/useResource";
export function Applications() {
  const resource = useResource(journeyApi.applications);
  const action = useAction();
  return (
    <>
      <PageTitle
        title="Application review"
        description="Review professional evidence before granting approval. Approval does not grant access to patient records."
      />
      {action.error && (
        <InlineNotice tone="danger">{action.error}</InlineNotice>
      )}
      {resource.error && (
        <InlineNotice tone="danger">
          The queue could not be loaded.{" "}
          <Button onClick={() => void resource.refresh()}>Retry</Button>
        </InlineNotice>
      )}
      {!resource.data && !resource.error ? (
        <Skeleton />
      ) : resource.data?.length ? (
        resource.data.map((item) => (
          <Card key={item.user}>
            <StatusBadge>{item.status}</StatusBadge>
            <h2>{item.display_name || "Clinician application"}</h2>
            <p className="supporting">Application reference · {item.user}{item.submitted_at?` · Submitted ${new Date(item.submitted_at).toLocaleDateString()}`:" · Submission date unavailable"}</p>
            <p className="prewrap">{item.statement}</p>
            <div className="application-evidence"><h3>Requested service scopes</h3><p>{item.requested_service_labels?.length?item.requested_service_labels.join(", "):"No requested scopes recorded"}</p><p>Evidence: {item.evidence_complete?"Complete":"Incomplete"} · Resume: {item.resume_uploaded?"Uploaded":"Not uploaded"}</p>{item.resume_uploaded&&<Button variant="secondary" onClick={async()=>{try{const response=await fetch(`/api/method/tele_tena.api.presentation.download_resume?clinician=${encodeURIComponent(item.user)}`,{credentials:"same-origin",cache:"no-store"});if(!response.ok)throw new Error();const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download="clinician-resume.pdf";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch{window.alert("Resume could not be opened. Check your reviewer access and try again.");}}}>Open resume</Button>}</div>
            <div className="actions">
              <Button
                disabled={action.busy || item.status === "Approved"}
                onClick={() =>
                  void action.run(async () => {
                    await journeyApi.reviewApplication(item.user, "Approved");
                    await resource.refresh();
                  })
                }
              >
                Approve application
              </Button>
              <Button
                variant="secondary"
                disabled={action.busy}
                onClick={() =>
                  void action.run(async () => {
                    await journeyApi.reviewApplication(item.user, "Rejected");
                    await resource.refresh();
                  })
                }
              >
                Reject application
              </Button>
            </div>
          </Card>
        ))
      ) : (
        <EmptyState title="No applications to review.">
          Submitted applications will appear here.
        </EmptyState>
      )}
    </>
  );
}
export function Scopes() {
  const applications = useResource(journeyApi.applications);
  const services = useResource(journeyApi.services);
  const scopes = useResource(journeyApi.serviceScopes);
  const [clinician, setClinician] = useState("");
  const [service, setService] = useState("");
  const [id, setId] = useState("");
  const [label, setLabel] = useState("");
  const action = useAction();
  return (
    <>
      <PageTitle
        title="Service scopes"
        description="Approve each service separately. General clinician approval does not authorize an unapproved scope."
      />
      <div className="two-column">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void action.run(async () => {
              await journeyApi.reviewServiceScope(
                clinician,
                service,
                "Approved",
              );
              await scopes.refresh();
            });
          }}
        >
          <Select
            label="Clinician"
            required
            value={clinician}
            onChange={(e) => setClinician(e.target.value)}
          >
            <option value="">Choose clinician</option>
            {applications.data
              ?.filter((a) => a.status === "Approved")
              .map((a) => (
                <option key={a.user} value={a.user}>{a.display_name || "Clinician"} · {a.requested_service_labels?.length ? a.requested_service_labels.join(", ") : "No requested scopes"}</option>
              ))}
          </Select>
          <Select
            label="Service"
            required
            value={service}
            onChange={(e) => setService(e.target.value)}
          >
            <option value="">Choose service</option>
            {services.data?.map((s) => (
              <option value={s.id} key={s.id}>
                {s.label}
              </option>
            ))}
          </Select>
          <Button type="submit" loading={action.busy}>
            Approve service scope
          </Button>
        </form>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void action.run(async () => {
              await journeyApi.saveService(id, label);
              await services.refresh();
            });
          }}
        >
          <h2>Service catalog</h2>
          <TextField
            label="Service identifier"
            value={id}
            onChange={(e) => setId(e.target.value)}
            required
          />
          <TextField
            label="Service name"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            required
          />
          <Button variant="secondary" type="submit" loading={action.busy}>
            Save service
          </Button>
        </form>
      </div>
      {action.error && (
        <InlineNotice tone="danger">{action.error}</InlineNotice>
      )}
      <h2>Current scopes</h2>
      {scopes.data?.map((scope) => (
        <Card key={scope.clinician + scope.service}>
          <h3>{applications.data?.find(a=>a.user===scope.clinician)?.display_name || "Clinician"}</h3>
          <p>
            {scope.service} · {scope.status} <span className="supporting">· {scope.clinician}</span>
          </p>
          <Button
            variant="secondary"
            disabled={action.busy || scope.status === "Revoked"}
            onClick={() =>
              void action.run(async () => {
                await journeyApi.reviewServiceScope(
                  scope.clinician,
                  scope.service,
                  "Revoked",
                );
                await scopes.refresh();
              })
            }
          >
            Revoke scope
          </Button>
        </Card>
      ))}
    </>
  );
}
