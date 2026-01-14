import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import UploadPage from "./pages/UploadPage";
import MetadataPage from "./pages/MetadataPage";
import CaptionsPage from "./pages/CaptionsPage";
import PublishPage from "./pages/PublishPage";
import YouTubeOAuthCallback from "./pages/YouTubeOAuthCallback";
import { ToastProvider } from "./components/Toasts";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "upload", element: <UploadPage /> },
      { path: "video/:id/metadata", element: <MetadataPage /> },
      { path: "video/:id/captions", element: <CaptionsPage /> },
      { path: "video/:id/publish", element: <PublishPage /> }
    ]
  },
  { path: "/oauth/youtube/callback", element: <YouTubeOAuthCallback /> }
]);

export default function App() {
  return (
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>
  );
}
