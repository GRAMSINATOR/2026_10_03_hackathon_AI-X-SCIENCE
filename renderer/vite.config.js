import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';

// Single self-contained HTML (Python injects the contract payload). In dev, fixtures are served from ../fixtures.
export default defineConfig(({ command }) => ({
  plugins: [react(), viteSingleFile()],
  publicDir: command === 'serve' ? '../fixtures' : false,
  build: { assetsInlineLimit: 100000000, cssCodeSplit: false, chunkSizeWarningLimit: 4000 },
  test: { environment: 'node' },
}));
