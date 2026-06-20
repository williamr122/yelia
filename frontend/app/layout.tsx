import type { ReactNode } from 'react';

export const metadata = {
  title: 'YELIA4AP',
  description: 'Asistente educativo virtual',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
