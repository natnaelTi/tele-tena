import { useState } from "react";
import { Mic, MicOff, PhoneOff, Video } from "lucide-react";
import {
  Button,
  Card,
  Checkbox,
  Dialog,
  EmptyState,
  IconButton,
  InlineNotice,
  OTPInput,
  PhoneField,
  RadioGroup,
  Select,
  Skeleton,
  StatusBadge,
  Switch,
  Tabs,
  TextField,
  Toast,
} from "../components/ui";
import {
  ClinicianCard,
  DisclosurePreview,
  PageTitle,
} from "../components/Domain";
import { LanguageSelect, useLocale } from "../hooks/useLocale";
export default function Showcase() {
  const [tab, setTab] = useState("overview");
  const [dialog, setDialog] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [radio, setRadio] = useState("Audio and video");
  const [toast, setToast] = useState(false);
  const { w } = useLocale();
  return (
    <main className="container showcase" id="main-content">
      <PageTitle
        eyebrow="DEVELOPMENT COMPONENT SHOWCASE"
        title="A shared language for care."
        description="Real components, synthetic examples. Provisional translations need human review."
        action={<LanguageSelect />}
      />
      <section>
        <h2>Brand at small sizes</h2>
        <div className="actions">
          {[16, 24, 32].map((size) => (
            <figure key={size}>
              <img
                src={import.meta.env.BASE_URL + "brand/symbol.svg"}
                width={size}
                height={size}
                alt={`TeleTena symbol at ${size} pixels`}
              />
              <figcaption>{size}px</figcaption>
            </figure>
          ))}
          <img
            src={import.meta.env.BASE_URL + "brand/mono-lockup.svg"}
            width="210"
            alt="Monochrome TeleTena"
          />
          <div className="reversed-logo">
            <img
              src={import.meta.env.BASE_URL + "brand/reversed-lockup.svg"}
              width="210"
              alt="Reversed TeleTena"
            />
          </div>
        </div>
      </section>
      <section>
        <h2>Typography and scripts</h2>
        <h1>Space for a real conversation.</h1>
        <h2>እንክብካቤ ያግኙ። ለውይይት ቦታ ይስጡ።</h2>
        <p>Nama itti dubbachuun sitti tolu argadhu.</p>
        <p>Manrope / Noto Sans Ethiopic · 400, 500, 600, 700 · body 16/1.6</p>
      </section>
      <section>
        <h2>Colors & spacing</h2>
        <div className="swatches">
          {[
            "#126B64",
            "#0D5751",
            "#182B2A",
            "#526561",
            "#FAF9F6",
            "#FFFFFF",
            "#EAF2EE",
            "#D7E2DC",
            "#F2BC97",
          ].map((color) => (
            <div key={color}>
              <span style={{ background: color }} />
              <code>{color}</code>
            </div>
          ))}
        </div>
        <p>4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 px</p>
      </section>
      <section>
        <h2>Buttons and states</h2>
        <div className="actions">
          <Button>{w("Continue")}</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="quiet">Quiet</Button>
          <Button variant="danger">End for everyone</Button>
          <Button disabled>Disabled</Button>
          <Button loading>Saving</Button>
          <IconButton label="Mute microphone">
            <Mic size={20} />
          </IconButton>
        </div>
      </section>
      <section>
        <h2>Fields</h2>
        <div className="component-grid">
          <TextField label="Preferred name" placeholder="Your name or alias" />
          <PhoneField label={w("Phone number")} />
          <OTPInput label={w("Verification code")} defaultValue="123456" />
          <TextField
            label="Field with error"
            error="Enter a valid email address."
            defaultValue="example"
          />
          <TextField label="Disabled field" disabled value="Unavailable" />
          <Select label="Language">
            <option>English</option>
            <option>አማርኛ</option>
            <option>Afaan Oromo</option>
          </Select>
        </div>
        <Checkbox label="Share my preferred name" />
        <Switch label="Audio-only mode" />
        <RadioGroup
          label="Call format"
          value={radio}
          onChange={setRadio}
          options={["Audio and video", "Audio only"]}
        />
      </section>
      <section>
        <h2>Status, feedback and loading</h2>
        <div className="actions">
          <StatusBadge tone="success">Approved</StatusBadge>
          <StatusBadge tone="warning">Review pending</StatusBadge>
          <StatusBadge tone="danger">Unavailable</StatusBadge>
        </div>
        <InlineNotice>Only share what helps this conversation.</InlineNotice>
        <InlineNotice tone="danger">
          That change could not be saved. Try again.
        </InlineNotice>
        <InlineNotice tone="success">Your changes are saved.</InlineNotice>
        <Skeleton />
        <EmptyState title="No appointments yet.">
          Your next conversation will appear here.
        </EmptyState>
      </section>
      <section>
        <h2>Cards & disclosure</h2>
        <div className="component-grid">
          <ClinicianCard
            offer={{
              id: "showcase",
              clinician_id: "00000000-0000-4000-8000-000000000000",
              display_name: "Synthetic clinician",
              label: "Demonstration service",
              price: 50000,
              minutes: 45,
            }}
          />
          <DisclosurePreview
            disclosure={{ request: "Synthetic request for a demonstration." }}
          />
          <Card>
            <h3>Session summary</h3>
            <p>45 minutes · ETB 500.00</p>
            <p>Simulated balance</p>
          </Card>
        </div>
      </section>
      <section>
        <h2>Dialogs, drawer and toast</h2>
        <div className="actions">
          <Button onClick={() => setDialog(true)}>Open dialog</Button>
          <Button variant="secondary" onClick={() => setDrawer(true)}>
            Open drawer
          </Button>
          <Button
            variant="quiet"
            onClick={() => {
              setToast(true);
              setTimeout(() => setToast(false), 3000);
            }}
          >
            Show confirmation
          </Button>
        </div>
        <Dialog
          open={dialog}
          onOpenChange={setDialog}
          title="Review your choice"
          description="Keyboard focus stays inside this dialog. Escape closes it."
        >
          <Button onClick={() => setDialog(false)}>Continue</Button>
        </Dialog>
        <Dialog
          drawer
          open={drawer}
          onOpenChange={setDrawer}
          title="Your sharing choices"
          description="Review the details before you continue."
        >
          <Checkbox label="Share my preferred name" />
        </Dialog>
        {toast && <Toast>Changes saved.</Toast>}
      </section>
      <section>
        <h2>Navigation tabs</h2>
        <Tabs
          value={tab}
          onChange={setTab}
          items={[
            {
              id: "overview",
              label: "Overview",
              content: <p>Appointment overview</p>,
            },
            {
              id: "privacy",
              label: "Privacy",
              content: <p>Sharing choices</p>,
            },
          ]}
        />
      </section>
      <section>
        <h2>Call controls</h2>
        <div className="call-controls">
          <Button>
            <MicOff size={20} />
            Unmute
          </Button>
          <Button>
            <Video size={20} />
            Camera off
          </Button>
          <Button variant="secondary">
            <PhoneOff size={20} />
            Leave
          </Button>
          <Button variant="danger">End for everyone</Button>
        </div>
      </section>
    </main>
  );
}
