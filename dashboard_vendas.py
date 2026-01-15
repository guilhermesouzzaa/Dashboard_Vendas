import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
st.markdown("<h1 style='text-align: center;'>Dashboard de Vendas</h1>", unsafe_allow_html=True)

# =============================
# CARREGAMENTO DE DADOS
# =============================
@st.cache_data
def load_data():
    df = pd.read_csv("relatorio_final.csv")
    df["data_venda"] = pd.to_datetime(df["data_venda"])
    df["faturamento"] = df["quantidade"] * df["preco_unitario"]
    df["lucro"] = df["faturamento"] - df["custo"]
    df["mes"] = df["data_venda"].dt.to_period("M").astype(str)
    df["dia"] = df["data_venda"].dt.date
    return df

dados = load_data()

# =============================
# FUNÇÕES AUXILIARES
# =============================
def calc_var(atual, anterior):
    if anterior == 0:
        return None
    return (atual - anterior) / anterior * 100

def kpi_box(titulo, valor, variacao=None, formato="R$ {:,.2f}", unidade=""):
    st.markdown(f"**{titulo}**")
    st.markdown(f"{formato.format(valor)} {unidade}")
    if variacao is not None:
        cor = "green" if variacao >= 0 else "red"
        sinal = "+" if variacao >= 0 else ""
        st.markdown(
                "<div style='font-size:14px; color:gray; margin-top:2px;'>Mês anterior</div>",
                unsafe_allow_html=True
        )
        st.markdown(
            f"<span style='color:{cor}; font-weight:bold;'>{sinal}{variacao:.2f}%</span>",
            unsafe_allow_html=True
        )

# =============================
# TABS
# =============================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Visão Geral", "Vendedores & Equipes", "Produtos, Categorias & Serviços", "Análise Geográfica", 'Previsão de Faturamento'])

# =============================
# ABA VISÃO GERAL
# =============================
with tab1:

    # ===== FILTRO DE MÊS =====
    meses = ["Todos"] + sorted(dados["mes"].unique())
    col_filtro, _ = st.columns([1, 4])
    with col_filtro:
        mes_selecionado = st.selectbox("Mês", meses)

    # ===== FILTRAGEM DE DADOS =====
    if mes_selecionado == "Todos":
        df_atual = dados.copy()
    else:
        df_atual = dados[dados["mes"] == mes_selecionado]

    # ===== CÁLCULO DAS MÉTRICAS =====
    faturamento = df_atual["faturamento"].sum()
    lucro = df_atual["lucro"].sum()
    quantidade = df_atual["quantidade"].sum()
    ticket = faturamento / quantidade if quantidade > 0 else 0
    margem = (lucro / faturamento * 100) if faturamento > 0 else 0

    custo = df_atual["custo"].sum()
    clientes = df_atual["cliente"].nunique()
    venda_cliente = faturamento / clientes if clientes > 0 else 0

    # ===== VARIAÇÃO MÊS ANTERIOR =====
    if mes_selecionado != "Todos":
        mes_dt = pd.to_datetime(mes_selecionado + "-01")
        mes_ant = (mes_dt - pd.DateOffset(months=1)).strftime("%Y-%m")
        df_ant = dados[dados["mes"] == mes_ant]

        var_fat = calc_var(faturamento, df_ant["faturamento"].sum())
        var_lucro = calc_var(lucro, df_ant["lucro"].sum())
        var_qtd = calc_var(quantidade, df_ant["quantidade"].sum())

        ticket_ant = (df_ant["faturamento"].sum() / df_ant["quantidade"].sum()) if df_ant["quantidade"].sum() > 0 else 0
        margem_ant = (df_ant["lucro"].sum() / df_ant["faturamento"].sum() * 100) if df_ant["faturamento"].sum() > 0 else 0
        var_ticket = calc_var(ticket, ticket_ant)
        var_margem = calc_var(margem, margem_ant)

        var_custo = calc_var(custo, df_ant["custo"].sum())
        var_clientes = calc_var(clientes, df_ant["cliente"].nunique())
        venda_cliente_ant = (df_ant["faturamento"].sum() / df_ant["cliente"].nunique()) if df_ant["cliente"].nunique() > 0 else 0
        var_venda_cliente = calc_var(venda_cliente, venda_cliente_ant)
    else:
        var_fat = var_lucro = var_qtd = var_ticket = var_margem = None
        var_custo = var_clientes = var_venda_cliente = None

    # ===== KPIs TOPO =====
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: kpi_box("Faturamento Total", faturamento, var_fat)
    with col2: kpi_box("Lucro Total", lucro, var_lucro)
    with col3: kpi_box("Quantidade de Vendas", quantidade, var_qtd, "{:,.0f}", "Un")
    with col4: kpi_box("Ticket Médio", ticket, var_ticket)
    with col5: kpi_box("Margem de Lucro", margem, var_margem, "{:.2f}", "%")

    st.divider()

    # ===== KPIs LATERAIS + GRÁFICO =====
    col_kpi, col_graf = st.columns([1.5, 4])

    with col_kpi:
        kpi_box("Custo Total", custo, var_custo)
        st.markdown("---")
        kpi_box("Clientes Ativos", clientes, var_clientes, "{:,.0f}")
        st.markdown("---")
        kpi_box("Venda Média por Cliente", venda_cliente, var_venda_cliente)

    with col_graf:
        if mes_selecionado == "Todos":
            df_plot = dados.groupby("mes", as_index=False)["faturamento"].sum()
            fig = px.line(df_plot, x="mes", y="faturamento", markers=True, title="Faturamento Mensal")
            fig.update_layout(template="plotly_dark", yaxis_title="R$", height=500)
        else:
            df_plot = df_atual.groupby("dia", as_index=False)["faturamento"].sum()
            fig = px.line(df_plot, x="dia", y="faturamento", markers=True, title=f"Faturamento Diário - {mes_selecionado}")
            fig.update_xaxes(tickformat="%d/%m")
            fig.update_layout(template="plotly_dark", yaxis_title="R$", height=650)

        st.plotly_chart(fig, use_container_width=True)

# =============================
# ABA Vendedores & Equipes
# =============================
with tab2:
    import pandas as pd
    import streamlit as st

    # =========================
    # Funções auxiliares
    # =========================
    def calc_var(atual, anterior):
        if anterior in (0, None):
            return None
        return ((atual - anterior) / anterior) * 100


    def texto_kpi(valor, variacao=None, formato="R$ {:,.2f}", unidade=""):
        try:
            texto_valor = formato.format(float(valor))
        except (TypeError, ValueError):
            texto_valor = "–"

        html = f"<div style='font-size:16px;'>{texto_valor} {unidade}</div>"

        if variacao is not None:
            cor = "green" if variacao >= 0 else "red"
            sinal = "+" if variacao >= 0 else ""
            html += "<div style='font-size:14px; color:gray; margin-top:4px;'>Mês anterior</div>"
            html += (
                f"<div style='font-size:15px; color:{cor}; font-weight:bold;'>"
                f"{sinal}{variacao:.2f}%</div>"
            )

        return html


    def kpi_box(titulo, conteudo):
        st.markdown(f"**{titulo}**")
        st.markdown(conteudo, unsafe_allow_html=True)

    # =========================
    # Filtros
    # =========================
    vendedores = sorted(dados["vendedor"].unique())
    meses = sorted(dados["mes"].unique())
    meses_disponiveis = ["Todos"] + meses

    col_vend, col_mes, _ = st.columns([1, 1, 2])

    with col_vend:
        vend = st.selectbox("Vendedor", vendedores)

    with col_mes:
        mes_sel = st.selectbox("Mês", meses_disponiveis, key="filtro_mesv")

    # =========================
    # Dados filtrados
    # =========================
    df_ven = dados[dados["vendedor"] == vend]

    if mes_sel != "Todos":
        df_ven = df_ven[df_ven["mes"] == mes_sel]

    # =========================
    # KPIs atuais
    # =========================
    fat = df_ven["faturamento"].sum()
    lucro = df_ven["lucro"].sum()
    qtd = df_ven["quantidade"].sum()
    clientes = df_ven["cliente"].nunique()

    media = fat / len(df_ven) if len(df_ven) > 0 else 0
    margem = (lucro / fat * 100) if fat > 0 else 0

    # =========================
    # KPIs mês anterior
    # =========================
    var_fat = var_lucro = var_qtd = var_media = var_margem = var_clientes = None

    if mes_sel != "Todos":
        meses_vendedor = sorted(
            dados[dados["vendedor"] == vend]["mes"].unique()
        )

        if mes_sel in meses_vendedor:
            idx = meses_vendedor.index(mes_sel)

            if idx > 0:
                mes_ant = meses_vendedor[idx - 1]
                df_ant = dados[
                    (dados["vendedor"] == vend) &
                    (dados["mes"] == mes_ant)
                ]

                fat_ant = df_ant["faturamento"].sum()
                lucro_ant = df_ant["lucro"].sum()
                qtd_ant = df_ant["quantidade"].sum()
                clientes_ant = df_ant["cliente"].nunique()

                media_ant = fat_ant / len(df_ant) if len(df_ant) > 0 else 0
                margem_ant = (lucro_ant / fat_ant * 100) if fat_ant > 0 else 0

                var_fat = calc_var(fat, fat_ant)
                var_lucro = calc_var(lucro, lucro_ant)
                var_qtd = calc_var(qtd, qtd_ant)
                var_media = calc_var(media, media_ant)
                var_margem = calc_var(margem, margem_ant)
                var_clientes = calc_var(clientes, clientes_ant)

    # =========================
    # Exibição dos KPIs
    # =========================
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        kpi_box("Faturamento Total", texto_kpi(fat, var_fat))

    with col2:
        kpi_box("Margem de Lucro", texto_kpi(margem, var_margem, "{:.2f}", "%"))

    with col3:
        kpi_box("Lucro do Vendedor", texto_kpi(lucro, var_lucro))

    with col4:
        kpi_box("Quantidade de Vendas", texto_kpi(qtd, var_qtd, "{:,.0f}", "Un"))

    with col5:
        kpi_box("Média da Venda", texto_kpi(media, var_media))

    with col6:
        kpi_box("Total de Clientes", texto_kpi(clientes, var_clientes, "{:,.0f}", "Un"))


    st.divider()

    vend = dados["vendedor"].unique()
    meses_fat = ["Todos"] + sorted(dados["mes"].unique())
    mul_filtro,_,filtro_meses, _ = st.columns([1,1,1,1])
    with mul_filtro:
        vends = st.multiselect("Vendedor", vend, default=["Sarah"])
        if vends:
            df_filtrado = dados[dados["vendedor"].isin(vends)]
        else:
            df_filtrado = dados[dados["vendedor"] == 'Sarah']

    with filtro_meses:
        mes_sel = st.selectbox("Mês", meses_disponiveis, key="filtro_bar")
    if mes_sel != "Todos":
        df_bar = dados[dados['mes'] == mes_sel]
    else:
        df_bar = dados.copy()
    col1, col2 = st.columns(2)
    with col1: 
        df_agg = (
        df_filtrado
        .groupby(["mes", "vendedor"], as_index=False)["faturamento"]
        .sum()
        )
        fig = px.line(
        df_agg,
        x="mes",
        y="faturamento",
        color="vendedor",  
        markers=False
        )

        fig.update_layout(
            title="Faturamento mensal por vendedor",
            xaxis_title="Mês",
            yaxis_title="Faturamento",
            legend_title="Vendedor"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        df_agg = df_bar.groupby(['vendedor'], as_index=False)['faturamento'].sum()
        long_df = px.data.medals_long()

            # Gráfico de barras
        figb = px.bar(
            df_agg,
            x="vendedor",
            y="faturamento",
            title="Faturamento por vendedor",
            text_auto=".2f"
        )

        # Formatação monetária
        figb.update_traces(
            texttemplate="R$ %{y:,.2f}",
            hovertemplate="Vendedor: %{x}<br>Faturamento: R$ %{y:,.2f}"
        )

        figb.update_layout(
            xaxis_title="Vendedor",
            yaxis_title="Faturamento (R$)",
            showlegend=False
        )

        st.plotly_chart(figb, use_container_width=True)

    meses_e = ["Todos"] + sorted(dados["mes"].unique())
    _,_,filtro, _ = st.columns([1,1,1,1])
    with filtro:
        mes_sel = st.selectbox("Mês", meses_e, key="filtro_mes")


    if mes_sel == "Todos":
        df_new = dados.copy()
    else:
        df_new = dados[dados["mes"] == mes_sel]

    col1, col2 = st.columns(2)
    with col1:
        df_agg = (
        dados.groupby(["mes", "equipe"], as_index=False)["faturamento"]
        .sum()
        )    
        fig = px.line(
        df_agg,
        x="mes",
        y="faturamento",
        color="equipe",  
        markers=False
        )

        fig.update_layout(
            title="Faturamento mensal por equipes",
            xaxis_title="Mês",
            yaxis_title="Faturamento",
            legend_title="equipe"
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        df_equipe = df_new.groupby(['equipe'], as_index=False)['faturamento'].sum()
        equi_df = px.data.medals_long()

        figb = px.bar(
        df_equipe,
        x="equipe",
        y="faturamento",
        title="Faturamento total por equipe",
        text_auto=".2f"
    )

        # Formatação em moeda
        figb.update_traces(
            texttemplate="R$ %{y:,.2f}",
            hovertemplate="Equipe: %{x}<br>Faturamento: R$ %{y:,.2f}"

        )
        figb.update_layout(
            xaxis_title="Equipe",
            yaxis_title="Faturamento (R$)",
            showlegend=False
        )

        st.plotly_chart(figb, use_container_width=True)

#=======================================================
#TAB03
#=======================================================
with tab3:
    import streamlit as st
    import pandas as pd

    # =========================
    # Funções auxiliares
    # =========================
    def calc_var(atual, anterior):
        if anterior in (0, None):
            return None
        return ((atual - anterior) / anterior) * 100


    def texto_kpi(valor, variacao=None, formato="R$ {:,.2f}", unidade=""):
        try:
            texto_valor = formato.format(float(valor))
        except (TypeError, ValueError):
            texto_valor = "–"

        html = f"<div style='font-size:16px;'>{texto_valor} {unidade}</div>"

        if variacao is not None:
            cor = "green" if variacao >= 0 else "red"
            sinal = "+" if variacao >= 0 else ""
            html += "<div style='font-size:14px; color:gray; margin-top:4px;'>Mês anterior</div>"
            html += (
                f"<div style='font-size:15px; color:{cor}; font-weight:bold;'>"
                f"{sinal}{variacao:.2f}%</div>"
            )

        return html


    def kpi_box(titulo, conteudo):
        st.markdown(f"**{titulo}**")
        st.markdown(conteudo, unsafe_allow_html=True)

    # =========================
    # Filtros
    # =========================
    meses = ["Todos"] + sorted(dados["mes"].unique())
    categorias = ["Todas"] + sorted(dados["categoria_servico"].unique())

    col_mes, col_cat, col_serv = st.columns(3)

    with col_mes:
        mes_sel = st.selectbox("Mês", meses, key="filtro_mes_tab3")

    with col_cat:
        categoria_sel = st.selectbox("Categoria", categorias, key="filtro_cat_tab3")

    # Serviços dependem da categoria
    if categoria_sel == "Todas":
        servicos = ["Todos"] + sorted(dados["servico"].unique())
    else:
        servicos = ["Todos"] + sorted(
            dados[dados["categoria_servico"] == categoria_sel]["servico"].unique()
        )

    with col_serv:
        servico_sel = st.selectbox("Serviço", servicos, key="filtro_serv_tab3")

    # =========================
    # Dados atuais
    # =========================
    df_atual = dados.copy()

    if mes_sel != "Todos":
        df_atual = df_atual[df_atual["mes"] == mes_sel]

    if categoria_sel != "Todas":
        df_atual = df_atual[df_atual["categoria_servico"] == categoria_sel]

    if servico_sel != "Todos":
        df_atual = df_atual[df_atual["servico"] == servico_sel]

    faturamento = df_atual["faturamento"].sum()
    lucro = df_atual["lucro"].sum()
    quantidade = df_atual["quantidade"].sum()

    ticket = faturamento / quantidade if quantidade > 0 else 0
    margem = (lucro / faturamento * 100) if faturamento > 0 else 0
    # =========================

    # Dados mês anterior
    # =========================
    var_fat = var_lucro = var_qtd = var_ticket = var_margem = None

    if mes_sel != "Todos":
        meses_ord = sorted(dados["mes"].unique())

        if mes_sel in meses_ord:
            idx = meses_ord.index(mes_sel)

            if idx > 0:
                mes_ant = meses_ord[idx - 1]

                df_ant = dados[dados["mes"] == mes_ant]

                if categoria_sel != "Todas":
                    df_ant = df_ant[df_ant["categoria_servico"] == categoria_sel]

                if servico_sel != "Todos":
                    df_ant = df_ant[df_ant["servico"] == servico_sel]

                faturamento_ant = df_ant["faturamento"].sum()
                lucro_ant = df_ant["lucro"].sum()
                quantidade_ant = df_ant["quantidade"].sum()

                ticket_ant = faturamento_ant / quantidade_ant if quantidade_ant > 0 else 0
                margem_ant = (lucro_ant / faturamento_ant * 100) if faturamento_ant > 0 else 0

                var_fat = calc_var(faturamento, faturamento_ant)
                var_lucro = calc_var(lucro, lucro_ant)
                var_qtd = calc_var(quantidade, quantidade_ant)
                var_ticket = calc_var(ticket, ticket_ant)
                var_margem = calc_var(margem, margem_ant)

    # =========================
    # Exibição dos KPIs
    # =========================
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        kpi_box("Faturamento Total", texto_kpi(faturamento, var_fat))

    with col2:
        kpi_box("Lucro Total", texto_kpi(lucro, var_lucro))

    with col3:
        kpi_box("Quantidade Vendida", texto_kpi(quantidade, var_qtd, "{:,.0f}", "Un"))

    with col4:
        kpi_box("Ticket Médio", texto_kpi(ticket, var_ticket))

    with col5:
        kpi_box("Margem de Lucro", texto_kpi(margem, var_margem, "{:.2f}", "%"))

    st.divider()

    # =========================
    # Lista de meses
    # =========================
    mesest3 = ["Todos"] + sorted(dados["mes"].unique())

    # =========================
    # Filtro de mês
    # =========================
    _,col_mesb, _ = st.columns([2,1,1])

    with col_mesb:
        mes_sel_bar = st.selectbox("Mês", mesest3, key="filtro_mes_tab_bar")

    # DataFrame filtrado pelo mês
    if mes_sel_bar != "Todos":
        df_bar = dados[dados["mes"] == mes_sel_bar]
    else:
        df_bar = dados.copy()

    col1g, col2g = st.columns(2)
    with col1g:
        df_agg = (
        dados.groupby(["mes", "categoria_servico"], as_index=False)["faturamento"]
        .sum()
        )    
        fig = px.line(
        df_agg,
        x="mes",
        y="faturamento",
        color="categoria_servico", 
        markers=False
        )

        fig.update_layout(
            title="Faturamento mensal por categoria_servico",
            xaxis_title="Mês",
            yaxis_title="Faturamento",
            legend_title="categoria_servico"
        )
        st.plotly_chart(fig, use_container_width=True)
    
        df_equipe = df_new.groupby(['equipe'], as_index=False)['faturamento'].sum()
        equi_df = px.data.medals_long()

    with col2g:

        df_equipe = df_bar.groupby(['categoria_servico'], as_index=False)['faturamento'].sum()
        equi_df = px.data.medals_long()

        figb = px.bar(
        df_equipe,
        x="categoria_servico",
        y="faturamento",
        title="Faturamento total por equipe",
        text_auto=".2f"
    )

        # Formatação em moeda
        figb.update_traces(
            texttemplate="R$ %{y:,.2f}",
            hovertemplate="Categoria_servico: %{x}<br>Faturamento: R$ %{y:,.2f}"

        )
        figb.update_layout(
            xaxis_title="Categoria de Serviço",
            yaxis_title="Faturamento (R$)",
            showlegend=False
        )

        st.plotly_chart(figb, use_container_width=True)

    lista_meses = ["Todos"] + sorted(dados["mes"].unique())
    lista_servicos = sorted(dados["servico"].unique())

    # =========================
    # Filtros
    # =========================
    col_serv, _, col_mes, _ = st.columns([1, 2, 1, 1])

    # 🔹 Filtro de serviço (para o gráfico de linha)
    with col_serv:
        servicos_sel = st.multiselect(
            "Serviço",
            lista_servicos,
            default=["Backup em Nuvem"],
            key="mult2"
        )

        if servicos_sel:
            df_servico = dados[dados["servico"].isin(servicos_sel)]
        else:
            df_servico = dados[dados["servico"] == "Backup em Nuvem"]

    # 🔹 Filtro de mês (para o gráfico de barras)
    with col_mes:
        mes_sel_l3 = st.selectbox("Mês", lista_meses, key="filtro_mes_tab_bars")

        if mes_sel_l3 != "Todos":
            df_mes = dados[dados["mes"] == mes_sel_l3]
        else:
            df_mes = dados.copy()

    # =========================
    # Layout dos gráficos
    # =========================
    colgr1, colgr2 = st.columns(2)

    # =========================
    # GRÁFICO 1 — Linha (por serviço)
    # =========================
    with colgr1:
        df_line = (
            df_servico
            .groupby(["mes", "servico"], as_index=False)["faturamento"]
            .sum()
        )

        fig_line = px.line(
            df_line,
            x="mes",
            y="faturamento",
            color="servico",
            markers=False,
            title="Faturamento mensal por serviço"
        )

        fig_line.update_layout(
            xaxis_title="Mês",
            yaxis_title="Faturamento",
            legend_title="Serviço"
        )

        st.plotly_chart(fig_line, use_container_width=True)

    # =========================
    # GRÁFICO 2 — Barras (por mês)
    # =========================
    with colgr2:
        df_bar = (
            df_mes
            .groupby("servico", as_index=False)["faturamento"]
            .sum()
        )

        fig_bar = px.bar(
            df_bar,
            x="servico",
            y="faturamento",
            title="Faturamento por Serviço",
            text_auto=".2f"
        )

        fig_bar.update_traces(
            texttemplate="R$ %{y:,.2f}",
            hovertemplate="Serviço: %{x}<br>Faturamento: R$ %{y:,.2f}"
        )

        fig_bar.update_layout(
            xaxis_title="Serviço",
            yaxis_title="Faturamento (R$)",
            showlegend=False
        )

        st.plotly_chart(fig_bar, use_container_width=True)

#===================================================================================
#=====================TAB4==========================================================
#===================================================================================

import json
import requests
import plotly.express as px

with tab4:
    # ===== FILTROS =====
    meses = ["Todos"] + sorted(dados["mes"].unique())
    col1, col2 = st.columns(2)
    with col1:
        mes_geo = st.selectbox("Selecione o mês:", meses)
    with col2:
        metrica_geo = st.selectbox(
            "Escolha a métrica do mapa:",
            ["faturamento", "lucro", "custo"]
        )

    # ===== FILTRAGEM =====
    if mes_geo == "Todos":
        df = dados.copy()
    else:
        df = dados[dados["mes"] == mes_geo]

    # ===== AGRUPAMENTO POR ESTADO =====
    mapa = df.groupby("estado", as_index=False).agg(
        faturamento=("faturamento", "sum"),
        lucro=("lucro", "sum"),
        custo=("custo", "sum")
    )

    # ===== CARREGAR GEOJSON DOS ESTADOS DO BRASIL =====
    url_geojson = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geojson = json.loads(requests.get(url_geojson).text)

    # ===== MAPA =====
    fig = px.choropleth_mapbox(
        mapa,
        geojson=geojson,
        locations="estado",
        featureidkey="properties.sigla",
        color=metrica_geo,
        hover_name="estado",
        hover_data={
            "faturamento": ":,.2f",
            "lucro": ":,.2f",
            "custo": ":,.2f"
        },
        mapbox_style="carto-positron",
        center={"lat": -14.2350, "lon": -51.9253},
        zoom=3.0,
        opacity=0.7,
        color_continuous_scale="Blues"
    )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

# =============================
# TAB 5 - PREVISÃO DE FATURAMENTO MENSAL
# =============================
from prophet import Prophet

with tab5:

    st.subheader("🔮 Previsão de Faturamento Mensal (Prophet)")

    # ----------------------------
    # Preparação dos dados - AGREGAR POR MÊS
    # ----------------------------
    # Usando resample para evitar problemas de coluna
    df_temp = dados.set_index("data_venda")
    df_prophet = df_temp["faturamento"].resample("M").sum().reset_index()
    df_prophet = df_prophet.rename(columns={"data_venda": "ds", "faturamento": "y"})

    # ----------------------------
    # Controles do usuário
    # ----------------------------
    col1, col2, _ = st.columns([1, 1, 2])

    with col1:
        horizonte = st.number_input(
            "Horizonte da previsão (meses)",
            min_value=1,
            max_value=12,
            value=3,
            step=1
        )

    with col2:
        st.write("")
        st.write("")
        processar = st.button("Gerar previsão")

    # ----------------------------
    # Treinamento do modelo Prophet (cache)
    # ----------------------------
    @st.cache_resource
    def treinar_modelo(df):
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        model.fit(df)
        return model

    if processar:
        with st.spinner("Treinando modelo e gerando previsão..."):
            model = treinar_modelo(df_prophet)

            # Criar dataframe futuro (freq mensal)
            future = model.make_future_dataframe(periods=horizonte, freq='M')
            forecast = model.predict(future)

        # ----------------------------
        # Gráfico da previsão
        # ----------------------------
        st.markdown("### 📈 Histórico + Previsão (Mensal)")

        import plotly.express as px

        fig = px.line(
            forecast,
            x="ds",
            y="yhat",
            title="Previsão de Faturamento Mensal",
            labels={"ds": "Mês", "yhat": "Faturamento Previsto"}
        )

        # Histórico real
        fig.add_scatter(
            x=df_prophet["ds"],
            y=df_prophet["y"],
            mode="lines+markers",
            name="Histórico",
            line=dict(color="white")
        )

        # Intervalo de confiança
        fig.add_scatter(
            x=forecast["ds"],
            y=forecast["yhat_upper"],
            mode="lines",
            line=dict(width=0),
            showlegend=False
        )

        fig.add_scatter(
            x=forecast["ds"],
            y=forecast["yhat_lower"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(0, 123, 255, 0.2)",
            line=dict(width=0),
            name="Intervalo de Confiança"
        )

        fig.update_layout(
            template="plotly_dark",
            yaxis_title="R$",
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

        # ----------------------------
        # Tabela com valores previstos
        # ----------------------------
        st.markdown("### 📅 Valores previstos")

        previsao_futura = (
            forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
            .tail(horizonte)
            .rename(columns={
                "ds": "Mês",
                "yhat": "Faturamento Previsto",
                "yhat_lower": "Limite Inferior",
                "yhat_upper": "Limite Superior"
            })
        )

        st.dataframe(previsao_futura)



