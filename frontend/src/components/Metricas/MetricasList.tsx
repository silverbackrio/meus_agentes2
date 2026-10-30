import React from "react";
import { analiseApi } from "../../api/analiseApi";

export const MetricasList = () => {
  const [metricas, setMetricas] = React.useState<any>(null);
  const [carregando, setCarregando] = React.useState(true);

  React.useEffect(() => {
    analiseApi.listMetricas().then((resp) => {
      const dados = resp.data;
      if (!dados || !Array.isArray(dados)) {
        setCarregando(false);
        return;
      }
      const lista: { nome: string; valor: string }[] = dados.map((m: any) => ({
        nome: m.nome || m.campo || "?",
        valor: typeof m.valor === "number" ? String(m.valor) : String(Number(m.valor ?? 0) || 0),
      }));
      setMetricas(lista);
      setCarregando(false);
    }).catch(() => {
      setCarregando(false);
    });
  }, []);

  if (carregando) return <div className="loading">Carregando métricas...</div>;
  if (!metricas) return <div className="loading">Sem dados</div>;

  return (
    <section className="metrics-section">
      <h2>Métricas</h2>
      <ul>
        {metricas?.map((m: { nome: string; valor: string }) => (
          <li key={m.nome} className="metric-item">
            <span className="metric-name">{m.nome}</span>
            <span className="metric-value">{m.valor}</span>
          </li>
        ))}
      </ul>
    </section>
  );
};