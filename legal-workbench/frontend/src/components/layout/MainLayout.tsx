import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { DocumentViewer } from '@/components/document/DocumentViewer';
import { AnnotationList } from '@/components/document/AnnotationList';
import { ToastContainer } from '@/components/ui/Toast';

export function MainLayout() {
  return (
    <div className="flex flex-col h-screen bg-gh-bg-primary">
      {/* Header */}
      <Header />

      {/* Main content - 3 columns */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar - Upload and patterns */}
        <Sidebar />

        {/* Center - Document viewer */}
        <main className="flex-1 overflow-hidden">
          <DocumentViewer />
        </main>

        {/* Right sidebar - Annotations */}
        <aside className="w-80">
          <AnnotationList />
        </aside>
      </div>

      {/* Toast notifications */}
      <ToastContainer />
    </div>
  );
}
