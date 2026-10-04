// Molded-polymer grain: a 160 px tile of ~1% luminance noise, generated at runtime and exposed as the CSS variable
// --grain. It is a blob: URL created in the browser, so no image is ever embedded in the page source (the public
// bundle's imagery guard stays meaningful). Until it exists, --grain falls back to a transparent layer.
export function installGrain(seed = 7) {
  if (typeof document === 'undefined' || document.documentElement.style.getPropertyValue('--grain')) return;
  const n = 160, c = document.createElement('canvas'); c.width = c.height = n;
  const g = c.getContext('2d'), img = g.createImageData(n, n), d = img.data;
  let s = seed >>> 0;
  const rnd = () => { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  for (let i = 0; i < d.length; i += 4) {
    const v = rnd() < 0.5 ? 0 : 255;                    // light or dark speck; strength comes from alpha
    d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = Math.round(rnd() * 9);   // ≤ 3.5% alpha per pixel, ~1% on average
  }
  g.putImageData(img, 0, 0);
  c.toBlob(b => { if (b) document.documentElement.style.setProperty('--grain', `url(${URL.createObjectURL(b)})`); });
}
