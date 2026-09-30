import React from "react";
import ReactDOM from "react-dom/client";
import routes from "./routes/index.tsx";
import { RouterProvider } from "react-router-dom";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={routes}></RouterProvider>
  </React.StrictMode>
);
