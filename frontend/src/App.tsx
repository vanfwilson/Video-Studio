import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ToastProvider } from "./components/ui";

// Pages
import Dashboard from "./pages/Dashboard";
import UploadPage from "./pages/UploadPage";
import VideoEditor from "./pages/VideoEditor";
import YouTubeCallback from "./pages/YouTubeCallback";

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/video/:id" element={<VideoEditor />} />
            <Route path="/oauth/youtube/callback" element={<YouTubeCallback />} />
            
            {/* Catch-all redirect to dashboard */}
            <Route path="*" element={<Dashboard />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;
