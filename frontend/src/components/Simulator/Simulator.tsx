import React, { useState, useRef } from "react";
import { analiseApi, type SimulacaoInput, type SimulacaoResultado, type SimulacaoError } from "../../api/analiseApi";
import { decimalParaMoeda, decimalParaPorcentagem } from "../../utils/format";

export const SimulatorComponent = () => {
  const [quantidadeAtual, setQuantidadeAtual] = useState("");
  const [quantidadeNova, setQuantidadeNova] = useState("");
  const [precoMedioAtual, setPrecoMedioAtual] = useState("");
  const [precoNovaCompra, setPrecoNovaCompra] = useState("");
  const [proventos12m, setProventos12m] = useState("");
  const [jcpAnual, setJcpAnual] = useState("");
  const [precoAtualTela, setPrecoAtualTela] = useState("");
  
  const [resultado, setResultado] = useState<SimulacaoResultado | null>(null);
  const [erro, setErro] = useState<SimulacaoError | null>(null);
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
    setErro(null);
    if (simularRef.current) simularRef.current.disabled = false;
  };

  const validarInput = (): boolean => {
    const qtd = parseInt(quantidadeNova, 10);
    
    if (!quantidadeNova || isNaN(qtd)) {
      setErro({
        campo: "quantidade_nova",
        mensagem: "Digite uma quantidade maior que zero para simular.",
        sugestao: "Informe a quantidade de ações que deseja comprar.",
      });
      return false;
    }
    
    if (qtd <= 0) {
      setErro({
        campo: "quantidade_nova",
        mensagem: "A quantidade de ações para o aporte deve ser positiva.",
        sugestao: "Informe um número inteiro positivo.",
      });
      return false;
    }
    
    if (!precoNovaCompra || isNaN(parseFloat(precoNovaCompra))) {
      setErro({
        campo: "preco_nova_compra",
        mensagem: "Insira apenas números para o preço.",
        sugestao: "Informe o preço da ação.",
      });
      return false;
    }
    
    if (!precoMedioAtual || isNaN(parseFloat(precoMedioAtual))) {
      setErro({
        campo: "preco_medio_atual",
        mensagem: "Informe o preço médio atual.",
        sugestao: "Informe o preço médio das ações já possuídas.",
      });
      return false;
    }
    
    if (!quantidadeAtual || isNaN(parseInt(quantidadeAtual, 10))) {
      setErro({
        campo: "quantidade_atual",
        mensagem: "Informe a quantidade atual de ações.",
        sugestao: "Informe quantas ações você já possui.",
      });
      return false;
    }
    
    return true;
  };

  const handleSimular = async () => {
    if (!validarInput()) return;
    
    setCarregando(true);
    setErro(null);
    
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
      
      if (response.status === 200) {
        setResultado(response.data);
      } else {
        setErro({
          campo: "simulacao",
          mensagem: response.data?.erro || "Erro na simulação",
          sugestao: response.data?.sugestao || "Tente novamente",
        });
      }
    } catch (err: any) {
      setErro({
        campo: "simulacao",
        mensagem: "Erro ao conectar com o servidor",
        sugestao: "Verifique se o backend está rodando",
      });
    } finally {
      setCarregando(false);
    }
  };

  const getVariacaoTexto = (): string => {
    if (resultado?.preco_medio_atual === undefined || resultado?.preco_medio_atual === null) {
      return "N/A";
    }
    const variacao = ((precoNovaCompra || 0) - (precoMedioAtual || 0)) / (precoMedioAtual || 1) * 100;
    return `${variacao.toFixed(2)}%`;
  };

  return (
    <div className="simulator-panel">
      <h2>Simulador de Aporte</h2>
      
      {erro && <div className="error-message">{erro.mensagem} {erro.sugestao}</div>}
      
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
            <div className="result-value">{decimalParaMoeda(resultado.preco_medio_novo)}</div>
            <div className="result-subtitle">
              {quantidadeAtual > 0 ? (
                `(((${quantidadeAtual} × ${precoMedioAtual}) + ${quantidadeNova} × ${precoNovaCompra}) ÷ (${quantidadeAtual} + ${quantidadeNova}))`
              ) : `${precoNovaCompra} (primeira compra)`}
              ↓
              Variação: {getVariacaoTexto()}
            </div>
          </div>
          
          <div className="result-card">
            <div className="result-label">Custo Total do Aporte</div>
            <div className="result-value">{decimalParaMoeda(resultado.custo_novo_total)}</div>
            <div className="result-subtitle">
              {quantidadeNova} títulos × R$ {precoNovaCompra} = R$ {quantidadeNova * precoNovaCompra}
            </div>
          </div>
          
          {resultado.pnl !== 0 && (
            <div className="result-card">
              <div className="result-label">P&L Acumulado</div>
              <div className="result-value {resultado.pnl >= 0 ? 'positive' : 'negative'}">
                {decimalParaMoeda(resultado.pnl)} {resultado.pnl >= 0 ? "↑" : "↓"}
              </div>
              <div className="result-subtitle">
                {resultado.pnl_pct >= 0 ? "+" : ""}{decimalParaPorcentagem(resultado.pnl_pct)} sobre o custo
              </div>
            </div>
          )}
          
          {resultado.yield_on_cost_novo && (
            <div className="result-card">
              <div className="result-label">Yield on Cost Projetado</div>
              <div className="result-value">{decimalParaPorcentagem(resultado.yield_on_cost_novo)} ao ano</div>
              <div className="result-subtitle">
                +R$ {decimalParaMoeda(resultado.projecao_renda_passiva)} de dividendos/ano estimados
              </div>
            </div>
          )}
          
          {resultado.jcp_anual_por_acao && (
            <div className="result-card">
              <div className="result-label">JCP Anual por Ação</div>
              <div className="result-value">{decimalParaMoeda(resultado.jcp_anual_por_acao)}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
