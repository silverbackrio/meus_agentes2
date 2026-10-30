import React from "react";
import { analiseApi } from "../../api/analiseApi";
import { decimalMoedaLocal } from "../../utils/format";

export interface DossieItem {
  data: string;
  data_base: string;
  total: number;
  titulo?: string;
}

export const DossiesList = () => {
  const [dossies, setDossies] = React.useState<DossieItem[] | null>(null);
  const [carregando, setCarregando] = React.useState(true);
  const [erro, setErro] = React.useState<string | null>(null);

  React.useEffect(() => {
    analiseApi.listDossies().then((resp) => {
      const dados = resp.data;
      if (!dados || !Array.isArray(dados)) {
        setErro("Resposta de dossiês inválida");
        setCarregando(false);
        return;
      }
      const itens = dados.map((d: any) => ({
        data: d.data || d.data_base || "?",
        data_base: d.data_base || "?",
        total: Number(d.total) || 0,
        titulo: d.titulo || undefined,
      }));
      setDossies(itens);
      setCarregando(false);
    }).catch((_e) => {
      setErro("Erro ao carregar dossiês");
      setCarregando(false);
    });
  }, []);

  if (carregando) return <div className="loading">Carregando dossiês...</div>;
  if (erro) return <div className="error">Erro: {erro}</div>;
  if (!dossies) return <div className="loading">Sem dados</div>;

  return (
    <section className="dossies-section">
      <h2>Dossiês</h2>
      <ul>
        {dossies.map((d) => (
          <li key={d?.data ?? d?.data_base ?? ""} className="dossie-item">
            <div>
              <strong>Data:</strong> {d?.data || ""}
              <br />
              <strong>Base:</strong> {d?.data_base || ""}
              <br />
              <strong>Total:</strong> {decimalMoedaLocal(d?.total ?? 0)}
            </div>
            {d?.titulo && <span className="dossie-titulo">{d.titulo}</span>}
          </li>
        ))}
      </ul>
    </section>
  );
};