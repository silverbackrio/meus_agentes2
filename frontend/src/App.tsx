// @codebuff fix: default export para main.tsx
import React from "react";
import "./App.css";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { analiseApi } from "./api/analiseApi";

import { SimulatorComponent } from "./components/Simulator/Simulator";
import { MetricasList } from "./components/Metricas/MetricasList";
import { DossiesList } from "./components/Dossies/DossiesList";
import { Painel } from "./components/Painel/Painel";
import { Dados } from "./components/Dados/Dados";
import { Carteira } from "./components/Carteira/Carteira";

const analise = analiseApi;

export default function App() {
  const [carregando, setCarregando] = React.useState(true);

  React.useEffect(() => {
    analise.listMetricas().then(() => setCarregando(false)).catch(() => setCarregando(false));
  }, []);

  if (carregando) {
    return <div className="loading">Carregando aplicação...</div>;
  }

  return (
    <Router>
      <nav className="navbar">
        <ul>
          <li><Link to="/">Painel</Link></li>
          <li><Link to="/analise">Análise</Link></li>
          <li><Link to="/dados">Dados</Link></li>
          <li><Link to="/carteira">Carteira</Link></li>
        </ul>
      </nav>

      <main className="container">
        <Routes>
          <Route path="/" element={<Painel />} />
          <Route path="/analise" element={<></>}>
            <Route index element={<></>} />
            <Route path="simulador" element={<SimulatorComponent />} />
          </Route>
          <Route path="/dados" element={<Dados />}>
            <Route index element={<></>} />
            <Route path="metricas" element={<MetricasList />} />
            <Route path="dossies" element={<DossiesList />} />
          </Route>
          <Route path="/carteira" element={<Carteira />} />
          <Route path="/comparar" element={<></>} />
        </Routes>
      </main>
    </Router>
  );
}

