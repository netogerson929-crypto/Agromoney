"""
AGRO MONEY — Oportunidade para quem faz o Brasil crescer.
=========================================================

Aplicativo (protótipo funcional) que conecta:
  • pequenos produtores e agricultores familiares
  • pessoas comuns, empresas, restaurantes e comércios
  • ONGs e cooperativas
  • comunidades indígenas (área exclusiva, com venda autorizada pela comunidade)
  • agrônomos e técnicos

Funções principais:
  • Mercado direto (ofertas de produtores + demandas de compradores)
  • Aluguel de máquinas entre produtores
  • Terras e parcerias (aluguel de áreas paradas ou divisão de lucro)
  • Povos & Territórios (produtos, cultura e parcerias justas)
  • Agrônomos especialistas
  • Assistente Agro (IA demonstrativa) + modo de leitura em voz
  • Acessibilidade: ouvir tela, alto contraste, letras grandes

COMO RODAR
----------
1) Instale o Python 3.10 ou mais novo.
2) No terminal:      pip install flet
   (opcional, voz no computador):  pip install pyttsx3
3) Rode:             python agro_money.py

No celular:
   • Instale o app "Flet" (Play Store / App Store) e rode:  flet run --android agro_money.py
   • Para gerar o APK: renomeie para main.py e rode:  flet build apk

CONTAS DE TESTE (senha de todas: 123456)
   produtor · comprador · restaurante · ong · indigena · agronomo

Todos os dados são fictícios e ficam só na memória (nenhuma transação real).
"""

import threading
import unicodedata
import uuid
from datetime import datetime

import flet as ft


# =====================================================================
# CORES (verde e branco) — tema normal e tema de alto contraste
# =====================================================================

TEMA_NORMAL = {
    "primaria": "#1B5E20",
    "primaria2": "#2E7D32",
    "clara": "#E8F5E9",
    "destaque": "#C8E6C9",
    "fundo": "#F3F7F0",
    "card": "#FFFFFF",
    "texto": "#14261A",
    "suave": "#46594A",
    "borda": "#CFE0CA",
    "sobre_primaria": "#FFFFFF",
    "alerta": "#7A4A00",
    "alerta_fundo": "#FFF4D6",
    "erro": "#B3261E",
    "erro_fundo": "#FDECEA",
    "ok_fundo": "#E3F4E1",
    "indigena": "#6D4219",
    "indigena_fundo": "#FBF1E4",
    "borda_w": 1,
}

TEMA_CONTRASTE = {
    "primaria": "#003D00",
    "primaria2": "#003D00",
    "clara": "#FFFFFF",
    "destaque": "#FFFFFF",
    "fundo": "#FFFFFF",
    "card": "#FFFFFF",
    "texto": "#000000",
    "suave": "#000000",
    "borda": "#000000",
    "sobre_primaria": "#FFFFFF",
    "alerta": "#000000",
    "alerta_fundo": "#FFFFFF",
    "erro": "#8B0000",
    "erro_fundo": "#FFFFFF",
    "ok_fundo": "#FFFFFF",
    "indigena": "#000000",
    "indigena_fundo": "#FFFFFF",
    "borda_w": 2,
}


# =====================================================================
# TIPOS DE CONTA
# =====================================================================

PERFIS = {
    "produtor": {
        "nome": "Produtor rural",
        "emoji": "👨‍🌾",
        "desc": "Agricultor familiar, pequeno produtor ou criador",
        "doc": "CPF",
    },
    "comprador": {
        "nome": "Pessoa comum",
        "emoji": "🧑",
        "desc": "Quero comprar direto de quem produz",
        "doc": "CPF",
    },
    "empresa": {
        "nome": "Empresa / Restaurante",
        "emoji": "🏪",
        "desc": "Mercados, restaurantes, comércios e indústrias",
        "doc": "CNPJ",
    },
    "ong": {
        "nome": "ONG / Cooperativa",
        "emoji": "🤝",
        "desc": "Associações, cooperativas e projetos sociais",
        "doc": "CNPJ",
    },
    "indigena": {
        "nome": "Comunidade indígena",
        "emoji": "🪶",
        "desc": "Povos, aldeias e associações indígenas",
        "doc": "CPF ou CNPJ",
    },
    "agronomo": {
        "nome": "Agrônomo / Técnico",
        "emoji": "👩‍🔬",
        "desc": "Especialistas que ajudam no campo",
        "doc": "CPF",
    },
}

CATEGORIAS = ["Frutas", "Verduras", "Raízes", "Grãos", "Mel e derivados", "Laticínios", "Ovos e carnes"]
UNIDADES = ["kg", "unidade", "dúzia", "maço", "litro", "saca"]


# =====================================================================
# FUNÇÕES DE APOIO (validação, formatação, texto)
# =====================================================================

def so_digitos(texto):
    return "".join(ch for ch in (texto or "") if ch.isdigit())


def sem_acento(texto):
    texto = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")


def cpf_valido(cpf):
    cpf = so_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11 % 10
        if digito != int(cpf[tamanho]):
            return False
    return True


def cnpj_valido(cnpj):
    cnpj = so_digitos(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, pos in ((pesos1, 12), (pesos2, 13)):
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(pos))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(cnpj[pos]):
            return False
    return True


def para_numero(texto):
    """Aceita '3,50', '3.50', 'R$ 1.200,00'. Retorna float ou None."""
    t = (texto or "").replace("R$", "").replace(" ", "").strip()
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def brl(valor):
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def agora():
    return datetime.now().strftime("%d/%m %H:%M")


def novo_id():
    return uuid.uuid4().hex[:8]


def falar_em_voz(texto):
    """Lê o texto em voz alta (computador, com pyttsx3). Retorna False se não houver voz."""
    try:
        import pyttsx3  # opcional
    except Exception:
        return False

    def tarefa():
        try:
            motor = pyttsx3.init()
            motor.setProperty("rate", 165)
            motor.say(texto)
            motor.runAndWait()
        except Exception:
            pass

    threading.Thread(target=tarefa, daemon=True).start()
    return True


# =====================================================================
# ASSISTENTE AGRO (IA demonstrativa, funciona sem internet)
# Para usar uma IA real, troque o conteúdo da função responder_ia().
# =====================================================================

BASE_IA = [
    (["praga", "lagarta", "pulgao", "inseto", "formiga", "bicho", "fungo", "doenca", "mancha", "ferrugem"],
     "Para pragas e doenças: 1) Olhe as folhas por baixo, de manhã cedo. 2) Tire e queime as partes muito "
     "atacadas. 3) Use primeiro opções naturais, como calda de fumo, óleo de neem ou calda bordalesa. "
     "4) Não use veneno sem receita agronômica. Mande uma foto para um agrônomo na aba Ajuda."),
    (["solo", "terra fraca", "adubo", "adubacao", "calcario", "acidez", "esterco", "compostagem"],
     "Para melhorar o solo: faça uma análise de solo (o agrônomo te ajuda a ler o resultado). Corrija a "
     "acidez com calcário uns 2 a 3 meses antes de plantar. Use esterco curtido ou composto e mantenha o solo "
     "coberto com palha. Plantar feijão-de-porco ou crotalária entre safras também ajuda."),
    (["agua", "irrigacao", "irrigar", "seca", "molhar", "chuva", "gotejamento", "cisterna"],
     "Para economizar água: regue de manhã cedo ou no fim da tarde, use gotejamento e cubra o solo com palha. "
     "Cisterna para guardar água de chuva ajuda muito no Nordeste. Você pode alugar um sistema de irrigação "
     "na aba Recursos."),
    (["preco", "vender", "venda", "cliente", "comprador", "lucro", "ganhar"],
     "Para vender melhor: 1) Veja o preço da sua região antes de anunciar. 2) Coloque foto boa e diga se é "
     "orgânico. 3) Veja as Demandas no Mercado: restaurantes e mercados já dizem o que querem comprar. "
     "4) Vender junto com vizinhos (em cooperativa) dá mais força para negociar."),
    (["maquina", "trator", "colheitadeira", "alugar", "aluguel", "equipamento", "pulverizador"],
     "Na aba Recursos > Máquinas você aluga equipamentos de outros produtores por dia. Se você tem uma máquina "
     "parada, toque em 'Anunciar equipamento' e ganhe renda extra."),
    (["terreno", "terra parada", "area", "parceria", "arrendar", "inutil", "pedregoso", "encharcado", "inclinado"],
     "Área que parece inútil muitas vezes serve! Terreno inclinado: café, frutas e agrofloresta. Encharcado: "
     "arroz, taioba ou inhame. Pedregoso: palma, sisal ou mandioca. Anuncie em Recursos > Terras: outro "
     "produtor pode alugar ou fazer parceria dividindo o lucro, e um agrônomo pode avaliar a área."),
    (["indigena", "aldeia", "povo", "comunidade", "cultura", "artesanato"],
     "A área Povos & Territórios é exclusiva para comunidades indígenas venderem seus produtos e mostrarem "
     "sua cultura. Toda publicação precisa da autorização da própria comunidade ou associação."),
    (["mandioca", "macaxeira", "aipim"],
     "Mandioca: plante manivas de 15 a 20 cm no início das chuvas, espaçamento de cerca de 1 m x 0,6 m. "
     "Aguenta solo fraco e seca. Colheita de 8 a 18 meses, conforme a variedade."),
    (["milho"],
     "Milho: plante no início das chuvas, umas 4 a 5 sementes por metro. Precisa de adubo com nitrogênio. "
     "Fique de olho na lagarta-do-cartucho nas primeiras semanas."),
    (["feijao"],
     "Feijão: ciclo curto (cerca de 90 dias). Não gosta de solo encharcado. Plante com espaçamento de 40 a "
     "50 cm entre linhas. Ótimo para alternar com milho."),
    (["banana"],
     "Banana: precisa de bastante água e matéria orgânica. Tire os brotos em excesso e deixe 'mãe, filha e "
     "neta' em cada touceira. Corte a folha seca para evitar doenças."),
    (["tomate"],
     "Tomate: use estaca ou tutor, regue sem molhar as folhas e faça rotação de cultura. Atenção à traça e à "
     "requeima em época de chuva."),
    (["credito", "financiamento", "pronaf", "emprestimo", "dinheiro", "banco"],
     "Para crédito rural, procure o Pronaf (Programa Nacional de Fortalecimento da Agricultura Familiar) no "
     "seu banco ou na Emater/órgão de assistência técnica da sua região. Leve seus documentos e o CAF."),
    (["cadastro", "senha", "conta", "login", "app", "aplicativo", "como usa"],
     "No Agro Money: Início mostra atalhos; Mercado é para comprar e vender; Recursos tem máquinas e terras; "
     "Povos é a área indígena; Ajuda tem o assistente e os agrônomos. Toque em 🔊 no topo para ouvir a tela."),
]


def responder_ia(pergunta, perfil=""):
    texto = sem_acento(pergunta)
    respostas = []
    for chaves, resposta in BASE_IA:
        if any(chave in texto for chave in chaves):
            respostas.append(resposta)
    if not respostas:
        return ("Ainda não sei responder isso com certeza. Tente perguntar sobre pragas, solo, água, preço, "
                "máquinas, terrenos ou uma cultura (milho, feijão, mandioca...). Para um caso específico, fale "
                "com um agrônomo na aba Ajuda.")
    return "\n\n".join(respostas[:2])


# =====================================================================
# BANCO DE DADOS EM MEMÓRIA (dados fictícios de demonstração)
# =====================================================================

class Banco:
    def __init__(self):
        self.usuarios = [
            self._u("produtor", "José da Silva", "produtor", "Gravatá - PE", "81 99999-0001"),
            self._u("comprador", "Maria Souza", "comprador", "Recife - PE", "81 99999-0002"),
            self._u("restaurante", "Restaurante Sabor do Campo", "empresa", "Caruaru - PE", "81 99999-0003"),
            self._u("ong", "Cooperativa Mãos da Terra", "ong", "Garanhuns - PE", "81 99999-0004"),
            self._u("indigena", "Associação Indígena Raízes (exemplo)", "indigena", "Território (exemplo) - PE",
                    "81 99999-0005"),
            self._u("agronomo", "Dra. Ana Lima", "agronomo", "Recife - PE", "81 99999-0006"),
        ]

        self.produtos = [
            self._p("Banana orgânica", "🍌", "Frutas", 3.50, "kg", "José da Silva", "Gravatá - PE", 300, True,
                    "Banana prata colhida na semana, sem agrotóxico."),
            self._p("Alface fresca", "🥬", "Verduras", 2.00, "unidade", "Sítio Boa Terra", "Chã Grande - PE", 150,
                    True, "Alface crespa colhida no dia da entrega."),
            self._p("Batata-doce", "🍠", "Raízes", 4.00, "kg", "Agricultura familiar Lima", "Bezerros - PE", 500,
                    False, "Batata-doce roxa, ótima para restaurantes."),
            self._p("Milho verde", "🌽", "Grãos", 1.20, "unidade", "Sítio Esperança", "Caruaru - PE", 800, False,
                    "Espiga graúda, ideal para festas juninas e restaurantes."),
            self._p("Mel artesanal", "🍯", "Mel e derivados", 35.00, "litro", "Apiário Flor do Sertão",
                    "Arcoverde - PE", 60, True, "Mel puro de florada silvestre."),
            self._p("Queijo coalho", "🧀", "Laticínios", 38.00, "kg", "Laticínio Família Santos", "Pesqueira - PE",
                    80, False, "Queijo coalho artesanal com selo de inspeção."),
            self._p("Ovos caipiras", "🥚", "Ovos e carnes", 14.00, "dúzia", "Granja Pé de Serra", "Gravatá - PE",
                    120, True, "Galinhas criadas soltas."),
            self._p("Tomate", "🍅", "Verduras", 5.50, "kg", "Horta do Seu Antônio", "Vitória - PE", 200, False,
                    "Tomate italiano firme, bom para molho."),
            self._p("Mandioca", "🥔", "Raízes", 2.80, "kg", "José da Silva", "Gravatá - PE", 400, True,
                    "Macaxeira mansa, cozinha rápido."),
            self._p("Feijão de corda", "🫘", "Grãos", 9.00, "kg", "Cooperativa Mãos da Terra", "Garanhuns - PE",
                    350, False, "Feijão novo da última safra."),
        ]

        self.demandas = [
            {"id": novo_id(), "comprador": "Restaurante Sabor do Campo", "tipo_comp": "Restaurante",
             "produto": "Tomate", "quantidade": "80 kg por semana", "preco": "Até R$ 5,00/kg",
             "local": "Caruaru - PE", "data": "18/11"},
            {"id": novo_id(), "comprador": "Mercadinho Bom Preço", "tipo_comp": "Mercado",
             "produto": "Banana", "quantidade": "200 kg por semana", "preco": "A combinar",
             "local": "Recife - PE", "data": "19/11"},
            {"id": novo_id(), "comprador": "Escola Municipal (merenda)", "tipo_comp": "Instituição",
             "produto": "Alface e verduras", "quantidade": "100 unidades por semana", "preco": "Preço de tabela",
             "local": "Gravatá - PE", "data": "20/11"},
        ]

        self.maquinas = [
            self._m("Colheitadeira", "🚜", 350, "Diária", "Produtor parceiro", "Gravatá - PE", True,
                    "Colheitadeira média para milho e feijão. Pode ir com operador."),
            self._m("Trator 75 cv", "🚜", 220, "Diária", "Sítio Esperança", "Caruaru - PE", True,
                    "Trator com grade aradora e carreta."),
            self._m("Sistema de irrigação", "💧", 70, "Diária", "José da Silva", "Gravatá - PE", False,
                    "Kit de gotejamento para até 1 hectare. Equipamento compartilhado na região."),
            self._m("Plantadeira", "🌱", 180, "Diária", "Cooperativa Mãos da Terra", "Garanhuns - PE", True,
                    "Plantadeira de 4 linhas para milho e feijão."),
            self._m("Pulverizador costal", "🧴", 25, "Diária", "Horta do Seu Antônio", "Vitória - PE", False,
                    "Pulverizador de 20 litros, bem conservado."),
            self._m("Triturador de forragem", "⚙️", 60, "Diária", "Granja Pé de Serra", "Gravatá - PE", False,
                    "Para preparar ração e silagem."),
        ]

        self.terras = [
            self._t("Encosta de 2 hectares", 2.0, "Gravatá - PE", "Inclinado", "Poço a 200 m", "Parceria", 30,
                    0, "José da Silva", ["Café sombreado", "Frutas", "Agrofloresta"],
                    "Área inclinada que o dono acha difícil de usar. Boa para culturas permanentes."),
            self._t("Baixada úmida de 1 hectare", 1.0, "Bezerros - PE", "Encharcado", "Riacho no terreno",
                    "Aluguel", 0, 250, "Sítio Boa Terra", ["Taioba", "Inhame", "Arroz"],
                    "Fica alagada na chuva, mas é ótima para culturas que gostam de umidade."),
            self._t("Área pedregosa de 3 hectares", 3.0, "Arcoverde - PE", "Pedregoso", "Cisterna", "Parceria", 25,
                    0, "Apiário Flor do Sertão", ["Palma forrageira", "Mandioca", "Pasto para abelhas"],
                    "Solo raso com pedras. Pode render bem com palma e mandioca."),
            self._t("Quintal produtivo de 0,5 hectare", 0.5, "Caruaru - PE", "Bom, sem uso", "Água encanada",
                    "Aluguel", 0, 150, "Dona Rita", ["Hortaliças", "Temperos", "Plantas medicinais"],
                    "Terreno bom, só falta quem cultive."),
        ]

        self.prod_indigenas = [
            self._i("Cestaria tradicional", "🧺", 85.00, "unidade", "Associação Indígena Raízes (exemplo)",
                    "Artesanato", "Cestos trançados à mão com fibras coletadas de forma sustentável."),
            self._i("Farinha de mandioca tradicional", "🥣", 12.00, "kg", "Aldeia Exemplo do Agreste",
                    "Alimento", "Feita na casa de farinha da comunidade, do jeito tradicional."),
            self._i("Castanha coletada", "🌰", 45.00, "kg", "Associação Floresta Viva (exemplo)", "Alimento",
                    "Coleta sustentável que ajuda a manter a floresta em pé."),
            self._i("Mel de abelhas nativas", "🍯", 60.00, "litro", "Aldeia Exemplo do Agreste", "Alimento",
                    "Mel de abelhas sem ferrão, criadas pela comunidade."),
            self._i("Cerâmica com grafismos", "🏺", 120.00, "unidade", "Associação Indígena Raízes (exemplo)",
                    "Artesanato", "Peças feitas à mão. Os grafismos foram autorizados para venda pela comunidade."),
            self._i("Açaí de manejo", "🫐", 18.00, "kg", "Associação Floresta Viva (exemplo)", "Alimento",
                    "Polpa de açaí de manejo comunitário."),
        ]

        self.culturas = [
            {"titulo": "Você sabia?", "emoji": "📊", "autor": "Dados do IBGE",
             "texto": "O Censo 2022 contou cerca de 1,7 milhão de pessoas indígenas no Brasil. O Censo 2010 "
                      "registrou 305 povos e 274 línguas indígenas diferentes."},
            {"titulo": "A casa de farinha", "emoji": "🏠", "autor": "Aldeia Exemplo do Agreste",
             "texto": "Fazer farinha é um trabalho coletivo: a família e os vizinhos se juntam para descascar, "
                      "ralar, prensar e torrar a mandioca. É um momento de trabalho e de convivência."},
            {"titulo": "Floresta em pé gera renda", "emoji": "🌳", "autor": "Associação Floresta Viva (exemplo)",
             "texto": "A coleta de castanha e o manejo do açaí mostram que é possível ter renda cuidando da "
                      "floresta, sem desmatar."},
            {"titulo": "Grafismos têm significado", "emoji": "🎨", "autor": "Associação Indígena Raízes (exemplo)",
             "texto": "Os desenhos nas peças contam histórias e identificam o povo. Por isso, só são vendidos "
                      "quando a comunidade autoriza. Copiar sem permissão desrespeita a cultura."},
        ]

        self.projetos = [
            {"id": novo_id(), "titulo": "Viveiro de mudas nativas", "emoji": "🌱",
             "comunidade": "Associação Floresta Viva (exemplo)", "meta": 15000.0, "arrecadado": 9200.0,
             "desc": "Produzir mudas para recuperar nascentes e gerar renda com reflorestamento."},
            {"id": novo_id(), "titulo": "Nova casa de farinha", "emoji": "🏠",
             "comunidade": "Aldeia Exemplo do Agreste", "meta": 22000.0, "arrecadado": 6100.0,
             "desc": "Equipar a casa de farinha comunitária para aumentar a produção."},
            {"id": novo_id(), "titulo": "Meliponário comunitário", "emoji": "🐝",
             "comunidade": "Aldeia Exemplo do Agreste", "meta": 8000.0, "arrecadado": 7300.0,
             "desc": "Ampliar a criação de abelhas nativas sem ferrão."},
        ]

        self.agronomos = [
            {"id": novo_id(), "nome": "Dra. Ana Lima", "emoji": "👩‍🔬", "area": "Solo e adubação",
             "registro": "CREA (exemplo) 12345", "local": "Recife - PE", "nota": 4.9, "atendimentos": 132,
             "preco": "1ª consulta grátis", "bio": "Ajuda a ler análise de solo e montar adubação barata."},
            {"id": novo_id(), "nome": "Carlos Souza", "emoji": "👨‍🔬", "area": "Pragas e doenças",
             "registro": "CREA (exemplo) 23456", "local": "Caruaru - PE", "nota": 4.8, "atendimentos": 98,
             "preco": "R$ 40 por vídeo", "bio": "Especialista em controle natural de pragas."},
            {"id": novo_id(), "nome": "Beatriz Rocha", "emoji": "👩‍🌾", "area": "Irrigação e água",
             "registro": "CREA (exemplo) 34567", "local": "Petrolina - PE", "nota": 4.9, "atendimentos": 75,
             "preco": "1ª consulta grátis", "bio": "Projeta irrigação por gotejamento e cisternas."},
            {"id": novo_id(), "nome": "João Pereira", "emoji": "🧑‍🌾", "area": "Agroecologia e agrofloresta",
             "registro": "CREA (exemplo) 45678", "local": "Garanhuns - PE", "nota": 5.0, "atendimentos": 61,
             "preco": "R$ 60 por visita", "bio": "Transforma áreas 'inúteis' em sistemas produtivos."},
            {"id": novo_id(), "nome": "Paula Martins", "emoji": "👩‍💼", "area": "Planejamento e vendas",
             "registro": "CREA (exemplo) 56789", "local": "Recife - PE", "nota": 4.7, "atendimentos": 54,
             "preco": "R$ 30 por ligação", "bio": "Ajuda a calcular custos, preço e onde vender."},
        ]

        self.pedidos = []  # compras, aluguéis, parcerias, consultas, apoios
        self.solicitacoes_agro = [  # o que o agrônomo recebe
            {"id": novo_id(), "produtor": "José da Silva", "problema": "Pragas", "forma": "Vídeo",
             "texto": "Minhas folhas de banana estão com manchas amarelas.", "status": "Nova", "data": "19/11"},
            {"id": novo_id(), "produtor": "Sítio Boa Terra", "problema": "Solo", "forma": "Visita",
             "texto": "Quero saber se a baixada serve para plantar inhame.", "status": "Nova", "data": "20/11"},
        ]

    # ---------- construtores de registros ----------
    @staticmethod
    def _u(usuario, nome, tipo, cidade, telefone):
        return {"id": novo_id(), "usuario": usuario, "senha": "123456", "nome": nome, "tipo": tipo,
                "cidade": cidade, "telefone": so_digitos(telefone), "documento": "", "extra": {}}

    @staticmethod
    def _p(nome, emoji, cat, preco, unidade, vendedor, local, estoque, organico, desc):
        return {"id": novo_id(), "nome": nome, "emoji": emoji, "categoria": cat, "preco": preco,
                "unidade": unidade, "vendedor": vendedor, "local": local, "estoque": estoque,
                "organico": organico, "desc": desc}

    @staticmethod
    def _m(nome, emoji, preco, periodo, dono, local, operador, desc):
        return {"id": novo_id(), "nome": nome, "emoji": emoji, "preco": preco, "periodo": periodo,
                "dono": dono, "local": local, "operador": operador, "desc": desc}

    @staticmethod
    def _t(titulo, hectares, local, condicao, agua, modalidade, parte_dono, aluguel, dono, sugestoes, desc):
        return {"id": novo_id(), "titulo": titulo, "hectares": hectares, "local": local, "condicao": condicao,
                "agua": agua, "modalidade": modalidade, "parte_dono": parte_dono, "aluguel": aluguel,
                "dono": dono, "sugestoes": sugestoes, "desc": desc}

    @staticmethod
    def _i(nome, emoji, preco, unidade, comunidade, tipo, desc):
        return {"id": novo_id(), "nome": nome, "emoji": emoji, "preco": preco, "unidade": unidade,
                "comunidade": comunidade, "tipo": tipo, "desc": desc, "autorizado": True}

    # ---------- consultas ----------
    def achar(self, lista, item_id):
        for item in getattr(self, lista):
            if item["id"] == item_id:
                return item
        return None

    def login(self, identificador, senha):
        ident = (identificador or "").strip().lower()
        digitos = so_digitos(identificador)
        for u in self.usuarios:
            if u["senha"] != senha:
                continue
            if ident == u["usuario"].lower():
                return u
            if digitos and len(digitos) >= 10 and digitos in (u["telefone"], u["documento"]):
                return u
        return None

    def existe(self, usuario="", documento="", telefone=""):
        for u in self.usuarios:
            if usuario and u["usuario"].lower() == usuario.lower():
                return "Esse nome de usuário já está em uso."
            if documento and u["documento"] == documento:
                return "Esse documento já tem cadastro."
            if telefone and u["telefone"] == telefone:
                return "Esse telefone já tem cadastro."
        return None


# =====================================================================
# APLICATIVO
# =====================================================================

class AgroMoney:
    TELAS_SEM_LOGIN = ("login", "tipo_conta", "cadastro", "recuperar")

    def __init__(self, page):
        self.page = page
        self.db = Banco()
        self.usuario = None
        self.c = TEMA_NORMAL
        self.alto_contraste = False
        self.escala = 1.0
        self.leitura_auto = False
        self.rota = "login"
        self.params = {}
        self.historico = []
        self.texto_tela = ""
        self.tipo_cadastro = "produtor"
        self.chat = []
        self.aviso = None  # (mensagem, tipo)

        page.title = "Agro Money"
        page.padding = 0
        page.theme_mode = ft.ThemeMode.LIGHT
        page.theme = ft.Theme(color_scheme_seed="#2E7D32")
        try:
            page.window.width = 420
            page.window.height = 860
        except Exception:
            pass

        self.render()

    # -----------------------------------------------------------------
    # NAVEGAÇÃO
    # -----------------------------------------------------------------
    def ir(self, rota, **params):
        if rota != self.rota or params != self.params:
            self.historico.append((self.rota, self.params))
            self.historico = self.historico[-30:]
        self.rota = rota
        self.params = params
        self.aviso = None
        self.render()

    def voltar(self, e=None):
        if self.historico:
            self.rota, self.params = self.historico.pop()
        else:
            self.rota, self.params = ("inicio" if self.usuario else "login"), {}
        self.aviso = None
        self.render()

    def avisar(self, msg, tipo="ok"):
        self.aviso = (msg, tipo)
        self.render()

    def render(self):
        construtores = {
            "login": self.tela_login,
            "tipo_conta": self.tela_tipo_conta,
            "cadastro": self.tela_cadastro,
            "recuperar": self.tela_recuperar,
            "inicio": self.tela_inicio,
            "busca": self.tela_busca,
            "mercado": self.tela_mercado,
            "produto": self.tela_produto,
            "anunciar_produto": self.tela_anunciar_produto,
            "nova_demanda": self.tela_nova_demanda,
            "recursos": self.tela_recursos,
            "maquina": self.tela_maquina,
            "anunciar_maquina": self.tela_anunciar_maquina,
            "terra": self.tela_terra,
            "anunciar_terra": self.tela_anunciar_terra,
            "povos": self.tela_povos,
            "povos_produto": self.tela_povos_produto,
            "povos_cultura": self.tela_povos_cultura,
            "povos_parcerias": self.tela_povos_parcerias,
            "povos_publicar": self.tela_povos_publicar,
            "ajuda": self.tela_ajuda,
            "assistente": self.tela_assistente,
            "agronomos": self.tela_agronomos,
            "agronomo": self.tela_agronomo,
            "pedidos": self.tela_pedidos,
            "perfil": self.tela_perfil,
        }
        if self.rota not in self.TELAS_SEM_LOGIN and not self.usuario:
            self.rota, self.params = "login", {}
        construtor = construtores.get(self.rota, self.tela_inicio)
        conteudo = construtor(**self.params)

        c = self.c
        self.page.bgcolor = c["fundo"]
        self.page.controls.clear()

        corpo = ft.Column(
            controls=[ft.Container(content=ft.Column(controls=conteudo, spacing=14),
                                   padding=ft.Padding(left=16, top=14, right=16, bottom=28))],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
        )

        partes = []
        if self.rota in self.TELAS_SEM_LOGIN:
            partes.append(self.barra_acessibilidade_topo())
        else:
            partes.append(self.cabecalho())
        if self.aviso:
            partes.append(self.caixa_aviso())
        partes.append(corpo)
        if self.rota not in self.TELAS_SEM_LOGIN:
            partes.append(self.menu_inferior())

        self.page.add(ft.SafeArea(content=ft.Column(controls=partes, spacing=0, expand=True), expand=True))
        self.page.update()

        if self.leitura_auto and self.texto_tela:
            falar_em_voz(self.texto_tela)

    # -----------------------------------------------------------------
    # COMPONENTES VISUAIS REUTILIZÁVEIS
    # -----------------------------------------------------------------
    def tam(self, n):
        return round(n * self.escala)

    def borda(self, cor=None, largura=None):
        lado = ft.BorderSide(width=largura or self.c["borda_w"], color=cor or self.c["borda"])
        return ft.Border(left=lado, top=lado, right=lado, bottom=lado)

    def txt(self, valor, tamanho=16, negrito=False, cor=None, centro=False, italico=False):
        return ft.Text(
            str(valor),
            size=self.tam(tamanho),
            weight=ft.FontWeight.BOLD if negrito else ft.FontWeight.NORMAL,
            color=cor or self.c["texto"],
            text_align=ft.TextAlign.CENTER if centro else ft.TextAlign.LEFT,
            italic=italico,
        )

    def titulo(self, texto, subtitulo=None, emoji=None):
        linha = ft.Row(
            controls=([self.txt(emoji, 26)] if emoji else []) + [
                ft.Container(content=self.txt(texto, 24, True), expand=True)],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        controles = [linha]
        if subtitulo:
            controles.append(self.txt(subtitulo, 15, cor=self.c["suave"]))
        return ft.Column(controls=controles, spacing=4)

    def secao(self, texto, acao=None, ao_clicar=None):
        controles = [ft.Container(content=self.txt(texto, 19, True), expand=True)]
        if acao:
            controles.append(ft.Container(content=self.txt(acao + " →", 14, True, self.c["primaria2"]),
                                          on_click=ao_clicar, padding=6))
        return ft.Row(controls=controles, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def botao(self, texto, ao_clicar, tipo="primario", expandir=False, largura=None, altura=52):
        c = self.c
        estilos = {
            "primario": (c["primaria"], c["sobre_primaria"], None),
            "secundario": (c["card"], c["primaria"], c["primaria"]),
            "claro": (c["clara"], c["primaria"], c["borda"]),
            "perigo": (c["erro_fundo"], c["erro"], c["erro"]),
            "indigena": (c["indigena"], "#FFFFFF", None),
        }
        fundo, cor_texto, cor_borda = estilos.get(tipo, estilos["primario"])
        return ft.Container(
            content=ft.Text(texto, size=self.tam(16), weight=ft.FontWeight.BOLD, color=cor_texto,
                            text_align=ft.TextAlign.CENTER),
            bgcolor=fundo,
            border=self.borda(cor_borda, 2) if cor_borda else None,
            border_radius=14,
            height=self.tam(altura),
            width=largura,
            expand=expandir,
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(left=14, top=0, right=14, bottom=0),
            on_click=ao_clicar,
            ink=True,
        )

    def card(self, controles, ao_clicar=None, padding=16, fundo=None, cor_borda=None, expandir=False):
        return ft.Container(
            content=ft.Column(controls=controles, spacing=8) if isinstance(controles, list) else controles,
            bgcolor=fundo or self.c["card"],
            border=self.borda(cor_borda),
            border_radius=18,
            padding=padding,
            on_click=ao_clicar,
            ink=ao_clicar is not None,
            expand=expandir,
        )

    def campo(self, rotulo, dica="", senha=False, teclado=None, valor="", multilinha=False, ao_mudar=None,
              ao_enviar=None):
        c = self.c
        return ft.TextField(
            label=rotulo,
            hint_text=dica,
            value=valor,
            password=senha,
            can_reveal_password=senha,
            keyboard_type=teclado or ft.KeyboardType.TEXT,
            multiline=multilinha,
            min_lines=3 if multilinha else 1,
            max_lines=6 if multilinha else 1,
            border_radius=14,
            border_color=c["borda"] if not self.alto_contraste else "#000000",
            focused_border_color=c["primaria"],
            bgcolor=c["card"],
            filled=True,
            color=c["texto"],
            cursor_color=c["primaria"],
            text_size=self.tam(17),
            label_style=ft.TextStyle(color=c["suave"], size=self.tam(15)),
            hint_style=ft.TextStyle(color=c["suave"], size=self.tam(15)),
            on_change=ao_mudar,
            on_submit=ao_enviar,
        )

    def chips(self, opcoes, estado, chave, ao_mudar=None, cor=None):
        """Grupo de botões de escolha. estado[chave] guarda a opção escolhida."""
        c = self.c
        linha = ft.Row(wrap=True, spacing=8, run_spacing=8)

        def montar():
            linha.controls.clear()
            for op in opcoes:
                marcado = estado.get(chave) == op
                linha.controls.append(ft.Container(
                    content=ft.Text(("✓ " if marcado else "") + op, size=self.tam(14),
                                    weight=ft.FontWeight.BOLD,
                                    color=c["sobre_primaria"] if marcado else (cor or c["primaria"])),
                    bgcolor=(cor or c["primaria"]) if marcado else c["card"],
                    border=self.borda(cor or c["primaria"], 2 if marcado else c["borda_w"]),
                    border_radius=20,
                    padding=ft.Padding(left=14, top=9, right=14, bottom=9),
                    on_click=lambda e, o=op: escolher(o),
                    ink=True,
                ))

        def escolher(op):
            estado[chave] = op
            montar()
            if ao_mudar:
                ao_mudar(op)
            self.page.update()

        montar()
        return linha

    def contador(self, estado, chave, minimo=1, maximo=9999, passo=1, ao_mudar=None, sufixo=""):
        """Botões − e + grandes, fáceis de usar."""
        c = self.c
        valor_txt = self.txt(f"{estado[chave]}{sufixo}", 22, True)

        def mudar(delta):
            estado[chave] = max(minimo, min(maximo, estado[chave] + delta))
            valor_txt.value = f"{estado[chave]}{sufixo}"
            if ao_mudar:
                ao_mudar()
            self.page.update()

        def bt(simbolo, delta):
            return ft.Container(content=self.txt(simbolo, 24, True, c["primaria"], centro=True),
                                width=self.tam(56), height=self.tam(56), border_radius=28,
                                bgcolor=c["clara"], border=self.borda(c["primaria"], 2),
                                alignment=ft.Alignment(0, 0), on_click=lambda e: mudar(delta), ink=True)

        return ft.Row(controls=[bt("−", -passo), ft.Container(content=valor_txt, padding=10), bt("+", passo)],
                      alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def selo(self, texto, fundo=None, cor=None):
        return ft.Container(content=ft.Text(texto, size=self.tam(12), weight=ft.FontWeight.BOLD,
                                            color=cor or self.c["primaria"]),
                            bgcolor=fundo or self.c["clara"], border_radius=10,
                            padding=ft.Padding(left=8, top=4, right=8, bottom=4),
                            border=self.borda(cor) if self.alto_contraste else None)

    def emoji_box(self, emoji, tamanho=44, fundo=None):
        return ft.Container(content=ft.Text(emoji, size=self.tam(tamanho)), bgcolor=fundo or self.c["clara"],
                            border_radius=14, alignment=ft.Alignment(0, 0),
                            height=self.tam(tamanho * 1.9))

    def info_linha(self, rotulo, valor):
        return ft.Row(controls=[self.txt(rotulo, 14, cor=self.c["suave"]),
                                ft.Container(content=self.txt(valor, 15, True), expand=True)],
                      spacing=8)

    def caixa_info(self, texto, emoji="ℹ️", tipo="ok"):
        c = self.c
        fundo = {"ok": c["ok_fundo"], "alerta": c["alerta_fundo"], "indigena": c["indigena_fundo"]}[tipo]
        cor = {"ok": c["primaria"], "alerta": c["alerta"], "indigena": c["indigena"]}[tipo]
        return ft.Container(
            content=ft.Row(controls=[self.txt(emoji, 20),
                                     ft.Container(content=self.txt(texto, 14, cor=cor), expand=True)],
                           vertical_alignment=ft.CrossAxisAlignment.START),
            bgcolor=fundo, border_radius=14, padding=12, border=self.borda(cor))

    def faixa(self, titulo, texto, botao=None, ao_clicar=None, indigena=False):
        """Banner verde de destaque (com texto bem legível)."""
        c = self.c
        fundo = c["indigena"] if indigena else c["primaria2"]
        controles = [self.txt(titulo, 21, True, "#FFFFFF"), self.txt(texto, 15, cor="#FFFFFF")]
        if botao:
            controles.append(ft.Container(
                content=ft.Text(botao + " →", size=self.tam(15), weight=ft.FontWeight.BOLD, color=fundo),
                bgcolor="#FFFFFF", border_radius=12, padding=ft.Padding(left=16, top=11, right=16, bottom=11),
                on_click=ao_clicar, ink=True))
        return ft.Container(content=ft.Column(controls=controles, spacing=8), bgcolor=fundo, border_radius=20,
                            padding=20)

    def caixa_aviso(self):
        msg, tipo = self.aviso
        c = self.c
        fundo, cor, emoji = {
            "ok": (c["ok_fundo"], c["primaria"], "✅"),
            "erro": (c["erro_fundo"], c["erro"], "⚠️"),
            "info": (c["alerta_fundo"], c["alerta"], "ℹ️"),
        }.get(tipo, (c["ok_fundo"], c["primaria"], "✅"))

        def fechar(e):
            self.aviso = None
            self.render()

        return ft.Container(
            content=ft.Row(controls=[self.txt(emoji, 18),
                                     ft.Container(content=self.txt(msg, 15, True, cor), expand=True),
                                     ft.Container(content=self.txt("✕", 18, True, cor), on_click=fechar,
                                                  padding=6)],
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=fundo, padding=ft.Padding(left=14, top=10, right=10, bottom=10),
            border=ft.Border(bottom=ft.BorderSide(width=2, color=cor)))

    def lista_em_pares(self, cards):
        """Coloca cards lado a lado (2 por linha), bom para celular."""
        linhas = []
        for i in range(0, len(cards), 2):
            par = cards[i:i + 2]
            if len(par) == 1:
                par.append(ft.Container(expand=True))
            linhas.append(ft.Row(controls=par, spacing=12, vertical_alignment=ft.CrossAxisAlignment.START))
        return ft.Column(controls=linhas, spacing=12)

    # -----------------------------------------------------------------
    # CABEÇALHO, MENU E ACESSIBILIDADE
    # -----------------------------------------------------------------
    def botao_redondo(self, simbolo, ao_clicar, dica=""):
        return ft.Container(content=ft.Text(simbolo, size=self.tam(18), color="#FFFFFF"),
                            width=self.tam(42), height=self.tam(42), border_radius=21,
                            bgcolor="#FFFFFF22" if not self.alto_contraste else "#000000",
                            border=self.borda("#FFFFFF", 1), alignment=ft.Alignment(0, 0),
                            on_click=ao_clicar, ink=True, tooltip=dica or None)

    def cabecalho(self):
        c = self.c
        principais = ("inicio", "mercado", "recursos", "povos", "ajuda")
        esquerda = []
        if self.rota not in principais:
            esquerda.append(self.botao_redondo("←", self.voltar, "Voltar"))
        esquerda.append(ft.Column(controls=[
            ft.Text("🌱 Agro Money", size=self.tam(21), weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            ft.Text("Oportunidade para quem faz o Brasil crescer", size=self.tam(11), color="#E8F5E9"),
        ], spacing=0, expand=True))

        primeira = self.usuario["nome"][:1].upper() if self.usuario else "?"
        avatar = ft.Container(
            content=ft.Text(PERFIS[self.usuario["tipo"]]["emoji"] if self.usuario else primeira,
                            size=self.tam(20)),
            width=self.tam(42), height=self.tam(42), border_radius=21, bgcolor="#FFFFFF",
            alignment=ft.Alignment(0, 0), on_click=lambda e: self.ir("perfil"), ink=True, tooltip="Meu perfil")

        topo = ft.Row(controls=esquerda + [
            self.botao_redondo("🔊", self.ouvir_tela, "Ouvir tela"),
            self.botao_redondo("◐", self.trocar_contraste, "Alto contraste"),
            avatar,
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        controles = [topo]
        if self.rota in principais:
            busca = ft.TextField(
                hint_text="🔎 O que você está procurando?",
                border_radius=24, bgcolor="#FFFFFF", filled=True, color="#14261A",
                border_color="#FFFFFF", focused_border_color="#A5D6A7", text_size=self.tam(16),
                hint_style=ft.TextStyle(color="#46594A", size=self.tam(15)),
                content_padding=ft.Padding(left=18, top=10, right=18, bottom=10),
                on_submit=lambda e: self.ir("busca", termo=e.control.value or ""),
            )
            controles.append(busca)
        return ft.Container(content=ft.Column(controls=controles, spacing=12), bgcolor=c["primaria"],
                            padding=ft.Padding(left=16, top=12, right=16, bottom=14))

    def barra_acessibilidade_topo(self):
        c = self.c

        def bt(texto, acao):
            return ft.Container(content=ft.Text(texto, size=self.tam(14), weight=ft.FontWeight.BOLD,
                                                color=c["primaria"]),
                                bgcolor=c["clara"], border=self.borda(c["primaria"], 1), border_radius=12,
                                padding=ft.Padding(left=10, top=8, right=10, bottom=8), on_click=acao, ink=True,
                                expand=True, alignment=ft.Alignment(0, 0))

        return ft.Container(
            content=ft.Row(controls=[bt("🔊 Ouvir tela", self.ouvir_tela),
                                     bt("◐ Contraste", self.trocar_contraste),
                                     bt("A+ Letra", self.trocar_letra)], spacing=8),
            bgcolor=c["card"], padding=ft.Padding(left=12, top=10, right=12, bottom=10),
            border=ft.Border(bottom=ft.BorderSide(width=1, color=c["borda"])))

    def menu_inferior(self):
        c = self.c
        itens = [("inicio", "🏠", "Início"), ("mercado", "🛒", "Mercado"), ("recursos", "🚜", "Recursos"),
                 ("povos", "🪶", "Povos"), ("ajuda", "🤖", "Ajuda")]
        grupos = {
            "inicio": ("inicio", "busca", "pedidos", "perfil"),
            "mercado": ("mercado", "produto", "anunciar_produto", "nova_demanda"),
            "recursos": ("recursos", "maquina", "anunciar_maquina", "terra", "anunciar_terra"),
            "povos": ("povos", "povos_produto", "povos_cultura", "povos_parcerias", "povos_publicar"),
            "ajuda": ("ajuda", "assistente", "agronomos", "agronomo"),
        }
        botoes = []
        for rota, emoji, nome in itens:
            ativo = self.rota in grupos[rota]
            botoes.append(ft.Container(
                content=ft.Column(controls=[
                    ft.Text(emoji, size=self.tam(22), text_align=ft.TextAlign.CENTER),
                    ft.Text(nome, size=self.tam(12), text_align=ft.TextAlign.CENTER,
                            weight=ft.FontWeight.BOLD if ativo else ft.FontWeight.NORMAL,
                            color=c["primaria"] if ativo else c["suave"]),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=c["clara"] if ativo else None,
                border_radius=14,
                padding=ft.Padding(left=2, top=6, right=2, bottom=6),
                expand=True,
                on_click=lambda e, r=rota: self.trocar_aba(r),
                ink=True,
            ))
        return ft.Container(content=ft.Row(controls=botoes, spacing=4), bgcolor=c["card"],
                            padding=ft.Padding(left=8, top=6, right=8, bottom=8),
                            border=ft.Border(top=ft.BorderSide(width=c["borda_w"], color=c["borda"])))

    def trocar_aba(self, rota):
        self.historico = []
        self.rota, self.params, self.aviso = rota, {}, None
        self.render()

    def ouvir_tela(self, e=None):
        texto = self.texto_tela or "Agro Money."
        if falar_em_voz(texto):
            self.avisar("Lendo a tela em voz alta…", "info")
        else:
            self.avisar("Leitura em voz: no celular, ative o 'Selecionar para falar' ou TalkBack. "
                        "No computador, instale: pip install pyttsx3", "info")

    def trocar_contraste(self, e=None):
        self.alto_contraste = not self.alto_contraste
        self.c = TEMA_CONTRASTE if self.alto_contraste else TEMA_NORMAL
        self.render()

    def trocar_letra(self, e=None):
        tamanhos = [1.0, 1.15, 1.3]
        i = tamanhos.index(self.escala) if self.escala in tamanhos else 0
        self.escala = tamanhos[(i + 1) % len(tamanhos)]
        self.render()

    # =================================================================
    # TELAS DE ENTRADA (login, tipo de conta, cadastro, recuperar senha)
    # =================================================================
    def logo(self):
        c = self.c
        return ft.Column(controls=[
            ft.Container(content=ft.Text("🌱", size=self.tam(48)), width=self.tam(92), height=self.tam(92),
                         border_radius=46, bgcolor=c["clara"], border=self.borda(c["primaria"], 2),
                         alignment=ft.Alignment(0, 0)),
            self.txt("Agro Money", 30, True, c["primaria"], centro=True),
            self.txt("Conectando quem produz com quem compra.", 15, cor=c["suave"], centro=True),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

    def tela_login(self):
        c = self.c
        self.texto_tela = ("Tela de entrada do Agro Money. Digite seu CPF, telefone ou usuário, depois sua "
                           "senha, e toque em Entrar. Se ainda não tem conta, toque em Criar conta.")
        ident = self.campo("CPF, telefone ou usuário", "Ex.: produtor", teclado=ft.KeyboardType.TEXT)
        senha = self.campo("Senha", "Sua senha", senha=True)

        def entrar(e=None):
            if not (ident.value or "").strip() or not senha.value:
                self.avisar("Preencha o usuário e a senha.", "erro")
                return
            u = self.db.login(ident.value, senha.value)
            if not u:
                self.avisar("Usuário ou senha incorretos.", "erro")
                return
            self.usuario = u
            self.historico = []
            self.rota, self.params = "inicio", {}
            self.aviso = (f"Bem-vindo(a), {u['nome'].split()[0]}!", "ok")
            self.render()

        senha.on_submit = entrar

        def entrar_demo(tipo):
            usuario = {"produtor": "produtor", "comprador": "comprador", "empresa": "restaurante", "ong": "ong",
                       "indigena": "indigena", "agronomo": "agronomo"}[tipo]
            ident.value, senha.value = usuario, "123456"
            entrar()

        demo_estado = {"tipo": None}

        return [
            ft.Container(height=6),
            self.logo(),
            self.card([
                self.txt("Bem-vindo!", 24, True, c["primaria"], centro=True),
                ident,
                senha,
                self.botao("Entrar →", entrar),
                ft.Row(controls=[ft.Container(content=ft.Divider(color=c["borda"]), expand=True),
                                 self.txt("ou", 14, cor=c["suave"]),
                                 ft.Container(content=ft.Divider(color=c["borda"]), expand=True)],
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.botao("📱 Entrar com número de celular", lambda e: self.avisar(
                    "Digite seu celular com DDD no primeiro campo (ex.: 81 99999-0001) e a senha.", "info"),
                    "secundario"),
                self.botao("🌐 Entrar com Google", lambda e: self.avisar(
                    "Login com Google entra na versão publicada do app (precisa de servidor).", "info"),
                    "secundario"),
                ft.Row(controls=[
                    ft.Container(content=self.txt("Esqueci minha senha", 15, True, c["primaria2"]),
                                 on_click=lambda e: self.ir("recuperar"), padding=6),
                    ft.Container(expand=True),
                    ft.Container(content=self.txt("Criar conta →", 15, True, c["primaria2"]),
                                 on_click=lambda e: self.ir("tipo_conta"), padding=6),
                ]),
            ], padding=20),
            self.botao("✨ Criar minha conta grátis", lambda e: self.ir("tipo_conta"), "claro"),
            self.card([
                self.txt("🧪 Testar sem cadastro", 16, True),
                self.txt("Escolha um tipo de conta de demonstração:", 14, cor=c["suave"]),
                self.chips([PERFIS[k]["emoji"] + " " + PERFIS[k]["nome"] for k in PERFIS], demo_estado, "tipo",
                           ao_mudar=lambda op: entrar_demo(
                               [k for k in PERFIS if op.endswith(PERFIS[k]["nome"])][0])),
            ], fundo=c["clara"]),
            self.txt("Mais oportunidades para o campo, e um Brasil mais forte. 🇧🇷", 13, cor=c["suave"],
                     centro=True),
        ]

    def tela_tipo_conta(self):
        c = self.c
        self.texto_tela = "Criar conta. Escolha quem você é: " + ", ".join(
            p["nome"] for p in PERFIS.values()) + "."

        def escolher(tipo):
            self.tipo_cadastro = tipo
            self.ir("cadastro")

        cards = []
        for chave, p in PERFIS.items():
            cards.append(self.card([
                ft.Text(p["emoji"], size=self.tam(36)),
                self.txt(p["nome"], 16, True),
                self.txt(p["desc"], 13, cor=c["suave"]),
            ], ao_clicar=lambda e, k=chave: escolher(k), expandir=True,
                fundo=c["indigena_fundo"] if chave == "indigena" else None))

        return [
            ft.Row(controls=[ft.Container(content=self.txt("← Voltar", 15, True, c["primaria2"]),
                                          on_click=self.voltar, padding=6)]),
            self.titulo("Criar conta", "Quem é você? Toque em uma opção."),
            self.lista_em_pares(cards),
            self.caixa_info("O cadastro é grátis. Você pode ouvir tudo tocando em 🔊 Ouvir tela.", "💚"),
        ]

    def tela_cadastro(self):
        c = self.c
        tipo = self.tipo_cadastro
        p = PERFIS[tipo]
        self.texto_tela = (f"Cadastro de {p['nome']}. Preencha seu nome, documento, telefone, cidade, "
                           f"crie um usuário e uma senha. Depois toque em Criar conta.")

        rotulo_nome = {"empresa": "Nome da empresa / restaurante", "ong": "Nome da ONG ou cooperativa",
                       "indigena": "Nome da comunidade ou associação"}.get(tipo, "Nome completo")
        nome = self.campo(rotulo_nome)
        doc = self.campo(p["doc"], "Só números", teclado=ft.KeyboardType.NUMBER)
        tel = self.campo("Celular com DDD", "81 99999-9999", teclado=ft.KeyboardType.PHONE)
        cidade = self.campo("Cidade - Estado", "Ex.: Gravatá - PE")
        usuario = self.campo("Crie um nome de usuário", "Ex.: josesilva")
        senha = self.campo("Crie uma senha", "Mínimo 6 caracteres", senha=True)
        senha2 = self.campo("Repita a senha", senha=True)
        aceite = ft.Checkbox(value=False)

        extras = {}
        estado = {}
        campos_extras = []
        if tipo == "produtor":
            extras["producao"] = self.campo("O que você produz?", "Ex.: banana, mandioca, ovos")
            estado["tamanho"] = None
            campos_extras += [extras["producao"], self.txt("Tamanho da propriedade", 15, True),
                              self.chips(["Até 5 ha", "5 a 20 ha", "20 a 100 ha", "Não tenho terra"], estado,
                                         "tamanho")]
        elif tipo == "empresa":
            estado["ramo"] = None
            extras["volume"] = self.campo("O que compra com frequência?", "Ex.: verduras, frutas, queijo")
            campos_extras += [self.txt("Tipo de negócio", 15, True),
                              self.chips(["Restaurante", "Mercado", "Padaria", "Indústria", "Escola/Hospital",
                                          "Outro"], estado, "ramo"), extras["volume"]]
        elif tipo == "ong":
            extras["causa"] = self.campo("Causa ou área de atuação", "Ex.: agricultura familiar, meio ambiente")
            campos_extras.append(extras["causa"])
        elif tipo == "indigena":
            extras["povo"] = self.campo("Povo / etnia")
            extras["territorio"] = self.campo("Terra indígena ou aldeia")
            extras["responsavel"] = self.campo("Nome do responsável pela conta")
            campos_extras += [extras["povo"], extras["territorio"], extras["responsavel"],
                              self.caixa_info("A conta deve ser criada com o conhecimento da comunidade. "
                                              "Nada é publicado sem a autorização dela.", "🪶", "indigena")]
        elif tipo == "agronomo":
            extras["registro"] = self.campo("Registro profissional (CREA/CFTA)")
            estado["area"] = None
            campos_extras += [extras["registro"], self.txt("Especialidade", 15, True),
                              self.chips(["Solo", "Pragas", "Irrigação", "Agroecologia", "Pecuária", "Gestão"],
                                         estado, "area")]

        def criar(e):
            doc_d = so_digitos(doc.value)
            tel_d = so_digitos(tel.value)
            erros = []
            if len((nome.value or "").strip()) < 3:
                erros.append("nome")
            if p["doc"] == "CPF" and not cpf_valido(doc_d):
                erros.append("CPF válido")
            if p["doc"] == "CNPJ" and not cnpj_valido(doc_d):
                erros.append("CNPJ válido")
            if p["doc"] == "CPF ou CNPJ" and not (cpf_valido(doc_d) or cnpj_valido(doc_d)):
                erros.append("CPF ou CNPJ válido")
            if len(tel_d) not in (10, 11):
                erros.append("celular com DDD")
            if len((usuario.value or "").strip()) < 3 or " " in (usuario.value or "").strip():
                erros.append("usuário (sem espaços)")
            if len(senha.value or "") < 6:
                erros.append("senha com 6+ caracteres")
            if erros:
                self.avisar("Confira: " + ", ".join(erros) + ".", "erro")
                return
            if senha.value != senha2.value:
                self.avisar("As senhas não são iguais.", "erro")
                return
            if tipo == "agronomo" and not (extras["registro"].value or "").strip():
                self.avisar("Informe seu registro profissional.", "erro")
                return
            if not aceite.value:
                self.avisar("Aceite os termos de uso para continuar.", "erro")
                return
            repetido = self.db.existe(usuario.value.strip(), doc_d, tel_d)
            if repetido:
                self.avisar(repetido, "erro")
                return
            novo = {"id": novo_id(), "usuario": usuario.value.strip(), "senha": senha.value,
                    "nome": nome.value.strip(), "tipo": tipo, "cidade": (cidade.value or "").strip() or "Brasil",
                    "telefone": tel_d, "documento": doc_d,
                    "extra": {**{k: v.value for k, v in extras.items()}, **estado}}
            self.db.usuarios.append(novo)
            if tipo == "agronomo":
                self.db.agronomos.append({
                    "id": novo["id"], "nome": novo["nome"], "emoji": "🧑‍🔬", "area": estado.get("area") or "Geral",
                    "registro": extras["registro"].value, "local": novo["cidade"], "nota": 5.0,
                    "atendimentos": 0, "preco": "A combinar", "bio": "Novo especialista no Agro Money."})
            self.usuario = novo
            self.historico = []
            self.rota, self.params = "inicio", {}
            self.aviso = ("Conta criada com sucesso! 🎉", "ok")
            self.render()

        return [
            ft.Row(controls=[ft.Container(content=self.txt("← Voltar", 15, True, c["primaria2"]),
                                          on_click=self.voltar, padding=6)]),
            self.titulo(f"Cadastro: {p['nome']}", "Leva menos de 2 minutos.", p["emoji"]),
            self.card([self.txt("Seus dados", 17, True), nome, doc, tel, cidade]),
            *([self.card([self.txt("Sobre você", 17, True), *campos_extras])] if campos_extras else []),
            self.card([self.txt("Acesso", 17, True), usuario, senha, senha2,
                       ft.Row(controls=[aceite, ft.Container(content=self.txt(
                           "Li e aceito os termos de uso e a política de privacidade (LGPD).", 14), expand=True)],
                              vertical_alignment=ft.CrossAxisAlignment.CENTER)]),
            self.botao("Criar conta ✓", criar),
            self.botao("Já tenho conta", lambda e: self.ir("login"), "secundario"),
        ]

    def tela_recuperar(self):
        c = self.c
        self.texto_tela = "Recuperar senha. Digite seu celular ou CPF para receber um código por SMS."
        ident = self.campo("Celular, CPF ou usuário", teclado=ft.KeyboardType.TEXT)

        def enviar(e):
            if len((ident.value or "").strip()) < 3:
                self.avisar("Digite seu celular, CPF ou usuário.", "erro")
                return
            self.avisar("Se houver conta, um código foi enviado por SMS. (Demonstração: senha 123456)", "ok")

        return [
            ft.Row(controls=[ft.Container(content=self.txt("← Voltar", 15, True, c["primaria2"]),
                                          on_click=self.voltar, padding=6)]),
            self.titulo("Recuperar senha", "Vamos te ajudar a entrar de novo.", "🔑"),
            self.card([ident, self.botao("Enviar código", enviar)]),
            self.caixa_info("Também pode pedir ajuda a um parente, à cooperativa ou à associação.", "🤝"),
        ]

    # =================================================================
    # INÍCIO (muda conforme o tipo de conta)
    # =================================================================
    def atalho(self, emoji, nome, ao_clicar):
        return ft.Container(
            content=ft.Column(controls=[ft.Text(emoji, size=self.tam(30), text_align=ft.TextAlign.CENTER),
                                        ft.Text(nome, size=self.tam(13), color=self.c["texto"],
                                                weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)],
                              spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=self.c["card"], border=self.borda(), border_radius=16,
            padding=ft.Padding(left=4, top=12, right=4, bottom=12), expand=True, on_click=ao_clicar, ink=True)

    def tela_inicio(self):
        c = self.c
        u = self.usuario
        tipo = u["tipo"]
        primeiro = u["nome"].split()[0] if tipo in ("produtor", "comprador", "agronomo") else u["nome"]
        ir = self.ir

        atalhos = {
            "produtor": [("🛒", "Vender", lambda e: ir("anunciar_produto")),
                         ("🚜", "Máquinas", lambda e: ir("recursos", aba="Máquinas")),
                         ("🌾", "Terrenos", lambda e: ir("recursos", aba="Terras")),
                         ("👩‍🔬", "Agrônomo", lambda e: ir("agronomos"))],
            "comprador": [("🛒", "Comprar", lambda e: self.trocar_aba("mercado")),
                          ("🪶", "Indígenas", lambda e: self.trocar_aba("povos")),
                          ("📦", "Pedidos", lambda e: ir("pedidos")),
                          ("🤖", "Ajuda", lambda e: self.trocar_aba("ajuda"))],
            "empresa": [("🛒", "Comprar", lambda e: self.trocar_aba("mercado")),
                        ("📢", "Demanda", lambda e: ir("nova_demanda")),
                        ("🪶", "Indígenas", lambda e: self.trocar_aba("povos")),
                        ("📦", "Pedidos", lambda e: ir("pedidos"))],
            "ong": [("🤝", "Projetos", lambda e: ir("povos_parcerias")),
                    ("📢", "Demanda", lambda e: ir("nova_demanda")),
                    ("🌾", "Terras", lambda e: ir("recursos", aba="Terras")),
                    ("📦", "Pedidos", lambda e: ir("pedidos"))],
            "indigena": [("📤", "Publicar", lambda e: ir("povos_publicar")),
                         ("🪶", "Nossa área", lambda e: self.trocar_aba("povos")),
                         ("🤝", "Parcerias", lambda e: ir("povos_parcerias")),
                         ("👩‍🔬", "Agrônomo", lambda e: ir("agronomos"))],
            "agronomo": [("📋", "Pedidos", lambda e: ir("pedidos")),
                         ("🌾", "Terras", lambda e: ir("recursos", aba="Terras")),
                         ("🤖", "Assistente", lambda e: ir("assistente")),
                         ("👤", "Perfil", lambda e: ir("perfil"))],
        }[tipo]

        faixas = {
            "produtor": ("Seu produto pode chegar mais longe!",
                         "Restaurantes, mercados e escolas estão procurando o que você produz.",
                         "Ver quem quer comprar", lambda e: ir("mercado", aba="Demandas")),
            "comprador": ("Compre direto de quem produz",
                          "Mais fresco para você, mais dinheiro para o agricultor.",
                          "Ver produtos", lambda e: self.trocar_aba("mercado")),
            "empresa": ("Fornecedores locais para o seu negócio",
                        "Publique o que você precisa e receba ofertas de produtores da região.",
                        "Publicar demanda", lambda e: ir("nova_demanda")),
            "ong": ("Conecte comunidades a mercados justos",
                    "Apoie projetos indígenas e de agricultura familiar com transparência.",
                    "Ver projetos", lambda e: ir("povos_parcerias")),
            "indigena": ("Sua terra, sua cultura, sua renda",
                         "Publique produtos e histórias com autorização da comunidade. Taxa zero.",
                         "Publicar agora", lambda e: ir("povos_publicar")),
            "agronomo": ("Produtores precisam de você",
                         "Responda pedidos de ajuda e avalie terrenos parados.",
                         "Ver pedidos", lambda e: ir("pedidos")),
        }[tipo]

        meus = [p for p in self.db.pedidos if p["usuario"] == u["id"]]
        meus_anuncios = [p for p in self.db.produtos if p["vendedor"] == u["nome"]]
        self.texto_tela = (f"Olá, {primeiro}. Tela inicial. Atalhos: " + ", ".join(a[1] for a in atalhos) +
                           f". {faixas[0]}. {faixas[1]}")

        controles = [
            ft.Column(controls=[self.txt(f"Olá, {primeiro}! 👋", 25, True),
                                self.txt("Vamos fazer seu negócio crescer?", 15, cor=c["suave"])], spacing=2),
            ft.Row(controls=[self.atalho(*a) for a in atalhos], spacing=8),
            self.faixa(*faixas, indigena=(tipo == "indigena")),
            self.card(ft.Row(controls=[
                self.numero_card(str(len(meus_anuncios)), "anúncios"),
                self.numero_card(str(len(meus)), "pedidos"),
                self.numero_card(str(len([p for p in meus if p["status"].startswith("Aguard")])), "aguardando"),
            ], spacing=8), ao_clicar=lambda e: ir("pedidos"), padding=12),
        ]

        if tipo == "agronomo":
            controles.append(self.secao("Pedidos de ajuda dos produtores"))
            for s in self.db.solicitacoes_agro:
                controles.append(self.card_solicitacao(s))

        if tipo in ("produtor", "ong", "indigena"):
            controles.append(self.secao("Quem quer comprar", "Ver todas",
                                        lambda e: ir("mercado", aba="Demandas")))
            for d in self.db.demandas[:2]:
                controles.append(self.card_demanda(d))

        controles.append(self.secao("Produtos em destaque", "Ver todos", lambda e: self.trocar_aba("mercado")))
        controles.append(self.lista_em_pares([self.card_produto(p) for p in self.db.produtos[:4]]))

        controles.append(self.secao("Oportunidades"))
        oportunidades = [
            ("🚜", "Alugue equipamentos", "Use máquinas de outros produtores ou disponibilize as suas.",
             lambda e: ir("recursos", aba="Máquinas")),
            ("🌱", "Terras disponíveis", "Áreas paradas para aluguel barato ou parceria com divisão de lucro.",
             lambda e: ir("recursos", aba="Terras")),
            ("🪶", "Povos & Territórios", "Produtos, projetos e culturas dos povos indígenas.",
             lambda e: self.trocar_aba("povos")),
            ("👩‍🔬", "Fale com um agrônomo", "Especialistas para solo, pragas, irrigação e planejamento.",
             lambda e: ir("agronomos")),
        ]
        for emoji, tit, desc, acao in oportunidades:
            controles.append(self.card(ft.Row(controls=[
                ft.Text(emoji, size=self.tam(30)),
                ft.Column(controls=[self.txt(tit, 17, True), self.txt(desc, 14, cor=c["suave"])], spacing=2,
                          expand=True),
                self.txt("›", 26, True, c["primaria"]),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12), ao_clicar=acao))
        return controles

    def numero_card(self, numero, rotulo):
        return ft.Container(content=ft.Column(controls=[
            self.txt(numero, 22, True, self.c["primaria"], centro=True),
            self.txt(rotulo, 12, cor=self.c["suave"], centro=True)],
            spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, bgcolor=self.c["clara"], border_radius=12, padding=8)

    # =================================================================
    # BUSCA GERAL
    # =================================================================
    def tela_busca(self, termo=""):
        c = self.c
        t = sem_acento(termo).strip()
        self.texto_tela = f"Resultados da busca por {termo}."
        if not t:
            return [self.titulo("Busca", "Digite algo na barra de pesquisa acima."),
                    self.caixa_info("Exemplos: banana, trator, terreno, mel, solo.", "🔎")]

        def bate(*textos):
            return any(t in sem_acento(x) for x in textos)

        prods = [p for p in self.db.produtos if bate(p["nome"], p["categoria"], p["vendedor"], p["local"])]
        maqs = [m for m in self.db.maquinas if bate(m["nome"], m["desc"], m["local"])]
        terras = [x for x in self.db.terras if bate(x["titulo"], x["local"], x["condicao"], *x["sugestoes"])]
        ind = [i for i in self.db.prod_indigenas if bate(i["nome"], i["comunidade"], i["tipo"])]
        agro = [a for a in self.db.agronomos if bate(a["nome"], a["area"])]
        total = len(prods) + len(maqs) + len(terras) + len(ind) + len(agro)
        self.texto_tela += f" {total} resultados."

        controles = [self.titulo(f"Busca: “{termo}”", f"{total} resultado(s)", "🔎")]
        if prods:
            controles += [self.secao("Produtos"), self.lista_em_pares([self.card_produto(p) for p in prods])]
        if ind:
            controles += [self.secao("Povos & Territórios")] + [self.card_indigena(i) for i in ind]
        if maqs:
            controles += [self.secao("Máquinas")] + [self.card_maquina(m) for m in maqs]
        if terras:
            controles += [self.secao("Terras")] + [self.card_terra(x) for x in terras]
        if agro:
            controles += [self.secao("Agrônomos")] + [self.card_agronomo(a) for a in agro]
        if not total:
            controles.append(self.caixa_info("Nada encontrado. Tente outra palavra ou pergunte ao Assistente.",
                                             "🤔", "alerta"))
            controles.append(self.botao("🤖 Perguntar ao Assistente", lambda e: self.ir("assistente")))
        return controles

    # =================================================================
    # MERCADO
    # =================================================================
    def card_produto(self, p):
        c = self.c
        controles = [
            self.emoji_box(p["emoji"]),
            self.txt(p["nome"], 16, True),
            self.txt(p["vendedor"], 12, cor=c["suave"]),
            self.txt(f"{brl(p['preco'])} / {p['unidade']}", 16, True, c["primaria"]),
        ]
        if p.get("organico"):
            controles.insert(2, self.selo("🌿 Orgânico"))
        controles.append(self.botao("Ver produto", lambda e, i=p["id"]: self.ir("produto", pid=i), altura=44))
        return self.card(controles, padding=12, expandir=True)

    def card_demanda(self, d):
        c = self.c
        pode_atender = self.usuario["tipo"] in ("produtor", "ong", "indigena")
        controles = [
            ft.Row(controls=[self.selo("📢 " + d["tipo_comp"], c["alerta_fundo"], c["alerta"]),
                             ft.Container(expand=True), self.txt(d["data"], 12, cor=c["suave"])]),
            self.txt(f"{d['produto']} — {d['quantidade']}", 17, True),
            self.txt(f"{d['comprador']} • {d['local']}", 14, cor=c["suave"]),
            self.txt(f"💰 {d['preco']}", 15, True, c["primaria"]),
        ]
        if pode_atender:
            controles.append(self.botao("Quero fornecer", lambda e, dd=d: self.atender_demanda(dd), altura=46))
        return self.card(controles)

    def atender_demanda(self, d):
        self.registrar_pedido("Fornecimento", f"Oferta para {d['comprador']}",
                              f"{d['produto']} — {d['quantidade']}", None, d["comprador"])
        self.avisar(f"Oferta enviada para {d['comprador']}! Acompanhe em Pedidos.", "ok")

    def tela_mercado(self, aba="Ofertas"):
        c = self.c
        estado = {"aba": aba, "cat": "Todos"}
        tipo = self.usuario["tipo"]
        area = ft.Column(spacing=12)

        def montar(_=None):
            area.controls.clear()
            if estado["aba"] == "Ofertas":
                lista = [p for p in self.db.produtos
                         if estado["cat"] == "Todos" or p["categoria"] == estado["cat"]]
                area.controls.append(self.chips(["Todos"] + CATEGORIAS, estado, "cat", montar))
                if lista:
                    area.controls.append(self.lista_em_pares([self.card_produto(p) for p in lista]))
                else:
                    area.controls.append(self.caixa_info("Nenhum produto nessa categoria ainda.", "🌱", "alerta"))
            else:
                area.controls.append(self.caixa_info(
                    "Demandas são pedidos de compradores (restaurantes, mercados, escolas). "
                    "Produtor: toque em 'Quero fornecer'.", "📢"))
                for d in self.db.demandas:
                    area.controls.append(self.card_demanda(d))

        montar()
        acoes = []
        if tipo in ("produtor", "ong", "indigena"):
            acoes.append(self.botao("+ Anunciar produto", lambda e: self.ir("anunciar_produto"), expandir=True))
        if tipo in ("empresa", "ong", "comprador"):
            acoes.append(self.botao("📢 Publicar demanda", lambda e: self.ir("nova_demanda"),
                                    "secundario", expandir=True))

        self.texto_tela = ("Mercado. Venda e compre direto dos produtores. Abas: Ofertas e Demandas. "
                           f"Há {len(self.db.produtos)} produtos e {len(self.db.demandas)} demandas.")
        return [
            self.titulo("Mercado", "Venda e compre diretamente dos produtores.", "🛒"),
            ft.Container(content=ft.Row(controls=[
                ft.Column(controls=[self.txt("Encontrar produtos", 18, True, "#FFFFFF"),
                                    self.txt("Use o microfone do teclado para falar.", 14, cor="#FFFFFF")],
                          spacing=2, expand=True),
                ft.Container(content=ft.Text("🎙️", size=self.tam(26)), width=self.tam(54),
                             height=self.tam(54), border_radius=27, bgcolor=c["clara"],
                             alignment=ft.Alignment(0, 0), on_click=lambda e: self.avisar(
                                 "Toque na barra de busca e use o 🎤 do teclado do celular para falar.", "info")),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER), bgcolor=c["primaria2"], border_radius=18,
                padding=16),
            ft.Row(controls=acoes, spacing=8) if acoes else ft.Container(),
            self.chips(["Ofertas", "Demandas"], estado, "aba", montar),
            area,
        ]

    def tela_produto(self, pid=None):
        c = self.c
        p = self.db.achar("produtos", pid)
        if not p:
            return [self.caixa_info("Produto não encontrado.", "⚠️", "alerta")]
        empresa = self.usuario["tipo"] in ("empresa", "ong")
        estado = {"qtd": 10 if empresa else 1, "entrega": "Retirar no local"}
        total_txt = self.txt("", 22, True, c["primaria"])
        proposta = self.campo("Sua proposta de preço por " + p["unidade"] + " (opcional)", "Ex.: 3,00",
                              teclado=ft.KeyboardType.NUMBER)

        def atualizar():
            frete = 15.0 if estado["entrega"] == "Entrega (taxa R$ 15)" else 0.0
            total_txt.value = f"Total: {brl(estado['qtd'] * p['preco'] + frete)}"

        atualizar()

        def comprar(e):
            if self.usuario["nome"] == p["vendedor"]:
                self.avisar("Esse anúncio é seu.", "info")
                return
            if estado["qtd"] > p["estoque"]:
                self.avisar(f"Só há {p['estoque']} {p['unidade']} disponíveis.", "erro")
                return
            frete = 15.0 if estado["entrega"].startswith("Entrega") else 0.0
            self.registrar_pedido("Compra", p["nome"], f"{estado['qtd']} {p['unidade']} • {estado['entrega']}",
                                  estado["qtd"] * p["preco"] + frete, p["vendedor"])
            self.ir("pedidos")
            self.avisar("Pedido enviado ao produtor! Ele vai confirmar pelo app.", "ok")

        def propor(e):
            valor = para_numero(proposta.value)
            if not valor or valor <= 0:
                self.avisar("Digite um preço válido para a proposta.", "erro")
                return
            self.registrar_pedido("Proposta", p["nome"],
                                  f"{estado['qtd']} {p['unidade']} a {brl(valor)}/{p['unidade']}",
                                  estado["qtd"] * valor, p["vendedor"])
            self.ir("pedidos")
            self.avisar("Proposta enviada! Você será avisado quando o produtor responder.", "ok")

        self.texto_tela = (f"{p['nome']}. {brl(p['preco'])} por {p['unidade']}. Vendido por {p['vendedor']}, "
                           f"{p['local']}. {p['desc']} Escolha a quantidade e toque em Comprar.")
        return [
            self.emoji_box(p["emoji"], 70),
            ft.Row(controls=[ft.Container(content=self.txt(p["nome"], 25, True), expand=True)] +
                   ([self.selo("🌿 Orgânico")] if p["organico"] else [])),
            self.txt(f"{brl(p['preco'])} / {p['unidade']}", 22, True, c["primaria"]),
            self.card([
                self.info_linha("Produtor:", p["vendedor"]),
                self.info_linha("Local:", p["local"]),
                self.info_linha("Disponível:", f"{p['estoque']} {p['unidade']}"),
                self.info_linha("Categoria:", p["categoria"]),
                self.txt(p["desc"], 15, cor=c["suave"]),
            ]),
            self.card([
                self.txt("Quantidade", 17, True),
                self.contador(estado, "qtd", 1, 9999, 1, atualizar, f" {p['unidade']}"),
                self.txt("Como receber?", 17, True),
                self.chips(["Retirar no local", "Entrega (taxa R$ 15)"], estado, "entrega",
                           lambda _: atualizar()),
                total_txt,
                self.botao("Comprar agora", comprar),
            ]),
            self.card([self.txt("💬 Negociar", 17, True),
                       self.txt("Comprando em quantidade? Faça uma proposta.", 14, cor=c["suave"]),
                       proposta, self.botao("Enviar proposta", propor, "secundario")]),
        ]

    def tela_anunciar_produto(self):
        c = self.c
        estado = {"cat": CATEGORIAS[0], "un": "kg", "org": None}
        nome = self.campo("Nome do produto", "Ex.: Banana prata")
        preco = self.campo("Preço (R$)", "Ex.: 3,50", teclado=ft.KeyboardType.NUMBER)
        qtd = self.campo("Quantidade disponível", "Ex.: 100", teclado=ft.KeyboardType.NUMBER)
        desc = self.campo("Conte sobre o produto", "Como foi produzido, quando colheu…", multilinha=True)
        emojis = {"Frutas": "🍎", "Verduras": "🥬", "Raízes": "🥔", "Grãos": "🌽", "Mel e derivados": "🍯",
                  "Laticínios": "🧀", "Ovos e carnes": "🥚"}

        def publicar(e):
            v = para_numero(preco.value)
            q = para_numero(qtd.value)
            if len((nome.value or "").strip()) < 2:
                self.avisar("Digite o nome do produto.", "erro")
                return
            if not v or v <= 0:
                self.avisar("Digite um preço válido.", "erro")
                return
            if not q or q <= 0:
                self.avisar("Digite a quantidade disponível.", "erro")
                return
            self.db.produtos.insert(0, self.db._p(
                nome.value.strip(), emojis.get(estado["cat"], "🌱"), estado["cat"], v, estado["un"],
                self.usuario["nome"], self.usuario["cidade"], int(q), estado["org"] == "Sim",
                (desc.value or "").strip() or "Produto fresco do produtor."))
            self.trocar_aba("mercado")
            self.avisar("Produto publicado no Mercado! 🎉", "ok")

        self.texto_tela = ("Anunciar produto. Preencha o nome, a categoria, o preço, a unidade e a quantidade. "
                           "Depois toque em Publicar.")
        return [
            self.titulo("Anunciar produto", "Seu produto aparece para compradores da região.", "📤"),
            self.card([nome, self.txt("Categoria", 15, True), self.chips(CATEGORIAS, estado, "cat")]),
            self.card([preco, self.txt("Vendido por", 15, True), self.chips(UNIDADES, estado, "un"), qtd,
                       self.txt("É orgânico / sem agrotóxico?", 15, True),
                       self.chips(["Sim", "Não"], estado, "org")]),
            self.card([desc, self.botao("📷 Adicionar foto", lambda e: self.avisar(
                "Na versão para celular, a câmera abre aqui.", "info"), "claro")]),
            self.caixa_info("Dica: preços parecidos com os da sua região vendem mais rápido. Pergunte ao "
                            "Assistente se tiver dúvida.", "💡"),
            self.botao("Publicar produto ✓", publicar),
        ]

    def tela_nova_demanda(self):
        estado = {"freq": "Por semana"}
        produto = self.campo("O que você precisa comprar?", "Ex.: Tomate")
        qtd = self.campo("Quantidade", "Ex.: 80 kg")
        preco = self.campo("Preço que pode pagar (opcional)", "Ex.: até R$ 5,00/kg")

        def publicar(e):
            if len((produto.value or "").strip()) < 2 or len((qtd.value or "").strip()) < 1:
                self.avisar("Informe o produto e a quantidade.", "erro")
                return
            freq = "" if estado["freq"] == "Uma vez" else " " + estado["freq"].lower()
            self.db.demandas.insert(0, {
                "id": novo_id(), "comprador": self.usuario["nome"],
                "tipo_comp": PERFIS[self.usuario["tipo"]]["nome"].split(" /")[0],
                "produto": produto.value.strip(), "quantidade": qtd.value.strip() + freq,
                "preco": (preco.value or "").strip() or "A combinar", "local": self.usuario["cidade"],
                "data": datetime.now().strftime("%d/%m")})
            self.ir("mercado", aba="Demandas")
            self.avisar("Demanda publicada! Produtores da região vão te mandar ofertas.", "ok")

        self.texto_tela = "Publicar demanda. Diga o que você precisa comprar, a quantidade e com que frequência."
        return [
            self.titulo("Publicar demanda", "Diga o que precisa e receba ofertas de produtores.", "📢"),
            self.card([produto, qtd, self.txt("Com que frequência?", 15, True),
                       self.chips(["Uma vez", "Por semana", "Por mês"], estado, "freq"), preco]),
            self.botao("Publicar demanda ✓", publicar),
        ]

    # =================================================================
    # RECURSOS: MÁQUINAS E TERRAS
    # =================================================================
    def card_maquina(self, m):
        c = self.c
        return self.card([
            ft.Row(controls=[ft.Text(m["emoji"], size=self.tam(36)),
                             ft.Column(controls=[self.txt(m["nome"], 18, True),
                                                 self.txt(f"{m['dono']} • {m['local']}", 13, cor=c["suave"])],
                                       spacing=2, expand=True)],
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.txt(m["desc"], 14, cor=c["suave"]),
            ft.Row(controls=[self.txt(f"{brl(m['preco'])} / dia", 18, True, c["primaria"]),
                             ft.Container(expand=True)] + ([self.selo("👷 Com operador")] if m["operador"] else [])),
            self.botao("Tenho interesse", lambda e, i=m["id"]: self.ir("maquina", mid=i), altura=46),
        ])

    def card_terra(self, t):
        c = self.c
        if t["modalidade"] == "Parceria":
            valor = f"🤝 Parceria: dono fica com {t['parte_dono']}% do lucro"
        else:
            valor = f"💰 Aluguel: {brl(t['aluguel'])} / mês"
        return self.card([
            ft.Row(controls=[ft.Text("🌾", size=self.tam(34)),
                             ft.Column(controls=[self.txt(t["titulo"], 17, True),
                                                 self.txt(f"{t['local']} • {t['dono']}", 13, cor=c["suave"])],
                                       spacing=2, expand=True)],
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row(controls=[self.selo(t["condicao"], c["alerta_fundo"], c["alerta"]),
                             self.selo("💧 " + t["agua"])], wrap=True, spacing=6),
            self.txt("Pode dar: " + ", ".join(t["sugestoes"]), 14, cor=c["suave"]),
            self.txt(valor, 15, True, c["primaria"]),
            self.botao("Ver terreno", lambda e, i=t["id"]: self.ir("terra", tid=i), altura=46),
        ])

    def tela_recursos(self, aba="Máquinas"):
        c = self.c
        estado = {"aba": aba}
        area = ft.Column(spacing=12)

        def montar(_=None):
            area.controls.clear()
            if estado["aba"] == "Máquinas":
                area.controls += [self.card_maquina(m) for m in self.db.maquinas]
                area.controls.append(self.card([
                    self.txt("📣 Disponibilize seu equipamento", 17, True),
                    self.txt("Tem uma máquina que fica parada? Ganhe renda extra alugando para outros "
                             "produtores.", 14, cor=c["suave"]),
                    self.botao("+ Anunciar equipamento", lambda e: self.ir("anunciar_maquina")),
                ], fundo=c["clara"]))
            else:
                area.controls.append(self.caixa_info(
                    "Tem uma parte do terreno que acha que não serve? Outro produtor pode alugar barato ou "
                    "plantar em parceria e vender pelo Agro Money, dividindo o lucro.", "💡"))
                area.controls += [self.card_terra(t) for t in self.db.terras]
                area.controls.append(self.card([
                    self.txt("🌱 Tenho terra parada", 17, True),
                    self.txt("Anuncie e ganhe com uma área que hoje não rende nada.", 14, cor=c["suave"]),
                    self.botao("+ Anunciar terreno", lambda e: self.ir("anunciar_terra")),
                ], fundo=c["clara"]))

        montar()
        self.texto_tela = ("Recursos: máquinas e terras. Compartilhe recursos e reduza custos. Na aba Máquinas "
                           "você aluga equipamentos por dia. Na aba Terras você encontra áreas para aluguel ou "
                           "parceria.")
        return [
            self.titulo("Máquinas e Terras", "Compartilhe recursos e reduza custos.", "🚜"),
            self.chips(["Máquinas", "Terras"], estado, "aba", montar),
            area,
        ]

    def tela_maquina(self, mid=None):
        c = self.c
        m = self.db.achar("maquinas", mid)
        if not m:
            return [self.caixa_info("Equipamento não encontrado.", "⚠️", "alerta")]
        estado = {"dias": 1, "operador": "Sem operador"}
        data = self.campo("A partir de qual dia?", "Ex.: 25/11")
        total_txt = self.txt("", 22, True, c["primaria"])
        taxa_operador = 120.0

        def atualizar():
            extra = taxa_operador if estado["operador"] == "Com operador (+R$ 120/dia)" else 0.0
            total_txt.value = f"Total: {brl(estado['dias'] * (m['preco'] + extra))}"

        atualizar()

        def reservar(e):
            if len((data.value or "").strip()) < 4:
                self.avisar("Diga a partir de que dia você precisa.", "erro")
                return
            extra = taxa_operador if estado["operador"].startswith("Com") else 0.0
            self.registrar_pedido("Aluguel", m["nome"],
                                  f"{estado['dias']} dia(s) a partir de {data.value.strip()} • {estado['operador']}",
                                  estado["dias"] * (m["preco"] + extra), m["dono"])
            self.ir("pedidos")
            self.avisar("Pedido de aluguel enviado ao dono da máquina!", "ok")

        self.texto_tela = (f"{m['nome']}. {brl(m['preco'])} por dia. Dono: {m['dono']}, {m['local']}. "
                           f"{m['desc']} Escolha os dias e toque em Pedir aluguel.")
        controles = [
            self.emoji_box(m["emoji"], 70),
            self.txt(m["nome"], 25, True),
            self.txt(f"{brl(m['preco'])} / dia", 22, True, c["primaria"]),
            self.card([self.info_linha("Dono:", m["dono"]), self.info_linha("Local:", m["local"]),
                       self.txt(m["desc"], 15, cor=c["suave"])]),
            self.card([
                self.txt("Quantos dias?", 17, True),
                self.contador(estado, "dias", 1, 30, 1, atualizar, " dia(s)"),
                data,
            ] + ([self.txt("Precisa de operador?", 17, True),
                  self.chips(["Sem operador", "Com operador (+R$ 120/dia)"], estado, "operador",
                             lambda _: atualizar())] if m["operador"] else []) + [
                total_txt,
                self.botao("Pedir aluguel", reservar),
            ]),
            self.caixa_info("O pagamento só é liberado ao dono depois que você confirma que recebeu a máquina "
                            "funcionando.", "🛡️"),
        ]
        return controles

    def tela_anunciar_maquina(self):
        estado = {"op": "Não"}
        nome = self.campo("Qual equipamento?", "Ex.: Trator 75 cv")
        preco = self.campo("Preço por dia (R$)", "Ex.: 200", teclado=ft.KeyboardType.NUMBER)
        desc = self.campo("Descrição", "Estado de conservação, acessórios…", multilinha=True)

        def publicar(e):
            v = para_numero(preco.value)
            if len((nome.value or "").strip()) < 2 or not v or v <= 0:
                self.avisar("Informe o equipamento e um preço válido.", "erro")
                return
            self.db.maquinas.insert(0, self.db._m(
                nome.value.strip(), "🚜", v, "Diária", self.usuario["nome"], self.usuario["cidade"],
                estado["op"] == "Sim", (desc.value or "").strip() or "Equipamento disponível para aluguel."))
            self.ir("recursos", aba="Máquinas")
            self.avisar("Equipamento anunciado! Você será avisado quando alguém se interessar.", "ok")

        self.texto_tela = "Anunciar equipamento. Diga qual máquina, o preço por dia e se vai com operador."
        return [
            self.titulo("Anunciar equipamento", "Ganhe renda com a máquina parada.", "📣"),
            self.card([nome, preco, self.txt("Pode ir com operador?", 15, True),
                       self.chips(["Sim", "Não"], estado, "op"), desc]),
            self.botao("Publicar ✓", publicar),
        ]

    def tela_terra(self, tid=None):
        c = self.c
        t = self.db.achar("terras", tid)
        if not t:
            return [self.caixa_info("Terreno não encontrado.", "⚠️", "alerta")]
        estado = {"cultura": t["sugestoes"][0], "parte": float(t["parte_dono"] or 30)}
        producao = self.campo("Produção esperada (kg)", "Ex.: 5000", teclado=ft.KeyboardType.NUMBER,
                              valor="5000")
        preco = self.campo("Preço de venda por kg (R$)", "Ex.: 2,50", teclado=ft.KeyboardType.NUMBER,
                           valor="2,50")
        resultado = ft.Column(spacing=4)
        parte_txt = self.txt("", 15, True)

        def calcular(e=None):
            resultado.controls.clear()
            parte_txt.value = f"Parte do dono da terra: {int(estado['parte'])}%"
            kg = para_numero(producao.value) or 0
            pr = para_numero(preco.value) or 0
            receita = kg * pr
            dono = receita * estado["parte"] / 100
            resultado.controls += [
                self.info_linha("Venda total:", brl(receita)),
                self.info_linha("Dono da terra:", brl(dono)),
                self.info_linha("Quem planta:", brl(receita - dono)),
            ]
            if e is not None:
                self.page.update()

        def mudar_parte(e):
            estado["parte"] = float(e.control.value)
            calcular(e)

        producao.on_change = calcular
        preco.on_change = calcular
        calcular()

        def propor(e):
            if t["modalidade"] == "Aluguel":
                self.registrar_pedido("Parceria", t["titulo"], f"Aluguel mensal • cultura: {estado['cultura']}",
                                      t["aluguel"], t["dono"])
            else:
                self.registrar_pedido("Parceria", t["titulo"],
                                      f"Parceria {int(estado['parte'])}% para o dono • cultura: {estado['cultura']}",
                                      None, t["dono"])
            self.ir("pedidos")
            self.avisar("Proposta enviada ao dono do terreno!", "ok")

        def pedir_avaliacao(e):
            self.registrar_pedido("Consulta", "Avaliação de terreno", f"{t['titulo']} • {t['local']}", None,
                                  "Agrônomo da região")
            self.avisar("Pedido de avaliação enviado a um agrônomo.", "ok")

        self.texto_tela = (f"{t['titulo']} em {t['local']}. Condição: {t['condicao']}. Água: {t['agua']}. "
                           f"Pode dar: {', '.join(t['sugestoes'])}. {t['desc']}")
        controles = [
            self.emoji_box("🌾", 64),
            self.txt(t["titulo"], 24, True),
            self.card([
                self.info_linha("Dono:", t["dono"]),
                self.info_linha("Local:", t["local"]),
                self.info_linha("Tamanho:", f"{t['hectares']:g} hectare(s)"),
                self.info_linha("Condição:", t["condicao"]),
                self.info_linha("Água:", t["agua"]),
                self.txt(t["desc"], 15, cor=c["suave"]),
            ]),
            self.card([self.txt("O que plantar?", 17, True),
                       self.chips(t["sugestoes"], estado, "cultura")]),
        ]
        if t["modalidade"] == "Aluguel":
            controles.append(self.card([
                self.txt("💰 Aluguel", 17, True),
                self.txt(f"{brl(t['aluguel'])} por mês", 22, True, c["primaria"]),
                self.txt("Você planta, colhe e vende pelo Agro Money. O lucro é todo seu.", 14, cor=c["suave"]),
            ]))
        else:
            controles.append(self.card([
                self.txt("🤝 Calculadora de parceria", 17, True),
                self.txt("Você planta, o app vende, e o lucro é dividido automaticamente.", 14, cor=c["suave"]),
                producao, preco, parte_txt,
                ft.Slider(min=10, max=60, divisions=10, value=estado["parte"], label="{value}%",
                          on_change=mudar_parte),
                ft.Container(content=resultado, bgcolor=c["clara"], border_radius=12, padding=12),
            ]))
        controles += [
            self.botao("Propor " + ("aluguel" if t["modalidade"] == "Aluguel" else "parceria"), propor),
            self.botao("👩‍🔬 Pedir avaliação de um agrônomo", pedir_avaliacao, "secundario"),
        ]
        return controles

    def tela_anunciar_terra(self):
        estado = {"cond": None, "mod": "Parceria", "agro": "Sim", "agua": None}
        area = self.campo("Tamanho (hectares)", "Ex.: 1,5", teclado=ft.KeyboardType.NUMBER)
        valor = self.campo("Aluguel por mês (R$) ou sua parte na parceria (%)", "Ex.: 200 ou 30",
                           teclado=ft.KeyboardType.NUMBER)
        desc = self.campo("Conte sobre a área", "Onde fica, acesso, o que tinha antes…", multilinha=True)
        sugestoes = {"Inclinado": ["Café", "Frutas", "Agrofloresta"],
                     "Pedregoso": ["Palma", "Mandioca", "Sisal"],
                     "Encharcado": ["Inhame", "Taioba", "Arroz"],
                     "Sem água": ["Palma", "Sorgo", "Feijão de corda"],
                     "Não sei": ["Avaliar com agrônomo"]}

        def publicar(e):
            ha = para_numero(area.value)
            v = para_numero(valor.value)
            if not ha or ha <= 0:
                self.avisar("Informe o tamanho da área.", "erro")
                return
            if not estado["cond"]:
                self.avisar("Escolha como é a área.", "erro")
                return
            if not v or v <= 0:
                self.avisar("Informe o valor do aluguel ou sua parte (%).", "erro")
                return
            parceria = estado["mod"] == "Parceria"
            if parceria and v > 90:
                self.avisar("Na parceria, sua parte deve ser no máximo 90%.", "erro")
                return
            self.db.terras.insert(0, self.db._t(
                f"Área de {ha:g} hectare(s)", ha, self.usuario["cidade"], estado["cond"],
                estado["agua"] or "Não informado", estado["mod"], int(v) if parceria else 0,
                0 if parceria else v, self.usuario["nome"], sugestoes[estado["cond"]],
                (desc.value or "").strip() or "Área disponível."))
            if estado["agro"] == "Sim":
                self.registrar_pedido("Consulta", "Avaliação grátis do terreno", f"{ha:g} ha • {estado['cond']}",
                                      None, "Agrônomo da região")
            self.ir("recursos", aba="Terras")
            self.avisar("Terreno anunciado! " + ("Um agrônomo vai avaliar a área." if estado["agro"] == "Sim"
                                                 else ""), "ok")

        self.texto_tela = ("Anunciar terreno. Diga o tamanho, como é a área, se tem água, e se quer aluguel ou "
                           "parceria.")
        return [
            self.titulo("Anunciar terreno", "Transforme área parada em renda.", "🌱"),
            self.card([area, self.txt("Como é a área?", 15, True),
                       self.chips(list(sugestoes.keys()), estado, "cond"),
                       self.txt("Tem água?", 15, True),
                       self.chips(["Poço", "Rio/riacho", "Cisterna", "Encanada", "Não tem"], estado, "agua")]),
            self.card([self.txt("Como quer ganhar?", 15, True),
                       self.chips(["Aluguel", "Parceria"], estado, "mod"), valor,
                       self.caixa_info("Parceria: outro produtor planta, vende pelo app e você recebe uma parte "
                                       "do lucro sem gastar nada.", "🤝")]),
            self.card([desc, self.txt("Quer avaliação grátis de um agrônomo?", 15, True),
                       self.chips(["Sim", "Não"], estado, "agro")]),
            self.botao("Publicar terreno ✓", publicar),
        ]

    # =================================================================
    # POVOS & TERRITÓRIOS (área indígena)
    # =================================================================
    def card_indigena(self, i):
        c = self.c
        return self.card([
            ft.Row(controls=[ft.Text(i["emoji"], size=self.tam(36)),
                             ft.Column(controls=[self.txt(i["nome"], 17, True),
                                                 self.txt(i["comunidade"], 13, cor=c["suave"])],
                                       spacing=2, expand=True)],
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.selo("✔ Venda autorizada pela comunidade", c["indigena_fundo"], c["indigena"]),
            self.txt(f"{brl(i['preco'])} / {i['unidade']}", 17, True, c["indigena"]),
            self.botao("Ver e comprar", lambda e, x=i["id"]: self.ir("povos_produto", iid=x), "indigena",
                       altura=46),
        ], cor_borda=c["indigena"] if not self.alto_contraste else None)

    def tela_povos(self):
        c = self.c
        indigena = self.usuario["tipo"] == "indigena"
        self.texto_tela = ("Povos e Territórios. Uma área dedicada à valorização cultural e às iniciativas "
                           "indígenas. Aqui você encontra produtos das comunidades, cultura e conhecimentos, e "
                           "parcerias justas. Tudo divulgado com autorização das próprias comunidades.")
        controles = [
            self.titulo("Povos & Territórios", "Uma área dedicada à valorização cultural e às iniciativas "
                                               "indígenas.", "🪶"),
            self.faixa("Conheça. Valorize. Apoie.",
                       "Produtos, arte, conhecimentos e histórias divulgados com autorização das próprias "
                       "comunidades. A renda vai direto para a comunidade — taxa zero.",
                       "Publicar da minha comunidade" if indigena else None,
                       (lambda e: self.ir("povos_publicar")) if indigena else None, indigena=True),
        ]
        menus = [
            ("🧺", "Produtos das comunidades", "Artesanato, alimentos e produtos tradicionais vendidos de acordo "
                                              "com as decisões e regras da comunidade.", None),
            ("🎨", "Cultura e conhecimentos", "Línguas, tradições, história e arte apresentadas pelos próprios "
                                             "povos.", lambda e: self.ir("povos_cultura")),
            ("🤝", "Parcerias justas", "Conexão direta com compradores e apoio a projetos econômicos definidos "
                                      "pelas comunidades.", lambda e: self.ir("povos_parcerias")),
        ]
        for emoji, tit, desc, acao in menus[1:]:
            controles.append(self.card(ft.Row(controls=[
                ft.Text(emoji, size=self.tam(30)),
                ft.Column(controls=[self.txt(tit, 17, True), self.txt(desc, 14, cor=c["suave"])], spacing=2,
                          expand=True),
                self.txt("›", 26, True, c["indigena"])],
                vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12), ao_clicar=acao,
                fundo=c["indigena_fundo"]))
        controles.append(self.secao(menus[0][0] + " " + menus[0][1]))
        controles.append(self.txt(menus[0][2], 14, cor=c["suave"]))
        controles += [self.card_indigena(i) for i in self.db.prod_indigenas]
        controles.append(self.caixa_info(
            "Respeito: não copie grafismos, cantos ou conhecimentos tradicionais sem permissão. Conhecimento "
            "sagrado ou restrito não é publicado aqui.", "🛡️", "indigena"))
        return controles

    def tela_povos_produto(self, iid=None):
        c = self.c
        i = self.db.achar("prod_indigenas", iid)
        if not i:
            return [self.caixa_info("Produto não encontrado.", "⚠️", "alerta")]
        estado = {"qtd": 1}
        total = self.txt("", 22, True, c["indigena"])

        def atualizar():
            total.value = f"Total: {brl(estado['qtd'] * i['preco'])}"

        atualizar()

        def comprar(e):
            self.registrar_pedido("Compra", i["nome"], f"{estado['qtd']} {i['unidade']} • Povos & Territórios",
                                  estado["qtd"] * i["preco"], i["comunidade"])
            self.ir("pedidos")
            self.avisar("Pedido enviado! 100% do valor vai para a comunidade.", "ok")

        self.texto_tela = (f"{i['nome']}, da {i['comunidade']}. {brl(i['preco'])} por {i['unidade']}. "
                           f"{i['desc']} Venda autorizada pela comunidade.")
        return [
            self.emoji_box(i["emoji"], 70, c["indigena_fundo"]),
            self.txt(i["nome"], 25, True),
            self.selo("✔ Venda autorizada pela comunidade", c["indigena_fundo"], c["indigena"]),
            self.txt(f"{brl(i['preco'])} / {i['unidade']}", 22, True, c["indigena"]),
            self.card([self.info_linha("Comunidade:", i["comunidade"]), self.info_linha("Tipo:", i["tipo"]),
                       self.txt(i["desc"], 15, cor=c["suave"])]),
            self.card([self.txt("Quantidade", 17, True),
                       self.contador(estado, "qtd", 1, 500, 1, atualizar, f" {i['unidade']}"),
                       total, self.botao("Comprar da comunidade", comprar, "indigena")]),
            self.caixa_info("Taxa zero: 100% do valor vai para a comunidade ou associação.", "💚", "indigena"),
        ]

    def tela_povos_cultura(self):
        c = self.c
        self.texto_tela = "Cultura e conhecimentos. " + " ".join(
            f"{x['titulo']}. {x['texto']}" for x in self.db.culturas)
        controles = [self.titulo("Cultura e conhecimentos", "Apresentados pelos próprios povos.", "🎨")]
        for x in self.db.culturas:
            controles.append(self.card([
                ft.Row(controls=[ft.Text(x["emoji"], size=self.tam(28)),
                                 ft.Container(content=self.txt(x["titulo"], 18, True), expand=True)]),
                self.txt(x["texto"], 15),
                self.txt("Por: " + x["autor"], 13, cor=c["indigena"], italico=True),
                ft.Container(content=self.txt("🔊 Ouvir", 14, True, c["indigena"]), padding=6,
                             on_click=lambda e, tx=x["texto"]: self.ler(tx)),
            ], fundo=c["indigena_fundo"]))
        if self.usuario["tipo"] == "indigena":
            controles.append(self.botao("+ Compartilhar história ou conhecimento",
                                        lambda e: self.ir("povos_publicar", tipo_pub="Cultura"), "indigena"))
        return controles

    def tela_povos_parcerias(self):
        c = self.c
        estado = {"valor": None}
        self.texto_tela = "Parcerias justas. Apoie projetos econômicos definidos pelas próprias comunidades."
        controles = [self.titulo("Parcerias justas", "Projetos definidos pelas próprias comunidades.", "🤝")]
        for p in self.db.projetos:
            pct = min(1.0, p["arrecadado"] / p["meta"])
            controles.append(self.card([
                ft.Row(controls=[ft.Text(p["emoji"], size=self.tam(30)),
                                 ft.Column(controls=[self.txt(p["titulo"], 17, True),
                                                     self.txt(p["comunidade"], 13, cor=c["suave"])],
                                           spacing=2, expand=True)]),
                self.txt(p["desc"], 14, cor=c["suave"]),
                ft.ProgressBar(value=pct, color=c["indigena"], bgcolor=c["indigena_fundo"], bar_height=10),
                self.txt(f"{brl(p['arrecadado'])} de {brl(p['meta'])} ({int(pct * 100)}%)", 14, True,
                         c["indigena"]),
                self.chips(["R$ 20", "R$ 50", "R$ 100", "R$ 500"], estado, "valor", cor=c["indigena"]),
                self.botao("Apoiar projeto", lambda e, pp=p: self.apoiar(pp, estado), "indigena", altura=46),
            ]))
        controles.append(self.caixa_info("Empresas e restaurantes também podem fechar compras contínuas "
                                         "direto com as associações. Toque em 'Ver e comprar' nos produtos.",
                                         "🏪", "indigena"))
        return controles

    def apoiar(self, projeto, estado):
        if not estado.get("valor"):
            self.avisar("Escolha um valor para apoiar.", "erro")
            return
        valor = para_numero(estado["valor"])
        projeto["arrecadado"] += valor
        self.registrar_pedido("Apoio", projeto["titulo"], projeto["comunidade"], valor, projeto["comunidade"],
                              "Confirmado")
        estado["valor"] = None
        self.avisar(f"Obrigado! Você apoiou com {brl(valor)}. 💚", "ok")

    def tela_povos_publicar(self, tipo_pub="Produto"):
        c = self.c
        if self.usuario["tipo"] != "indigena":
            self.texto_tela = "Esta área é só para contas de comunidades indígenas."
            return [self.titulo("Publicar", None, "🪶"),
                    self.caixa_info("Somente contas de comunidades e associações indígenas podem publicar "
                                    "nesta área. Isso protege as comunidades e a sua cultura.", "🛡️", "indigena"),
                    self.botao("Voltar para Povos", lambda e: self.trocar_aba("povos"), "indigena")]

        estado = {"tipo": tipo_pub, "cat": "Artesanato", "un": "unidade"}
        nome = self.campo("Nome do produto ou título", "Ex.: Cesto trançado")
        preco = self.campo("Preço (R$) — só para produtos", "Ex.: 80", teclado=ft.KeyboardType.NUMBER)
        texto = self.campo("História / descrição", "Conte como é feito, quem faz, o que significa…",
                           multilinha=True)
        autorizado = ft.Checkbox(value=False)
        sem_sagrado = ft.Checkbox(value=False)

        def publicar(e):
            if len((nome.value or "").strip()) < 2:
                self.avisar("Digite o nome ou título.", "erro")
                return
            if not autorizado.value or not sem_sagrado.value:
                self.avisar("Confirme a autorização da comunidade e que não há conhecimento restrito.", "erro")
                return
            if estado["tipo"] == "Produto":
                v = para_numero(preco.value)
                if not v or v <= 0:
                    self.avisar("Digite um preço válido.", "erro")
                    return
                emoji = {"Artesanato": "🧺", "Alimento": "🥣", "Arte": "🎨"}.get(estado["cat"], "🪶")
                self.db.prod_indigenas.insert(0, self.db._i(
                    nome.value.strip(), emoji, v, estado["un"], self.usuario["nome"], estado["cat"],
                    (texto.value or "").strip() or "Produto da comunidade."))
                self.trocar_aba("povos")
                self.avisar("Produto publicado com autorização da comunidade! 🪶", "ok")
            else:
                if len((texto.value or "").strip()) < 10:
                    self.avisar("Escreva a história (ou grave em áudio).", "erro")
                    return
                self.db.culturas.insert(0, {"titulo": nome.value.strip(), "emoji": "📖",
                                            "autor": self.usuario["nome"], "texto": texto.value.strip()})
                self.ir("povos_cultura")
                self.avisar("História compartilhada! Obrigado por ensinar o Brasil. 🪶", "ok")

        self.texto_tela = ("Publicar da minha comunidade. Escolha produto ou cultura, preencha e confirme que a "
                           "comunidade autorizou.")
        return [
            self.titulo("Publicar da comunidade", "Só é publicado com autorização da comunidade.", "📤"),
            self.card([self.txt("O que vai publicar?", 15, True),
                       self.chips(["Produto", "Cultura"], estado, "tipo", cor=c["indigena"]),
                       nome,
                       self.txt("Tipo (para produtos)", 15, True),
                       self.chips(["Artesanato", "Alimento", "Arte"], estado, "cat", cor=c["indigena"]),
                       preco,
                       self.chips(["unidade", "kg", "litro"], estado, "un", cor=c["indigena"]),
                       texto,
                       self.botao("🎙️ Gravar em áudio", lambda e: self.avisar(
                           "Use o 🎤 do teclado para ditar o texto. Gravação de áudio entra na versão final.",
                           "info"), "claro")]),
            self.card([
                ft.Row(controls=[autorizado, ft.Container(content=self.txt(
                    "A comunidade/associação autorizou esta publicação.", 14), expand=True)]),
                ft.Row(controls=[sem_sagrado, ft.Container(content=self.txt(
                    "Não contém conhecimento sagrado ou restrito.", 14), expand=True)]),
            ], fundo=c["indigena_fundo"]),
            self.botao("Publicar ✓", publicar, "indigena"),
        ]

    # =================================================================
    # AJUDA: ASSISTENTE IA, AGRÔNOMOS, ÁUDIO
    # =================================================================
    def tela_ajuda(self):
        c = self.c
        self.texto_tela = ("Assistência e IA. Tecnologia que ajuda sem complicar. Opções: Assistente Agro, "
                           "Fale com um agrônomo, Ajuda por áudio e Perguntas frequentes.")
        faqs = [
            ("Como vendo meu produto?", "Vá em Mercado e toque em '+ Anunciar produto'. Preencha nome, preço e "
                                        "quantidade. Pronto!"),
            ("É seguro pagar pelo app?", "O dinheiro fica guardado e só é liberado ao vendedor quando você "
                                         "confirma que recebeu. (Na demonstração não há pagamento real.)"),
            ("Não sei ler bem. Consigo usar?", "Sim! Toque em 🔊 no topo para ouvir a tela e use o 🎤 do "
                                               "teclado para falar em vez de escrever."),
            ("Como funciona a parceria de terra?", "Quem tem terra parada anuncia. Outro produtor planta e "
                                                   "vende pelo app. O lucro é dividido na porcentagem "
                                                   "combinada."),
        ]
        lista_faq = ft.Column(spacing=8)
        for pergunta, resposta in faqs:
            resp_txt = self.txt(resposta, 14, cor=c["suave"])
            resp_txt.visible = False

            def alternar(e, r=resp_txt):
                r.visible = not r.visible
                self.page.update()

            lista_faq.controls.append(self.card([self.txt("❓ " + pergunta, 15, True), resp_txt],
                                                ao_clicar=alternar, padding=12))

        return [
            self.titulo("Assistência & IA", "Tecnologia que ajuda sem complicar.", "🤖"),
            ft.Container(content=ft.Row(controls=[
                ft.Column(controls=[self.txt("🔊 Modo acessível", 18, True, "#FFFFFF"),
                                    self.txt("Ouça instruções e a tela em voz alta.", 14, cor="#FFFFFF")],
                          spacing=2, expand=True),
                ft.Container(content=ft.Text("▶️", size=self.tam(24)), width=self.tam(54), height=self.tam(54),
                             border_radius=27, bgcolor=c["clara"], alignment=ft.Alignment(0, 0),
                             on_click=self.ouvir_tela)], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=c["primaria2"], border_radius=18, padding=16),
            self.card([self.txt("🤖 Assistente Agro", 18, True),
                       self.txt("Pergunte sobre plantio, pragas, solo, água, preço ou como usar o app.", 14,
                                cor=c["suave"]),
                       self.botao("Conversar com o assistente", lambda e: self.ir("assistente"))]),
            self.card([self.txt("👩‍🔬 Fale com um agrônomo", 18, True),
                       self.txt("Especialistas para solo, pragas, irrigação e planejamento.", 14, cor=c["suave"]),
                       self.botao("Encontrar especialista", lambda e: self.ir("agronomos"))]),
            self.card([self.txt("🎧 Ajuda por áudio", 18, True),
                       self.txt("Instruções faladas para quem tem dificuldade de leitura.", 14, cor=c["suave"]),
                       self.botao("Ouvir instruções", lambda e: self.ler(
                           "Bem-vindo ao Agro Money. Embaixo da tela tem cinco botões: Início, Mercado, "
                           "Recursos, Povos e Ajuda. No Mercado você compra e vende. Em Recursos você aluga "
                           "máquinas e terrenos. Em Povos fica a área indígena. Em Ajuda tem o assistente e os "
                           "agrônomos. Toque no alto-falante no topo para ouvir qualquer tela."), "secundario")]),
            self.secao("Perguntas frequentes"),
            lista_faq,
        ]

    def ler(self, texto):
        if falar_em_voz(texto):
            self.avisar("Lendo em voz alta…", "info")
        else:
            self.avisar("Para ouvir no celular, ative o TalkBack ou 'Selecionar para falar'. No computador: "
                        "pip install pyttsx3", "info")

    def tela_assistente(self):
        c = self.c
        if not self.chat:
            self.chat.append(("ia", "Olá! Sou o Assistente Agro 🌱. Pode me perguntar sobre plantio, pragas, "
                                    "solo, água, preços, máquinas, terrenos ou como usar o app."))
        conversa = ft.Column(spacing=10)
        entrada = self.campo("Escreva ou fale sua pergunta", "Ex.: Como melhorar meu plantio?")

        def bolha(quem, texto):
            eu = quem == "eu"
            return ft.Row(controls=[ft.Container(
                content=self.txt(texto, 15, cor="#FFFFFF" if eu else c["texto"]),
                bgcolor=c["primaria2"] if eu else c["card"],
                border=None if eu else self.borda(),
                border_radius=16, padding=12, width=300)],
                alignment=ft.MainAxisAlignment.END if eu else ft.MainAxisAlignment.START)

        def montar():
            conversa.controls.clear()
            for quem, texto in self.chat[-20:]:
                conversa.controls.append(bolha(quem, texto))

        def enviar(e=None, texto=None):
            pergunta = (texto or entrada.value or "").strip()
            if not pergunta:
                return
            self.chat.append(("eu", pergunta))
            self.chat.append(("ia", responder_ia(pergunta, self.usuario["tipo"])))
            entrada.value = ""
            montar()
            self.texto_tela = self.chat[-1][1]
            self.page.update()

        entrada.on_submit = enviar
        montar()
        self.texto_tela = self.chat[-1][1]
        sugestoes = ["Como combater pragas?", "Meu solo é fraco", "Como vender melhor?",
                     "Terreno inclinado serve?", "Como pegar crédito?"]
        return [
            self.titulo("Assistente Agro", "Respostas rápidas para o dia a dia.", "🤖"),
            self.caixa_info("Respostas de orientação geral. Para casos sérios, fale com um agrônomo.", "ℹ️",
                            "alerta"),
            conversa,
            ft.Row(controls=[ft.Container(
                content=self.txt(s, 13, True, c["primaria"]), bgcolor=c["clara"], border_radius=16,
                border=self.borda(c["primaria"]), padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                on_click=lambda e, s=s: enviar(texto=s), ink=True) for s in sugestoes],
                wrap=True, spacing=8, run_spacing=8),
            entrada,
            ft.Row(controls=[self.botao("Perguntar ➤", enviar, expandir=True),
                             self.botao("🔊 Ouvir", lambda e: self.ler(self.chat[-1][1]), "secundario")],
                   spacing=8),
            self.botao("👩‍🔬 Falar com um agrônomo de verdade", lambda e: self.ir("agronomos"), "claro"),
        ]

    def card_agronomo(self, a):
        c = self.c
        return self.card(ft.Row(controls=[
            ft.Container(content=ft.Text(a["emoji"], size=self.tam(30)), width=self.tam(58),
                         height=self.tam(58), border_radius=29, bgcolor=c["clara"], alignment=ft.Alignment(0, 0)),
            ft.Column(controls=[self.txt(a["nome"], 17, True), self.txt(a["area"], 14, True, c["primaria2"]),
                                self.txt(f"⭐ {a['nota']:.1f} • {a['atendimentos']} atendimentos • {a['local']}",
                                         12, cor=c["suave"]),
                                self.selo(a["preco"])], spacing=3, expand=True),
            self.txt("›", 26, True, c["primaria"]),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            ao_clicar=lambda e, i=a["id"]: self.ir("agronomo", aid=i))

    def tela_agronomos(self):
        estado = {"filtro": "Todos"}
        area = ft.Column(spacing=10)
        filtros = {"Todos": "", "Solo": "solo", "Pragas": "praga", "Irrigação": "irriga",
                   "Agroecologia": "agroecologia", "Vendas": "venda"}

        def montar(_=None):
            area.controls.clear()
            chave = filtros.get(estado["filtro"], "")
            lista = [a for a in self.db.agronomos if chave in sem_acento(a["area"])]
            area.controls += [self.card_agronomo(a) for a in lista] or [
                self.caixa_info("Nenhum especialista nessa área ainda.", "🔎", "alerta")]

        montar()
        self.texto_tela = "Agrônomos especialistas. Escolha um especialista para pedir ajuda. " + ", ".join(
            f"{a['nome']}, {a['area']}" for a in self.db.agronomos)
        return [
            self.titulo("Fale com um agrônomo", "Especialistas para resolver problemas da sua terra.", "👩‍🔬"),
            self.chips(list(filtros.keys()), estado, "filtro", montar),
            area,
        ]

    def tela_agronomo(self, aid=None):
        c = self.c
        a = self.db.achar("agronomos", aid)
        if not a:
            return [self.caixa_info("Especialista não encontrado.", "⚠️", "alerta")]
        estado = {"problema": None, "forma": "Vídeo"}
        texto = self.campo("Descreva o problema", "Ex.: folhas amarelas com manchas pretas", multilinha=True)

        def solicitar(e):
            if not estado["problema"]:
                self.avisar("Escolha o tipo de problema.", "erro")
                return
            if len((texto.value or "").strip()) < 5:
                self.avisar("Conte um pouco sobre o problema (pode usar o 🎤 do teclado).", "erro")
                return
            self.registrar_pedido("Consulta", f"{a['nome']} — {estado['problema']}",
                                  f"{estado['forma']} • {texto.value.strip()[:60]}", None, a["nome"])
            self.db.solicitacoes_agro.insert(0, {
                "id": novo_id(), "produtor": self.usuario["nome"], "problema": estado["problema"],
                "forma": estado["forma"], "texto": texto.value.strip(), "status": "Nova",
                "data": datetime.now().strftime("%d/%m")})
            self.ir("pedidos")
            self.avisar(f"Pedido enviado para {a['nome']}! Resposta em até 24 horas.", "ok")

        self.texto_tela = (f"{a['nome']}, especialista em {a['area']}. Nota {a['nota']}. {a['bio']} "
                           f"Preço: {a['preco']}. Escolha o problema, descreva e toque em Pedir ajuda.")
        return [
            ft.Row(controls=[ft.Container(content=ft.Text(a["emoji"], size=self.tam(44)), width=self.tam(84),
                                          height=self.tam(84), border_radius=42, bgcolor=c["clara"],
                                          alignment=ft.Alignment(0, 0)),
                             ft.Column(controls=[self.txt(a["nome"], 22, True),
                                                 self.txt(a["area"], 15, True, c["primaria2"]),
                                                 self.txt(f"⭐ {a['nota']:.1f} • {a['atendimentos']} atendimentos",
                                                          13, cor=c["suave"])], spacing=2, expand=True)],
                   vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
            self.card([self.txt(a["bio"], 15), self.info_linha("Registro:", a["registro"]),
                       self.info_linha("Atende em:", a["local"]), self.info_linha("Valor:", a["preco"])]),
            self.card([
                self.txt("Qual é o problema?", 17, True),
                self.chips(["Pragas", "Doenças", "Solo", "Água", "Terreno parado", "Planejamento"], estado,
                           "problema"),
                texto,
                self.botao("📷 Enviar foto da planta", lambda e: self.avisar(
                    "Na versão para celular, a câmera abre aqui.", "info"), "claro"),
                self.txt("Como prefere ser atendido?", 17, True),
                self.chips(["Vídeo", "Ligação", "Áudio", "Visita"], estado, "forma"),
                self.botao("Pedir ajuda ✓", solicitar),
            ]),
        ]

    def card_solicitacao(self, s):
        c = self.c

        def aceitar(e, ss=s):
            ss["status"] = "Aceita"
            self.avisar(f"Você aceitou o pedido de {ss['produtor']}. Entre em contato pelo app.", "ok")

        controles = [
            ft.Row(controls=[self.selo(s["problema"]), self.selo(s["forma"], c["alerta_fundo"], c["alerta"]),
                             ft.Container(expand=True), self.txt(s["data"], 12, cor=c["suave"])]),
            self.txt(s["produtor"], 16, True),
            self.txt(s["texto"], 14, cor=c["suave"]),
        ]
        if s["status"] == "Nova":
            controles.append(self.botao("Aceitar atendimento", aceitar, altura=44))
        else:
            controles.append(self.txt("✅ " + s["status"], 15, True, c["primaria"]))
        return self.card(controles)

    # =================================================================
    # PEDIDOS E PERFIL
    # =================================================================
    def registrar_pedido(self, tipo, titulo, detalhe, valor, contraparte, status="Aguardando resposta"):
        self.db.pedidos.insert(0, {"id": novo_id(), "usuario": self.usuario["id"], "tipo": tipo,
                                   "titulo": titulo, "detalhe": detalhe, "valor": valor,
                                   "contraparte": contraparte, "status": status, "data": agora()})

    def tela_pedidos(self):
        c = self.c
        estado = {"f": "Todos"}
        area = ft.Column(spacing=10)
        icones = {"Compra": "🛒", "Proposta": "💬", "Aluguel": "🚜", "Parceria": "🤝", "Consulta": "👩‍🔬",
                  "Apoio": "💚", "Fornecimento": "📦"}
        grupos = {"Todos": None, "Compras": ("Compra", "Proposta", "Fornecimento"), "Aluguéis": ("Aluguel",),
                  "Parcerias": ("Parceria", "Apoio"), "Consultas": ("Consulta",)}

        def cancelar(p):
            p["status"] = "Cancelado"
            self.avisar("Pedido cancelado.", "info")

        def montar(_=None):
            area.controls.clear()
            meus = [p for p in self.db.pedidos if p["usuario"] == self.usuario["id"]]
            g = grupos[estado["f"]]
            if g:
                meus = [p for p in meus if p["tipo"] in g]
            if not meus:
                area.controls.append(self.caixa_info("Nada por aqui ainda. Explore o Mercado e os Recursos!",
                                                     "📭", "alerta"))
            for p in meus:
                cor_status = c["erro"] if p["status"] == "Cancelado" else (
                    c["primaria"] if p["status"] == "Confirmado" else c["alerta"])
                linhas = [
                    ft.Row(controls=[ft.Text(icones.get(p["tipo"], "📄"), size=self.tam(24)),
                                     ft.Column(controls=[self.txt(p["titulo"], 16, True),
                                                         self.txt(f"{p['tipo']} • {p['data']}", 12,
                                                                  cor=c["suave"])], spacing=1, expand=True)]),
                    self.txt(p["detalhe"], 14, cor=c["suave"]),
                    self.txt("Com: " + p["contraparte"], 14),
                ]
                rodape = [self.selo(p["status"], c["clara"], cor_status), ft.Container(expand=True)]
                if p["valor"]:
                    rodape.append(self.txt(brl(p["valor"]), 17, True, c["primaria"]))
                linhas.append(ft.Row(controls=rodape, vertical_alignment=ft.CrossAxisAlignment.CENTER))
                if p["status"] == "Aguardando resposta":
                    linhas.append(self.botao("Cancelar", lambda e, pp=p: cancelar(pp), "perigo", altura=42))
                area.controls.append(self.card(linhas))

        montar()
        n = len([p for p in self.db.pedidos if p["usuario"] == self.usuario["id"]])
        self.texto_tela = f"Meus pedidos. Você tem {n} pedidos, propostas, aluguéis, parcerias ou consultas."
        controles = [self.titulo("Meus pedidos", "Compras, aluguéis, parcerias e consultas.", "📦")]
        if self.usuario["tipo"] == "agronomo":
            controles.append(self.secao("Pedidos de produtores para você"))
            controles += [self.card_solicitacao(s) for s in self.db.solicitacoes_agro]
            controles.append(self.secao("Meus pedidos"))
        controles += [self.chips(list(grupos.keys()), estado, "f", montar), area]
        return controles

    def tela_perfil(self):
        c = self.c
        u = self.usuario
        p = PERFIS[u["tipo"]]
        doc = u["documento"]
        doc_mask = ("•" * (len(doc) - 4) + doc[-4:]) if doc else "Conta de demonstração"
        meus_prod = [x for x in self.db.produtos if x["vendedor"] == u["nome"]]
        minhas_maq = [x for x in self.db.maquinas if x["dono"] == u["nome"]]
        minhas_terras = [x for x in self.db.terras if x["dono"] == u["nome"]]
        estado = {"letra": {1.0: "Normal", 1.15: "Grande", 1.3: "Muito grande"}.get(self.escala, "Normal"),
                  "contraste": "Ligado" if self.alto_contraste else "Desligado",
                  "auto": "Ligada" if self.leitura_auto else "Desligada"}

        def mudar_letra(op):
            self.escala = {"Normal": 1.0, "Grande": 1.15, "Muito grande": 1.3}[op]
            self.render()

        def mudar_contraste(op):
            if (op == "Ligado") != self.alto_contraste:
                self.trocar_contraste()

        def mudar_auto(op):
            self.leitura_auto = op == "Ligada"
            self.avisar("Leitura automática " + op.lower() + ".", "info")

        def sair(e):
            self.usuario = None
            self.historico = []
            self.chat = []
            self.rota, self.params = "login", {}
            self.aviso = ("Você saiu da conta.", "info")
            self.render()

        anuncios = ([f"{x['emoji']} {x['nome']} — {brl(x['preco'])}/{x['unidade']}" for x in meus_prod] +
                    [f"🚜 {x['nome']} — {brl(x['preco'])}/dia" for x in minhas_maq] +
                    [f"🌾 {x['titulo']}" for x in minhas_terras])

        self.texto_tela = (f"Meu perfil. {u['nome']}, conta de {p['nome']}, {u['cidade']}. "
                           f"Você tem {len(anuncios)} anúncios. Aqui você muda o tamanho da letra, o contraste e "
                           f"a leitura automática, ou sai da conta.")
        return [
            ft.Container(content=ft.Column(controls=[
                ft.Container(content=ft.Text(p["emoji"], size=self.tam(44)), width=self.tam(88),
                             height=self.tam(88), border_radius=44, bgcolor="#FFFFFF", alignment=ft.Alignment(0, 0)),
                self.txt(u["nome"], 21, True, "#FFFFFF", centro=True),
                self.txt(f"{p['nome']} • {u['cidade']}", 14, cor="#FFFFFF", centro=True),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6), bgcolor=c["primaria2"],
                border_radius=20, padding=20),
            self.card([
                self.info_linha("Usuário:", u["usuario"]),
                self.info_linha("Documento:", doc_mask),
                self.info_linha("Celular:", u["telefone"] or "—"),
            ]),
            self.secao("Meus anúncios"),
            self.card([self.txt(a, 15) for a in anuncios] or [
                self.txt("Você ainda não tem anúncios.", 15, cor=c["suave"])]),
            self.botao("📦 Meus pedidos", lambda e: self.ir("pedidos"), "secundario"),
            self.secao("Acessibilidade"),
            self.card([
                self.txt("Tamanho da letra", 15, True),
                self.chips(["Normal", "Grande", "Muito grande"], estado, "letra", mudar_letra),
                self.txt("Alto contraste", 15, True),
                self.chips(["Desligado", "Ligado"], estado, "contraste", mudar_contraste),
                self.txt("Ler cada tela em voz alta automaticamente", 15, True),
                self.chips(["Desligada", "Ligada"], estado, "auto", mudar_auto),
            ]),
            self.botao("Sair da conta", sair, "perigo"),
            self.txt("Agro Money • Protótipo demonstrativo • Nenhuma transação real", 12, cor=c["suave"],
                     centro=True),
        ]


# =====================================================================
# INÍCIO DO PROGRAMA
# =====================================================================

def main(page: ft.Page):
    AgroMoney(page)


if __name__ == "__main__":
    if hasattr(ft, "run"):   # Flet 0.70 / 1.0 ou mais novo
        ft.run(main)
    else:                    # Flet 0.2x
        ft.app(target=main)
