import React from "react";
import { analiseApi } from "../../api/analiseApi";

interface Lancamento {
  id: number;
  linha: number;
  data: string;
  ativo: string;
  especificacao: string;
  lado: "C" | "V";
  quantidade: string;
  preco: string;
  valor: string;
  avisos: string;
  promovido: boolean;
}

interface Documento {
  id: number;
  nome_original: string;
  tipo: string;
  layout: string;
  status: string;
  as_of: string | null;
  numero_nota: string;
  corretora: string;
  avisos: string;
  lancamentos: Lancamento[];
  total_lancamentos: number;
}

const moeda = (valor: string | number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(valor));

const numero = (valor: string | number) =>
  new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 }).format(Number(valor));

export const Documentos = () => {
  const [documentos, setDocumentos] = React.useState<Documento[]>([]);
  const [texto, setTexto] = React.useState("");
  const [arquivo, setArquivo] = React.useState<File | null>(null);
  const [selecionado, setSelecionado] = React.useState<number | null>(null);
  const [erro, setErro] = React.useState<string | null>(null);
  const [mensagem, setMensagem] = React.useState<string | null>(null);
  const [ocupado, setOcupado] = React.useState(false);

  const carregar = React.useCallback(() => {
    analiseApi
      .listDocumentos()
      .then((resp) => setDocumentos(resp.data))
      .catch((e) =>
        setErro(e?.response?.data?.erro || "Não foi possível listar os documentos. A API está na 8901?"),
      );
  }, []);

  React.useEffect(() => {
    carregar();
  }, [carregar]);

  const enviar = (evento: React.FormEvent) => {
    evento.preventDefault();
    setErro(null);
    setMensagem(null);
    setOcupado(true);

    const dados = arquivo
      ? (() => {
          const form = new FormData();
          form.append("arquivo", arquivo);
          form.append("tipo", "nota_corretagem");
          form.append("nome_original", arquivo.name);
          return form;
        })()
      : { texto, tipo: "nota_corretagem", nome_original: "nota_colada.txt" };

    analiseApi
      .enviarDocumento(dados)
      .then((resp) => {
        setMensagem(
          resp.data.duplicado
            ? "Este documento já havia sido lido — nenhum lançamento foi duplicado."
            : `Documento lido: ${resp.data.total_lancamentos} lançamento(s), data-base ${resp.data.as_of}.`,
        );
        setTexto("");
        setArquivo(null);
        setSelecionado(resp.data.id);
        carregar();
        setOcupado(false);
      })
      .catch((e) => {
        const corpo = e?.response?.data;
        setErro(
          corpo
            ? `${corpo.erro ?? "Não foi possível ler o documento"} — ${corpo.sugestao ?? ""}`
            : "Não foi possível enviar o documento.",
        );
        setOcupado(false);
      });
  };

  const promover = (id: number) => {
    setErro(null);
    setMensagem(null);
    setOcupado(true);
    analiseApi
      .promoverDocumento(id)
      .then((resp) => {
        const { total_criadas, total_ignorados } = resp.data;
        setMensagem(
          `Promoção concluída: ${total_criadas} operação(ões) gravada(s)` +
            (total_ignorados ? `, ${total_ignorados} lançamento(s) ignorado(s) (venda sem posição).` : "."),
        );
        carregar();
        setOcupado(false);
      })
      .catch((e) => {
        setErro(e?.response?.data?.erro || "Não foi possível promover o documento.");
        setOcupado(false);
      });
  };

  const aberto = documentos.find((item) => item.id === selecionado);
  const disputado = (doc: Documento) => doc.lancamentos.some((lancamento) => !lancamento.promovido);

  return (
    <section className="documentos-section">
      <h2>Importar documento</h2>
      <p className="muted">
        Nota de corretagem da B3 em PDF com camada de texto ou o texto colado. A leitura é
        determinística: linha de total não vira lançamento, divergência vira aviso e venda reduz
        posição — nunca inclui.
      </p>

      {erro && <div className="error">Erro: {erro}</div>}
      {mensagem && <div className="sucesso">{mensagem}</div>}

      <form className="form-cadastro" onSubmit={enviar}>
        <label>
          <span>Texto da nota</span>
          <textarea
            rows={5}
            value={texto}
            placeholder={"Data pregão 29/10/2026\n1-BOVESPA C D2S PETR PETR4 PN N2 100 38,50 3.850,00 D"}
            onChange={(e) => setTexto(e.target.value)}
          />
        </label>
        <label>
          <span>Ou envie o arquivo (PDF/TXT)</span>
          <input
            type="file"
            accept=".pdf,.txt,text/plain,application/pdf"
            onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
          />
        </label>
        <button className="primary-btn" type="submit" disabled={ocupado || (!texto.trim() && !arquivo)}>
          {ocupado ? "Lendo..." : "Extrair lançamentos"}
        </button>
      </form>

      <h3>Documentos ({documentos.length})</h3>
      {documentos.length === 0 ? (
        <p className="vazio">Nenhum documento importado ainda.</p>
      ) : (
        <table className="tabela">
          <thead>
            <tr>
              <th>#</th>
              <th>Data-base</th>
              <th>Layout</th>
              <th>Situação</th>
              <th>Lançamentos</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {documentos.map((doc) => (
              <tr key={doc.id} className={selecionado === doc.id ? "linha-ativa" : undefined}>
                <td>{doc.id}</td>
                <td>{doc.as_of ?? "—"}</td>
                <td>{doc.layout || doc.tipo}</td>
                <td>
                  <span className={doc.status === "promovido" ? "selo ok" : "selo neutro"}>{doc.status}</span>
                </td>
                <td>{doc.total_lancamentos}</td>
                <td className="acoes-linha">
                  <button className="link-btn" onClick={() => setSelecionado(doc.id)}>
                    Ver
                  </button>
                  <button
                    className="link-btn"
                    disabled={ocupado || !disputado(doc)}
                    onClick={() => promover(doc.id)}
                  >
                    Promover
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {aberto && (
        <div className="detalhe-serie">
          <h3>
            Documento {aberto.id} · {aberto.as_of ?? "sem data"} · nota {aberto.numero_nota || "—"}
          </h3>
          {aberto.avisos && <p className="muted small">{aberto.avisos}</p>}
          {aberto.lancamentos.length === 0 ? (
            <p className="vazio">Sem lançamentos neste documento.</p>
          ) : (
            <table className="tabela tabela-compacta">
              <thead>
                <tr>
                  <th>Linha</th>
                  <th>Data</th>
                  <th>Ativo</th>
                  <th>Lado</th>
                  <th>Qtd.</th>
                  <th>Preço</th>
                  <th>Valor</th>
                  <th>Situação</th>
                </tr>
              </thead>
              <tbody>
                {aberto.lancamentos.map((lancamento) => (
                  <tr key={lancamento.id}>
                    <td>{lancamento.linha}</td>
                    <td>{lancamento.data}</td>
                    <td>
                      <strong>{lancamento.ativo}</strong>
                      <div className="muted small">{lancamento.especificacao}</div>
                    </td>
                    <td>
                      <span className={lancamento.lado === "C" ? "selo ok" : "selo fora"}>
                        {lancamento.lado === "C" ? "compra" : "venda"}
                      </span>
                    </td>
                    <td>{numero(lancamento.quantidade)}</td>
                    <td>{moeda(lancamento.preco)}</td>
                    <td>{moeda(lancamento.valor)}</td>
                    <td>{lancamento.promovido ? "na carteira" : "pendente"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  );
};
