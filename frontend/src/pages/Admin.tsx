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
            <h2>{item.user}</h2>
            <p className="prewrap">{item.statement}</p>
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
                <option key={a.user}>{a.user}</option>
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
          <h3>{scope.clinician}</h3>
          <p>
            {scope.service} · {scope.status}
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
