/**
 * Componente de aviso de compliance exibido em telas de simulação,
 * comparação, cenário e dossiê.
 * 
 * Regras R9 de specs/compliance-e-avisos.md: avisos obrigatórios devem
 * ser renderizados nestas telas. Textos não podem conter verbos de ordem
 * ("compre", "venda", "aloque").
 */
export const AvisoCompliance = () => {
  return (
    <div className="aviso-compliance">
      <h3>Aviso Importante</h3>
      <p>
        Esta análise é apenas para fins informativos e educacionais. Os
        cálculos de projeção, IR e IOF seguem as leis vigentes (Lei 11.033/2004
        para IR, Decreto 6.306/2007 para IOF) e as normas do Tesouro Direto.
      </p>
      <ul>
        <li>
          <strong>IR (Imposto de Renda):</strong> Tributação por faixa (22,5% até
          180d, 20% de 181 a 360d, 17,5% de 361 a 720d, 15% acima de 720d). Isentos
          via LCI/LCA/CRI/CRA art. 3º mediante entrada `isento=True`.
        </li>
        <li>
          <strong>IOF:</strong> Incidência sobre resgates até 30 dias (regressivo),
          não incidente a partir de 30 dias. Alíquota: 96% do 1% no 1º dia, diminui
          0,96% ao dia.
        </li>
        <li>
          <strong>Não é recomendação:</strong> Não há emissão de recomendação de
          compra, venda ou alocação de ativos. A escolha e o aporte são de sua
          responsabilidade.
        </li>
      </ul>
    </div>
  );
};