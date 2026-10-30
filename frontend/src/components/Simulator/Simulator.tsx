import { useState, useRef } from "react";
import { analiseApi, type SimulacaoInput, type SimulacaoResultado } from "../../api/analiseApi";
import { decimalMoedaLocal } from "../../utils/format";

export const SimulatorComponent = () => {
  const [quantidadeAtual, setQuantidadeAtual] = useState("");
  const [quantidadeNova, setQuantidadeNova] = useState("");
  const [precoMedioAtual, setPrecoMedioAtual] = useState("");
  const [precoNovaCompra, setPrecoNovaCompra] = useState("");
  const [proventos12m, setProventos12m] = useState("");
  const [jcpAnual, setJcpAnual] = useState("");
  const [precoAtualTela, setPrecoAtualTela] = useState("");

  const [resultado, setResultado] = useState<SimulacaoResultado | null>(null);
  const [carregando, setCarregando] = useState(false);

  const simularRef = useRef<HTMLButtonElement>(null);

  const limparCampos = () => {
    setQuantidadeAtual("");
    setQuantidadeNova("");
    setPrecoMedioAtual("");
    setPrecoNovaCompra("");
    setProventos12m("");
    setJcpAnual("");
    setPrecoAtualTela("");
    setResultado(null);
    if (simularRef.current) simularRef.current.disabled = false;
  };

  const validarInput = (): boolean => {
    const qtd = parseInt(quantidadeNova, 10);

    if (!quantidadeNova || isNaN(qtd)) { return false; }
    if (qtd <= 0) { return false; }
    if (!precoNovaCompra || isNaN(parseFloat(precoNovaCompra))) { return false; }
    if (!precoMedioAtual || isNaN(parseFloat(precoMedioAtual))) { return false; }
    if (!quantidadeAtual || isNaN(parseInt(quantidadeAtual, 10))) { return false; }

    return true;
  };

  const handleSimular = async () => {
    if (!validarInput()) { return; }

    setCarregando(true);

    try {
      const payload: SimulacaoInput = {
        quantidade_atual: parseInt(quantidadeAtual, 10),
        preco_medio_atual: parseFloat(precoMedioAtual),
        quantidade_nova: parseInt(quantidadeNova, 10),
        preco_nova_compra: parseFloat(precoNovaCompra),
        proventos_12m_por_acao: proventos12m ? parseFloat(proventos12m) : undefined,
        jcp_anual_por_acao: jcpAnual ? parseFloat(jcpAnual) : undefined,
        preco_atual_tela: precoAtualTela ? parseFloat(precoAtualTela) : undefined,
      };

      const response = await analiseApi.simular(payload);

      if (response.status === 200 && response.data) {
        setResultado(response.data);
      }
    } catch (err) {
      // Erro tratado pelo backend/endpoint
    } finally {
      setCarregando(false);
    }
  };

  const getVariacaoTexto = (): string => {
    if (!resultado) { return "N/A"; }
    const entrada = (precoNovaCompra ? parseFloat(precoNovaCompra) : 0) -
                    (precoMedioAtual ? parseFloat(precoMedioAtual) : 0);
    const base = Math.max(precoMedioAtual ? parseFloat(precoMedioAtual) : 1, 1);
    const variacao = (entrada / base) * 100;
    return `${variacao.toFixed(2)}%`;
  };

  return (
    <div className="simulator-panel">
      <h2>Simulador de Aporte</h2>

      <div className="form-group">
        <label>Quantidade Atual (ações já possuídas)</label>
        <input
          type="number"
          value={quantidadeAtual}
          onChange={(e) => setQuantidadeAtual(e.target.value)}
          placeholder="Ex: 100"
          disabled={carregando}
        />
      </div>

      <div className="form-group">
        <label>Preço Médio Atual (R$/ação)</label>
        <input
          type="number"
          value={precoMedioAtual}
          onChange={(e) => setPrecoMedioAtual(e.target.value)}
          step="0.01"
          placeholder="Ex: 26.50"
          disabled={carregando}
        />
      </div>

      <div className="form-group">
        <label>Quantidade Nova (ações para aporte)</label>
        <input
          type="number"
          value={quantidadeNova}
          onChange={(e) => setQuantidadeNova(e.target.value)}
          placeholder="Ex: 50"
          disabled={carregando}
        />
      </div>

      <div className="form-group">
        <label>Preço da Nova Compra (R$/ação)</label>
        <input
          type="number"
          value={precoNovaCompra}
          onChange={(e) => setPrecoNovaCompra(e.target.value)}
          step="0.01"
          placeholder="Ex: 24.00"
          disabled={carregando}
        />
      </div>

      {precoAtualTela !== "" && (
        <div className="form-group">
          <label>Preço de Tela Atual (R$/ação)</label>
          <input
            type="number"
            value={precoAtualTela}
            onChange={(e) => setPrecoAtualTela(e.target.value)}
            step="0.01"
            placeholder="Ex: 22.10"
            disabled={carregando}
          />
          <small>Usado para cálculo de P&L e YoC</small>
        </div>
      )}

      <div className="form-group">
        <label>Provento Anual Projetado por Ação (R$)</label>
        <input
          type="number"
          value={proventos12m}
          onChange={(e) => setProventos12m(e.target.value)}
          step="0.01"
          placeholder="Ex: 2.10"
          disabled={carregando}
        />
        <small>Opcional: usado no cálculo de Yield on Cost</small>
      </div>

      <div className="form-group">
        <label>JCP Anual por Ação (R$)</label>
        <input
          type="number"
          value={jcpAnual}
          onChange={(e) => setJcpAnual(e.target.value)}
          step="0.01"
          placeholder="Ex: 0.50"
          disabled={carregando}
        />
        <small>Opcional: se omitido, usa zero</small>
      </div>

      <div className="actions">
        <button
          ref={simularRef}
          onClick={handleSimular}
          disabled={carregando}
          className="primary-btn"
        >
          {carregando ? "Calculando..." : "Simular Aporte"}
        </button>
        <button onClick={limparCampos} className="secondary-btn">
          Resetar Simulação
        </button>
      </div>

      {resultado && (
        <div className="result-panel">
          <h3>Resultados da Simulação</h3>

          <div className="result-card">
            <div className="result-label">Novo Preço Médio</div>
            <div className="result-value">
              {decimalMoedaLocal(resultado.preco_medio_novo)}
            </div>
            <div className="result-subtitle">
              {Number(quantidadeAtual) > 0 ? (
                `(((${quantidadeAtual} × ${precoMedioAtual}) + ${quantidadeNova} × ${precoNovaCompra}) ÷ (${quantidadeAtual} + ${quantidadeNova}))`
              ) : `${precoNovaCompra} (primeira compra)`}
              ↓
              Variação: {getVariacaoTexto()}
            </div>
          </div>

          <div className="result-card">
            <div className="result-label">Custo Total do Aporte</div>
            <div className="result-value">
              {decimalMoedaLocal(resultado.custo_novo_total)}
            </div>
            <div className="result-subtitle">
              {quantidadeNova} títulos × R$ {precoNovaCompra} = R$ {(Number(quantidadeNova) * Number(precoNovaCompra)).toFixed(2)}
            </div>
          </div>

          {resultado.pnl !== undefined && resultado.pnl !== null && resultado.pnl !== 0 && (
            <div>
              <div className="result-card">
                <div className="result-label">P&L Acumulado</div>
                <div className={resultado.pnl < 0 ? "negative" : "positive"}>"n"
                  {decimalMoedaLocal(resultado.pnl)} {resultado.pnl < 0 ? "↓" : "↑"}
                </div>
                <div className="result-subtitle">
                  {resultado.pnl_pct >= 0 ? "+" : ""}{resultado.pnl_pct}
                </div>
              </div>
            </div>
          )}

          {resultado.yield_on_cost_novo && (
            <div className="result-card">
              <div className="result-label">Yield on Cost Projetado</div>
              <div className="result-value">
                {decimalMoedaLocal(resultado.yield_on_cost_novo)} ao ano
              </div>
              <div className="result-subtitle">
                +R$ {decimalMoedaLocal(resultado.projecao_renda_passiva)} de dividendos/ano estimados
              </div>
            </div>
          )}

          {resultado.jcp_anual_por_acao && (
            <div>
              <div className="result-label">JCP Anual por Ação</div>
              <div className="result-value">
                {decimalMoedaLocal(resultado.jcp_anual_por_acao)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};