import React, { useEffect } from 'react';
import Toolbar from './components/Toolbar';
import DataTable from './components/DataTable';
import StatusBar from './components/StatusBar';
import useTrelloStore from './stores/trelloStore';

function App() {
  const initializeDummyData = useTrelloStore((state) => state.initializeDummyData);

  useEffect(() => {
    initializeDummyData();
  }, [initializeDummyData]);

  return (
    <div className="flex flex-col min-h-screen bg-background text-text-primary font-data text-data leading-dense">
      <Toolbar />
      <DataTable />
      <StatusBar />
    </div>
  );
}

export default App;
