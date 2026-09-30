import { useState } from 'react'
import './App.css'

type Status = 'idle' | 'checking' | 'connected' | 'unavailable'
export default function App() {
  const [status, setStatus] = useState<Status>('idle')
  async function checkConnection() {
    setStatus('checking')
    try {
      const response = await fetch('/api/method/tele_tena.api.system.status', {
        credentials: 'same-origin', cache: 'no-store',
      })
      if (!response.ok) throw new Error('Unavailable')
      const data = await response.json()
      setStatus(data.message?.application === 'tele-tena' ? 'connected' : 'unavailable')
    } catch { setStatus('unavailable') }
  }
  return <main>
    <p className="eyebrow">TELE-TENA · DEVELOPMENT</p>
    <h1>Care begins with<br />a trusted connection.</h1>
    <p className="intro">The patient and clinician platform is taking shape. This is the technical foundation, using no real patient data or funds.</p>
    <section aria-labelledby="foundation">
      <h2 id="foundation">Foundation checkpoint</h2>
      <p>React interface → authenticated Frappe API</p>
      <button disabled={status === 'checking'} onClick={checkConnection}>Check backend connection</button>
      <p role="status">{status === 'idle' ? 'Ready to check your local bench.' : status === 'checking' ? 'Checking…' : status === 'connected' ? 'Authenticated backend connection verified.' : 'Connection unavailable. Check the bench, site routing, app installation and authenticated session.'}</p>
    </section>
    <footer>Consultations, wallet operations, localization and installation support are not yet implemented.</footer>
  </main>
}
