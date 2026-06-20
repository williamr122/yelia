'use client';

import { useEffect, useState } from 'react';
import ChatApp from './react/chat/ChatApp.jsx';

export default function ChatClient() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <main className="yelia-chat-loading">
        <div>
          <strong>YELIA4AP</strong>
          <span>Cargando chat...</span>
        </div>
      </main>
    );
  }

  return <ChatApp />;
}
