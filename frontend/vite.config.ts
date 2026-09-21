import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 开发期通过代理访问后端，避免跨域；生产由网关统一转发 /api
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
});
