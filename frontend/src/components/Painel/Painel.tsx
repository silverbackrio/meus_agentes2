import React from "react";
import { analiseApi } from "../../api/analiseApi";

export const Painel = () => {
  const [metricas, setMetricas] = React.useState<any>(null);
  const [carregando, setCarregando] = React.useState(true);

  React.useEffect(() => {
    analiseApi.listMetricas().then((resp) => {
      setMetricas(resp.data);
      setCarregando(false);
    }).catch(() => {
      setCarregando(false);
    });
  }, []);

  if (carregando) return <div className="loading">Carregando painel...</div>;

  return (
    <section className="painel-section">
      <h2>Painel Investimentos</h2>
      {metricas && metricas.length > 0 ? (
        <ul>
          {metricas.map((m: any) => (
            <li key={m.campo || m.nome}>
              {m.nome}: {m.valor}
            </li>
          ))}
        </ul>
      ) : <p>Sem métricas disponíveis</p>}
    </section>
  );
};