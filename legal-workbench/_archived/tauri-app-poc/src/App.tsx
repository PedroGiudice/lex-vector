import { useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { ProcessExplorer } from './components/ProcessExplorer';
import './App.css';

function App() {
  useEffect(() => {
    invoke('init_cache').catch(console.error);
  }, []);

  return <ProcessExplorer />;
}

export default App;
