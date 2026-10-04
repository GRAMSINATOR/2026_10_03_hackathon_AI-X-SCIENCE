// Standalone dev preview of the Marker Frontier (npm run dev -> /frontier.html). Fixtures are served from ../fixtures:
//   ?frontier=marker_frontier.json (default) | marker_frontier.example.json     ?fixture=epistemic_field.Batch_3.json
// The integrated page mounts the same component under the Examiner Matrix (App.jsx) and passes the real onTrace.
import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import '@fontsource/inter/latin-400.css';
import '@fontsource/inter/latin-500.css';
import '@fontsource/inter/latin-600.css';
import './styles.css';
import MarkerFrontier, { loadFrontier } from './ui/MarkerFrontier.jsx';

function Preview() {
  const [state, setState] = useState(null), [traced, setTraced] = useState(null);
  useEffect(() => {
    const q = new URLSearchParams(location.search);
    const get = n => fetch('/' + n).then(r => (r.ok ? r.json() : null)).catch(() => null);
    Promise.all([loadFrontier(), get(q.get('fixture') || 'epistemic_field.Batch_3.json')]).then(async ([frontier, field]) => {
      const brief = field ? await get(`decision_brief.${field.context.batch}.json`) : null;
      setState({ frontier, field, brief });
    });
  }, []);
  if (!state) return <div className="fatal muted">Loading the frontier…</div>;
  if (!state.frontier) return <div className="fatal">No marker-frontier/1 document: run <code>python -m qc.frontier fixtures</code>.</div>;
  return (
    <div className="app">
      <header className="bar"><div className="ident"><span className="brand">EVIDENCE INSTRUMENT</span><b>{state.field ? state.field.context.batch : '—'}</b>
        <span className="muted">Agentic Marker Frontier · standalone preview</span></div></header>
      {traced && <p className="muted" role="status">Examiner Matrix target (integrated page): <b>{traced.id}</b> · {traced.text}</p>}
      <MarkerFrontier frontier={state.frontier} field={state.field} brief={state.brief} onTrace={c => setTraced(c)} />
    </div>
  );
}

createRoot(document.getElementById('root')).render(<StrictMode><Preview /></StrictMode>);
