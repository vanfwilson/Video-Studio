import React from "react";
import { createBrowserRouter } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Editor from "./pages/Editor";
import Publish from "./pages/Publish";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "upload", element: <Upload /> },
      { path: "editor/:id", element: <Editor /> },
      { path: "publish/:id", element: <Publish /> }
    ]
  }
]);
