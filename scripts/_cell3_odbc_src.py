import sys
from pathlib import Path
sys.path.insert(0, str((Path.cwd().parent / "Utitlities").resolve()))
from fechamento_excel import gravar_fechamento_excel

def read_csv_with_fallback(path, sep=';', dtype=str, nrows=None):
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin1']
    ultimo_erro = None
    for enc in encodings:
        try:
            df = pd.read_csv(path, sep=sep, dtype=dtype, encoding=enc, nrows=nrows, low_memory=False)
            return df, enc
        except UnicodeDecodeError as e:
            ultimo_erro = e
    raise UnicodeDecodeError(
        getattr(ultimo_erro, 'encoding', 'unknown'),
        getattr(ultimo_erro, 'object', b''),
        getattr(ultimo_erro, 'start', 0),
        getattr(ultimo_erro, 'end', 1),
        f'Nao foi possivel ler com encodings {encodings}: {ultimo_erro}'
    )


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def validar_colunas_odbc(df: pd.DataFrame) -> None:
    faltantes = [c for c in COLUNAS_ODBC_OBRIGATORIAS if c not in df.columns]
    if faltantes:
        raise ValueError(
            'Colunas ODBC obrigatorias ausentes: '
            + ', '.join(faltantes)
            + f'\nColunas encontradas: {", ".join(df.columns)}'
        )


def read_odbc_base(path: Path, sheet: str | None = None):
    path = Path(path)
    if path.suffix.lower() in {'.xlsx', '.xls'}:
        df = pd.read_excel(path, sheet_name=sheet if sheet is not None else 0, dtype=str)
        return normalizar_colunas(df), 'xlsx'
    df, enc = read_csv_with_fallback(path)
    return normalizar_colunas(df), enc


base, enc_base = read_odbc_base(BASE_PATH, BASE_SHEET)
validar_colunas_odbc(base)

print(f'Fonte ODBC: {BASE_PATH.name} ({enc_base}) | linhas: {len(base):,}'.replace(',', '.'))
print(f'Colunas ODBC: {len(base.columns)} | layout fechamento: {len(COLUNAS_FECHAMENTO)} colunas')


def filtrar_mes(base_df: pd.DataFrame, mes_referencia: str, campo_data: str) -> pd.DataFrame:
    mes, ano = mes_referencia.split('/')
    mes_int = int(mes)
    ano_int = int(ano)

    if campo_data == 'lancamento':
        serie_data = base_df[campo_data].fillna('').astype(str).str.strip()
        # Excel ODBC costuma vir em ISO (aaaa-mm-dd); CSV em dd/mm/aaaa
        iso_like = serie_data.str.match(r'^\d{4}-\d{2}-\d{2}', na=False).mean() > 0.5
        dt = pd.to_datetime(serie_data, errors='coerce') if iso_like else pd.to_datetime(serie_data, dayfirst=True, errors='coerce')
        filtro = (dt.dt.month == mes_int) & (dt.dt.year == ano_int)
        if not filtro.any():
            m2 = str(mes_int).zfill(2)
            padrao1 = rf'(^|\D){m2}/{ano_int}(\D|$)'
            padrao2 = rf'(^|\D){mes_int}/{ano_int}(\D|$)'
            filtro = serie_data.str.contains(padrao1, regex=True, na=False) | serie_data.str.contains(padrao2, regex=True, na=False)
    elif campo_data == 'ite_pagrec_vencimento':
        serie_data = base_df[campo_data].fillna('').astype(str).str.strip()
        dt = pd.to_datetime(serie_data, errors='coerce')
        filtro = (dt.dt.month == mes_int) & (dt.dt.year == ano_int)
        if not filtro.any():
            m2 = str(mes_int).zfill(2)
            filtro = serie_data.str.startswith(f'{ano_int}-{m2}')
    else:
        raise ValueError("campo_data deve ser 'lancamento' ou 'ite_pagrec_vencimento'.")

    resultado = base_df.loc[filtro].copy().reset_index(drop=True)
    if resultado.empty:
        raise ValueError(f"Nenhum registro encontrado para {mes_referencia} usando {campo_data}.")
    return resultado


def converter_para_fechamento(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work['valor_bruto_num'] = work['valor_bruto'].apply(to_float_br)
    work['valor_plano_num'] = work['valor_plano'].apply(to_float_br)
    work['valor_centro_num'] = work['valor_centro'].apply(to_float_br)

    out = pd.DataFrame(index=work.index)
    out['id'] = (work.index + 1).astype(str).str.zfill(6)

    lvl = work['codcen'].apply(levels_from_codcen)
    out['n1_cod_centro_custo'] = lvl.apply(lambda x: x[0])
    out['n2_cod_centro_custo'] = lvl.apply(lambda x: x[1])
    out['n3_cod_centro_custo'] = lvl.apply(lambda x: x[2])
    out['n4_cod_centro_custo'] = lvl.apply(lambda x: x[3])

    desc_split = work['descen'].apply(split_descen)
    out['n1_centro_custo'] = desc_split.apply(lambda x: x[1])
    out['n2_centro_custo'] = desc_split.apply(lambda x: x[2])
    out['n3_centro_custo'] = desc_split.apply(lambda x: x[3])
    out['n4_centro_custo'] = desc_split.apply(lambda x: x[4])

    out['Segmento'] = out['n1_centro_custo']
    out['n1_CC'] = (out['n1_cod_centro_custo'].fillna('') + ' ' + out['n1_centro_custo'].fillna('')).str.strip()
    out['n2_CC'] = (out['n2_cod_centro_custo'].fillna('') + ' ' + out['n2_centro_custo'].fillna('')).str.strip()
    out['n3_CC'] = (out['n3_cod_centro_custo'].fillna('') + ' ' + out['n3_centro_custo'].fillna('')).str.strip()
    out['n4_CC'] = (out['n4_cod_centro_custo'].fillna('') + ' ' + out['n4_centro_custo'].fillna('')).str.strip()

    out['cod_conta'] = work['codcdc'].fillna('')
    out['conta'] = work['descdc'].fillna('')
    out['cod_conta-descr'] = (out['cod_conta'] + ' ' + out['conta']).str.strip()
    out['filial'] = work['filial'].fillna('')
    out['titulo'] = work['documento'].fillna('')
    out['valor_nf'] = work['valor_bruto_num']
    out['valor_pago'] = work['valor_bruto_num']
    out['valor_conta'] = work['valor_centro_num']
    out['observacao'] = work['observacao'].fillna('')
    out['data_nf'] = work['lancamento'].apply(parse_data_nf)
    out['data_pagamento'] = work['iterea_pagamento'].apply(parse_data_pagamento)
    out['cod_credor_forn_cli_func'] = work['codigo_pessoa'].fillna('')
    out['credor_forn_cli_func'] = work['nome'].fillna('')

    out['Origem'] = np.where(
        out['cod_conta'].str.startswith(('4.', '5.')),
        'Entrada (Origem)',
        'Saida (Aplicacoes)'
    )
    out['Sistema'] = 'SAGI'
    out['Dados auxiliares'] = work['nota'].fillna('')
    out['Valor Oficial'] = work['valor_plano_num']
    out['DE-PARA1'] = ''
    out['DE-PARA2'] = ''
    out['CUSTEIO VARIÁVEL'] = ''

    for c in COLUNAS_FECHAMENTO:
        if c not in out.columns:
            out[c] = ''

    result = out[COLUNAS_FECHAMENTO].copy()
    for c in COLUNAS_NUMERICAS_SAIDA:
        result[c] = pd.to_numeric(result[c], errors='coerce')
    for c in COLUNAS_DATA_SAIDA:
        result[c] = pd.to_datetime(result[c], errors='coerce')

    text_cols = [
        c for c in COLUNAS_FECHAMENTO
        if c not in COLUNAS_NUMERICAS_SAIDA and c not in COLUNAS_DATA_SAIDA
    ]
    result[text_cols] = result[text_cols].fillna('')
    return result


def validar_totais(df_origem: pd.DataFrame, df_saida: pd.DataFrame, rotulo: str = '') -> None:
    bruto = df_origem['valor_bruto'].apply(to_float_br).sum()
    plano = df_origem['valor_plano'].apply(to_float_br).sum()
    centro = df_origem['valor_centro'].apply(to_float_br).sum()
    pago = pd.to_numeric(df_saida['valor_pago'], errors='coerce').sum()
    conta = pd.to_numeric(df_saida['valor_conta'], errors='coerce').sum()
    oficial = pd.to_numeric(df_saida['Valor Oficial'], errors='coerce').sum()
    prefixo = f'{rotulo}: ' if rotulo else ''
    print(f"{prefixo}ODBC valor_bruto={bruto:,.2f} | saida valor_pago={pago:,.2f}")
    print(f"{prefixo}ODBC valor_plano={plano:,.2f} | saida Valor Oficial={oficial:,.2f}")
    print(f"{prefixo}ODBC valor_centro={centro:,.2f} | saida valor_conta={conta:,.2f}")


def salvar_fechamento(df_out: pd.DataFrame, caminho: Path) -> None:
    gravar_fechamento_excel(df_out, caminho, sheet_name='Fechamento')

saidas_por_mes = {}
bases_por_mes = {}
arquivos_gerados: list[Path] = []

if MESES_REFERENCIA:
    lotes = [(mes_ref, filtrar_mes(base, mes_ref, CAMPO_DATA_FILTRO)) for mes_ref in MESES_REFERENCIA]
else:
    lotes = [(None, base.copy().reset_index(drop=True))]

for mes_ref, df_lote in lotes:
    out = converter_para_fechamento(df_lote)

    if mes_ref:
        mes, ano = mes_ref.split('/')
        chave = mes_ref
        caminho = OUT_DIR / f'{PREFIXO_SAIDA}_{ano}_{mes}.xlsx'
    else:
        chave = '__todos__'
        caminho = OUT_DIR / f'{BASE_PATH.stem}_fechamento.xlsx'

    saidas_por_mes[chave] = out
    bases_por_mes[chave] = df_lote
    salvar_fechamento(out, caminho)
    arquivos_gerados.append(caminho)
    validar_totais(df_lote, out, mes_ref or 'Todos')
    print(f'{(mes_ref or "Todos")}: {len(out):,} registros -> {caminho.name}'.replace(',', '.'))

if MESES_REFERENCIA and len(MESES_REFERENCIA) > 1:
    consolidado = pd.concat([saidas_por_mes[m] for m in MESES_REFERENCIA], ignore_index=True)
    base_consolidada = pd.concat([bases_por_mes[m] for m in MESES_REFERENCIA], ignore_index=True)
    ano_cons = MESES_REFERENCIA[0].split('/')[1]
    caminho_cons = OUT_DIR / f'{PREFIXO_SAIDA}_COMPLETO_{ano_cons}.xlsx'
    salvar_fechamento(consolidado, caminho_cons)
    arquivos_gerados.append(caminho_cons)
    validar_totais(base_consolidada, consolidado, 'Consolidado')
    print(f'Consolidado: {len(consolidado):,} registros -> {caminho_cons.name}'.replace(',', '.'))
    out = consolidado
else:
    out = next(iter(saidas_por_mes.values()))

display(out.head(5))

# --- Checagem de layout (mesma celula: evita NameError se rodar so a ultima) ---
faltantes = [c for c in COLUNAS_FECHAMENTO if c not in out.columns]
extras = [c for c in out.columns if c not in COLUNAS_FECHAMENTO]
print('Colunas faltantes:', faltantes)
print('Colunas extras:', extras)
print('Quantidade de colunas esperadas:', len(COLUNAS_FECHAMENTO))
print('Quantidade de colunas na saida:', len(out.columns))
print()
if arquivos_gerados:
    print('Arquivo(s) gerado(s):')
    for caminho in arquivos_gerados:
        print(f'  - {caminho.resolve()}')
else:
    print('Nenhum arquivo gerado.')
