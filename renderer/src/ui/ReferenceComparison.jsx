const z = value => value == null ? '—' : (Math.abs(Number(value)) < .1 ? Number(value).toPrecision(3) : Number(value).toFixed(1));

export function comparisonRows(sensitivity) {
  if (!sensitivity || !sensitivity.complete) return [];
  const ids = sensitivity.frames_evaluated || [];
  const dimensions = [...new Set(ids.flatMap(id => Object.keys(sensitivity.frames[id]?.dimensions || {})))].sort();
  return dimensions.map(dimension => ({
    dimension,
    stable: !(sensitivity.sensitive_dimensions || []).includes(dimension),
    cells: ids.map(id => {
      const row = sensitivity.frames[id]?.dimensions?.[dimension] || {};
      return { id, outside: row.outside || 0, measurable: row.measurable || 0, maxAbsZ: row.max_abs_z,
        mean: row.reference_mean, sd: row.reference_sd, regime: row.spatial_regime };
    }),
  }));
}

export default function ReferenceComparison({ field }) {
  const s = field.reference_sensitivity;
  if (!s || !s.complete) return (
    <section className="refcmp quiet" aria-label="Reference sensitivity">
      <b>REFERENCE SENSITIVITY</b><span>Joint comparison has not been evaluated for every eligible frame.</span>
    </section>
  );
  const ids = s.frames_evaluated || [];
  const rows = comparisonRows(s);
  const why = (s.findings || []).find(f => f.classification === 'reference_sensitive');
  return (
    <section className="refcmp" aria-label="Reference sensitivity comparison">
      <div className="refcmp-head">
        <div><b>REFERENCE SENSITIVITY</b><strong>{s.conclusion.replaceAll('_', ' ')}</strong></div>
        <span>Same target measurements · all eligible frames compared together</span>
      </div>
      <div className="refcmp-grid">
        <table><thead><tr><th>dimension</th>{ids.map(id => <th key={id}>{id}<small>{s.frames[id].support.n_parent_micrographs} parents · {s.frames[id].verdict}</small></th>)}</tr></thead>
          <tbody>{rows.map(row => <tr key={row.dimension} className={row.stable ? 'stable' : 'sensitive'}>
            <td>{row.dimension.replaceAll('_', ' ')}<small>{row.stable ? 'stable' : 'frame dependent'}</small></td>
            {row.cells.map(cell => <td key={cell.id}>{cell.outside}/{cell.measurable} outside<small>max |z| {z(cell.maxAbsZ)} · μ {z(cell.mean)} · σ {z(cell.sd)}</small>
              {cell.regime?.cls && <small>{cell.regime.cls} spatial regime{cell.regime.range_um ? ` · ${z(cell.regime.range_um)} µm range` : ''}</small>}</td>)}
          </tr>)}</tbody>
        </table>
        <div className="refcmp-note">
          <p><b>Stable:</b> {(s.stable_dimensions || []).map(x => x.replaceAll('_', ' ')).join(', ') || 'none'}</p>
          <p><b>Frame dependent:</b> {(s.sensitive_dimensions || []).map(x => x.replaceAll('_', ' ')).join(', ') || 'none'}</p>
          <p><b>Invariant unusual:</b> {(s.invariant_findings || []).join(', ') || 'none'}</p>
          {why && <p><b>Why a finding changes:</b> {why.dimension.replaceAll('_', ' ')} crosses a frame envelope; μ spans {why.why.reference_mean_range.map(z).join('–')}, σ spans {why.why.reference_sd_range.map(z).join('–')}, and support spans {why.why.reference_parent_range.join('–')} parents.</p>}
          <p>{s.guardrail}</p>
        </div>
      </div>
    </section>
  );
}
