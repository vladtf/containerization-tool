import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./App.css";

import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.min.js";
import "react-toastify/dist/ReactToastify.css";

import HomePage from "./pages/HomePage";
import MessagesPage from "./pages/MessagesPage";
import ForwardingRulesPage from "./pages/ForwardingRulesPage";
import ContainersPage from "./pages/ContainersPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/messages" element={<MessagesPage />} />
        <Route path="/forwarding-rules" element={<ForwardingRulesPage />} />
        <Route path="/containers" element={<ContainersPage />} />
        <Route path="*" element={<h1>Not Found</h1>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
