export const decimalParaMoeda = (valor: number | string, moeda: string = "BRL"): string => {
  const d = typeof valor === "number" ? Number(valor) : Number(String(valor).replace(",", "."));
  return d.toFixed(2).replace(".", ",") + " " + moeda;
};

export const decimalParaPorcentagem = (valor: number | string, casas: number = 2): string => {
  const d = typeof valor === "number" ? Number(valor) : Number(String(valor).replace(",", "."));
  return (d * 100).toFixed(casas).replace(".", ",") + " %";
};

export const decimalMoedaLocal = (valor: number): string => {
  return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(valor);
};