import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { InspectionProvider } from "./context/InspectionContext.jsx";
import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <InspectionProvider>
        <App />
      </InspectionProvider>
    </BrowserRouter>
  </React.StrictMode>
);
