// apps/web-client/lib/auth.ts - OAuth Helper Functions
export const initiateOAuth = (platform: string) => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const redirectUrl = `${baseUrl}/auth/oauth/${platform}`;
  
  // Open popup for OAuth flow
  const popup = window.open(
    redirectUrl,
    'oauth',
    'width=600,height=700,scrollbars=yes,resizable=yes'
  );

  return new Promise((resolve, reject) => {
    const checkClosed = setInterval(() => {
      if (popup?.closed) {
        clearInterval(checkClosed);
        reject(new Error('OAuth cancelled'));
      }
    }, 1000);

    // Listen for message from popup
    const messageListener = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;

      if (event.data.type === 'OAUTH_SUCCESS') {
        clearInterval(checkClosed);
        popup?.close();
        window.removeEventListener('message', messageListener);
        resolve(event.data.tokens);
      } else if (event.data.type === 'OAUTH_ERROR') {
        clearInterval(checkClosed);
        popup?.close();
        window.removeEventListener('message', messageListener);
        reject(new Error(event.data.error));
      }
    };

    window.addEventListener('message', messageListener);
  });
};