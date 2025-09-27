// apps/web-client/pages/_app.tsx - Main App Component with Authentication Context (Corrected)
import type { AppProps } from 'next/app';
import { AuthProvider } from '../hooks/useAuth';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}
