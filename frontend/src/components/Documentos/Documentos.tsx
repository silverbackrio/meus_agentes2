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

interface Diagnostico {
  nome: string;
  tamanho_bytes: number;
  tipo: string;
  paginas: number | null;
  tem_camada_texto: boolean;
  caracteres_camada: number;
  ocr_disponivel: boolean;
  ocr_motivo: string;
  recomendacao: string;
  layout_detectado: string;
  confianca: number;
  layout_reconhecido: boolean;
  previa: string;
}

const ACEITOS = ".pdf,.txt,.png,.jpg,.jpeg,.tif,.tiff,.bmp,.webp,application/pdf,image/*,text/plain";

const moeda = (valor: string | number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(Number(valor));

const numero = (valor: string | number) =>
  new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 }).format(Number(valor));

const tamanho = (bytes: number) =>
  bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(2)} MB` : `${(bytes / 1024).toFixed(0)} KB`;

export const Documentos = () => {
  const [documentos, setDocumentos] = React.useState<Documento[]>([]);
  const [texto, setTexto] = React.useState("");
  const [arquivo, setArquivo] = React.useState<File | null>(null);
  const [selecionado, setSelecionado] = React.useState<number | null>(null);
  const [diagnostico, setDiagnostico] = React.useState<Diagnostico | null>(null);
  const [erro, setErro] = React.useState<string | null>(null);
  const [detalheErro, setDetalheErro] = React.useState<string | null>(null);
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

  // Colar screenshot direto (Ctrl+V) — o caminho mais rápido no dia a dia.
  React.useEffect(() => {
    const aoColar = (evento: ClipboardEvent) => {
      const itens = evento.clipboardData?.items;
      if (!itens) return;
      for (let indice = 0; indice < itens.length; indice += 1) {
        const item = itens[indice];
        if (item.type.startsWith("image/")) {
          const blob = item.getAsFile();
          if (blob) {
            setArquivo(new File([blob], `screenshot-${Date.now()}.png`, { type: blob.type || "image/png" }));
            setDiagnostico(null);
            setMensagem("Imagem colada da área de transferência — clique em Extrair lançamentos.");
            evento.preventDefault();
          }
          break;
        }
      }
    };
    window.addEventListener("paste", aoColar);
    return () => window.removeEventListener("paste", aoColar);
  }, []);

  const montarPayload = () => {
    if (!arquivo) {
      return { texto, tipo: "nota_corretagem", nome_original: "nota_colada.txt" };
    }
    const form = new FormData();
    form.append("arquivo", arquivo);
    form.append("tipo", "nota_corretagem");
    form.append("nome_original", arquivo.name);
    return form;
  };

  const diagnosticar = () => {
    setErro(null);
    setMensagem(null);
    if (!arquivo && !texto.trim()) {
      setErro("Escolha um arquivo (PDF, imagem ou txt) ou cole o texto da nota para diagnosticar.");
      return;
    }
    setOcupado(true);
    analiseApi
      .diagnosticarDocumento(montarPayload())
      .then((resp) => {
        setDiagnostico(resp.data);
        setOcupado(false);
      })
      .catch((e) => {
        const corpo = e?.response?.data;
        setErro(corpo?.erro || "Não foi possível diagnosticar o arquivo.");
        setOcupado(false);
      });
  };

  const enviar = (evento: React.FormEvent) => {
    evento.preventDefault();
    setErro(null);
    setDetalheErro(null);
    setMensagem(null);

    if (!arquivo && !texto.trim()) {
      setErro(
        "Nada para enviar: escolha o arquivo (PDF, imagem ou txt), cole o texto da nota ou cole um screenshot com Ctrl+V.",
      );
      return;
    }

    setOcupado(true);
    analiseApi
      .enviarDocumento(montarPayload())
      .then((resp) => {
        setMensagem(
          resp.data.duplicado
            ? "Este documento já havia sido lido — nenhum lançamento foi duplicado."
            : `Documento lido: ${resp.data.total_lancamentos} lançamento(s), data-base ${resp.data.as_of}.`,
        );
        setTexto("");
        setArquivo(null);
        setDiagnostico(null);
        setSelecionado(resp.data.id);
        carregar();
        setOcupado(false);
      })
      .catch((e) => {
        const corpo = e?.response?.data;
        setErro(corpo?.erro || "Não foi possível ler o documento.");
        const partes: string[] = [];
        if (corpo?.sugestao) partes.push(corpo.sugestao);
        if (corpo?.diagnostico?.recomendacao) partes.push(corpo.diagnostico.recomendacao);
        setDetalheErro(partes.length ? partes.join(" ") : null);
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
  const pendente = (doc: Documento) => doc.lancamentos.some((lancamento) => !lancamento.promovido);

  return (
    <section className="documentos-section">
      <h2>Importar documento</h2>
      <p className="muted">
        Aceita PDF (com texto ou digitalizado), imagem/screenshot da nota (inclusive colar com Ctrl+V) e
        texto colado. A leitura é determinística: linha de total não vira lançamento, divergência vira
        aviso e venda reduz posição — nunca inclui.
      </p>

      {erro && (
        <div className="error">
          Erro: {erro}
          {detalheErro && <div className="detalhe-erro">{detalheErro}</div>}
        </div>
      )}
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
          <span>Ou o arquivo (PDF, imagem ou TXT)</span>
          <input
            type="file"
            accept={ACEITOS}
            onChange={(e) => {
              setArquivo(e.target.files?.[0] ?? null);
              setDiagnostico(null);
              setErro(null);
            }}
          />
          {arquivo && (
            <small className="ajuda">
              Selecionado: {arquivo.name} · {tamanho(arquivo.size)}
            </small>
          )}
          <small className="ajuda">Dica: cole um print da nota com Ctrl+V nesta tela.</small>
        </label>

        <div className="acoes-topo">
          <button className="primary-btn" type="submit" disabled={ocupado || (!texto.trim() && !arquivo)}>
            {ocupado ? "Lendo..." : "Extrair lançamentos"}
          </button>
          <button className="secondary-btn" type="button" onClick={diagnosticar} disabled={ocupado}>
            Diagnosticar arquivo
          </button>
        </div>
      </form>

      {diagnostico && (
        <div className="diagnostico">
          <h3>O que o servidor vê em {diagnostico.nome}</h3>
          <dl className="diagnostico-grid">
            <div>
              <dt>Tipo detectado</dt>
              <dd>{diagnostico.tipo}</dd>
            </div>
            <div>
              <dt>Tamanho</dt>
              <dd>{tamanho(diagnostico.tamanho_bytes)}</dd>
            </div>
            <div>
              <dt>Páginas</dt>
              <dd>{diagnostico.paginas ?? "—"}</dd>
            </div>
            <div>
              <dt>Camada de texto</dt>
              <dd>
                <span className={diagnostico.tem_camada_texto ? "selo ok" : "selo fora"}>
                  {diagnostico.tem_camada_texto
                    ? `${diagnostico.caracteres_camada} caracteres`
                    : "ausente (vai para OCR)"}
                </span>
              </dd>
            </div>
            <div>
              <dt>OCR</dt>
              <dd>
                <span className={diagnostico.ocr_disponivel ? "selo ok" : "selo fora"}>
                  {diagnostico.ocr_disponivel ? "disponível" : diagnostico.ocr_motivo || "indisponível"}
                </span>
              </dd>
            </div>
            <div>
              <dt>Layout reconhecido</dt>
              <dd>
                <span className={diagnostico.layout_reconhecido ? "selo ok" : "selo fora"}>
                  {diagnostico.layout_reconhecido
                    ? `${diagnostico.layout_detectado} (${(diagnostico.confianca * 100).toFixed(0)}%)`
                    : "não reconhecido"}
                </span>
              </dd>
            </div>
          </dl>
          <p className="muted">{diagnostico.recomendacao}</p>
          {diagnostico.previa && <pre className="previa">{diagnostico.previa}</pre>}
        </div>
      )}

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
                  <button className="link-btn" disabled={ocupado || !pendente(doc)} onClick={() => promover(doc.id)}>
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
