/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string           // Backend orchestrator API URL for SSE events
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
