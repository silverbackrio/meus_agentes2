// @codebuff fix: default export para main.tsx
import React from "react";
import "./App.css";
import { BrowserRouter as Router, Routes, Route, Link, Outlet, Navigate } from "react-router-dom";
import { analiseApi } from "./api/analiseApi";

import { SimulatorComponent } from "./components/Simulator/Simulator";
import { MetricasList } from "./components/Metricas/MetricasList";
import { DossiesList } from "./components/Dossies/DossiesList";
import { Painel } from "./components/Painel/Painel";
import { Dados } from "./components/Dados/Dados";
import { Carteira } from "./components/Carteira/Carteira";
import { Comparar } from "./components/Comparar/Comparar";
import { CadastroPosicao } from "./components/Carteira/CadastroPosicao";
import { Documentos } from "./components/Documentos/Documentos";

const analise = analiseApi;

// Rotas com filhos precisam de um Outlet, senão só o pai renderiza e a
// sub-rota fica em branco.
const Pagina = () => <Outlet />;

export default function App() {
  const [carregando, setCarregando] = React.useState(true);

  React.useEffect(() => {
    analise
      .listMetricas()
      .then(() => setCarregando(false))
      .catch(() => setCarregando(false));
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
          <li><Link to="/comparar">Comparar</Link></li>
          <li><Link to="/documentos">Documentos</Link></li>
        </ul>
      </nav>

      <main className="container">
        <Routes>
          <Route path="/" element={<Painel />} />
          <Route path="/analise" element={<Pagina />}>
            <Route index element={<SimulatorComponent />} />
            <Route path="simulador" element={<SimulatorComponent />} />
          </Route>
          <Route path="/dados" element={<Pagina />}>
            <Route index element={<Dados />} />
            <Route path="metricas" element={<MetricasList />} />
            <Route path="dossies" element={<DossiesList />} />
          </Route>
          <Route path="/carteira" element={<Carteira />} />
          <Route path="/carteira/nova" element={<CadastroPosicao />} />
          <Route path="/comparar" element={<Comparar />} />
          <Route path="/documentos" element={<Documentos />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </Router>
  );
}
