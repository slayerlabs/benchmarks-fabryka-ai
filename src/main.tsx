import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { ModelBoardPage } from "./features/leaderboard/ModelBoard";
import "./styles.css";
createRoot(document.getElementById("root")!).render(<StrictMode><BrowserRouter><Routes><Route path="/models" element={<ModelBoardPage />} /><Route path="*" element={<Navigate to="/models" replace />} /></Routes></BrowserRouter></StrictMode>);
