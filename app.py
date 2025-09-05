# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, Response, json
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime
import math
import os

# --- Configuração do Flask e do Banco de Dados ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Dicionário de Combos ---
COMBOS = {
    "CIDADE_FIBRA": {
        "300_MEGAS": {"preco": 99.90, "descricao": "300 MEGAS - CIDADE FIBRA ÓPTICA"},
        "650_MEGAS": {"preco": 119.90, "descricao": "650 MEGAS - CIDADE FIBRA ÓPTICA"},
        "800_MEGAS": {"preco": 139.90, "descricao": "800 MEGAS - CIDADE FIBRA ÓPTICA"},
    },
    "RURAL_FIBRA": {
        "300_MEGAS": {"preco": 109.90, "descricao": "300 MEGAS - RURAL FIBRA ÓPTICA"},
        "650_MEGAS": {"preco": 129.90, "descricao": "650 MEGAS - RURAL FIBRA ÓPTICA"},
        "800_MEGAS": {"preco": 149.90, "descricao": "800 MEGAS - RURAL FIBRA ÓPTICA"},
    },
    "RURAL_RADIO": {
        "4_MEGAS": {"preco": 109.90, "descricao": "4 MEGAS - RURAL VIA RÁDIO"},
        "8_MEGAS": {"preco": 129.90, "descricao": "8 MEGAS - RURAL VIA RÁDIO"},
        "14_MEGAS": {"preco": 159.90, "descricao": "14 MEGAS - RURAL VIA RÁDIO"},
    },
}

# --- Função de Arredondamento ---
def arredondar_valor(valor):
    return math.ceil(valor) if valor % 1 != 0 else valor

# --- Modelos do Banco de Dados ---
class Instalacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_combo = db.Column(db.String(50), nullable=False)
    descricao_combo = db.Column(db.String(100), nullable=False)
    valor_original = db.Column(db.Float, nullable=False)
    valor_arredondado = db.Column(db.Float, nullable=False)
    login_cliente = db.Column(db.String(100), nullable=False)
    # LINHA MODIFICADA ABAIXO
    data_instalacao = db.Column(db.String(20), nullable=False)
    comissao = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.String(300), nullable=True)
    data_registro = db.Column(db.DateTime, default=datetime.datetime.now)

class RelatorioHistorico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # LINHAS MODIFICADAS ABAIXO
    data_inicio = db.Column(db.String(20), nullable=False)
    data_fim = db.Column(db.String(20), nullable=False)
    total_comissoes = db.Column(db.Float, nullable=False)
    num_instalacoes = db.Column(db.Integer, nullable=False)
    data_salva = db.Column(db.DateTime, default=datetime.datetime.now)
    instalacoes_json = db.Column(db.String, nullable=False)

# --- Filtro para formatar datas no template ---
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    # This filter now handles both date objects and string dates
    if isinstance(date, str):
        try:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return date # Return original string if format is wrong
    
    date_format = fmt or '%d/%m/%Y'
    return date.strftime(date_format)

# --- Rotas PWA (Manifest e Service Worker) ---
@app.route('/manifest.json')
def manifest():
    return Response(json.dumps({
        "name": "Gerenciador de Comissões",
        "short_name": "Comissões",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#1e293b",
        "theme_color": "#1e293b",
        "icons": [{"src": "/static/img/ic_launcher.png", "sizes": "512x512", "type": "image/png"}]
    }), mimetype='application/json')

@app.route('/service-worker.js')
def service_worker():
    return Response("self.addEventListener('fetch', (event) => { event.respondWith(fetch(event.request)); });", mimetype='application/javascript')

# --- Rotas da Aplicação ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            tipo_combo = request.form['tipo_combo']
            combo_key = request.form['combo_key']
            login_cliente = request.form['login_cliente']
            data_instalacao_str = request.form['data_instalacao']
            observacoes = request.form.get('observacoes', '')

            combo_selecionado = COMBOS[tipo_combo][combo_key]
            valor_original = combo_selecionado["preco"]
            valor_arredondado = arredondar_valor(valor_original)
            comissao = valor_arredondado * 0.15
            
            nova_instalacao = Instalacao(
                tipo_combo=tipo_combo,
                descricao_combo=combo_selecionado["descricao"],
                valor_original=valor_original,
                valor_arredondado=valor_arredondado,
                login_cliente=login_cliente,
                # Salva a data como string no formato ISO
                data_instalacao=data_instalacao_str,
                comissao=comissao,
                observacoes=observacoes
            )
            db.session.add(nova_instalacao)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            return f"Ocorreu um erro: {e}", 500

    instalacoes = Instalacao.query.order_by(Instalacao.data_registro.desc()).all()
    total_comissoes = sum(inst.comissao for inst in instalacoes)
    historico = RelatorioHistorico.query.order_by(RelatorioHistorico.data_salva.desc()).all()
    
    return render_template('index.html', 
                           instalacoes=instalacoes, 
                           total_comissoes=total_comissoes, 
                           historico=historico, 
                           COMBOS_JS=json.dumps(COMBOS))

@app.route('/editar/<int:instalacao_id>', methods=['GET', 'POST'])
def editar(instalacao_id):
    instalacao = Instalacao.query.get_or_404(instalacao_id)
    if request.method == 'POST':
        try:
            instalacao.tipo_combo = request.form['tipo_combo']
            combo_key = request.form['combo_key']
            instalacao.descricao_combo = COMBOS[instalacao.tipo_combo][combo_key]['descricao']
            instalacao.valor_original = COMBOS[instalacao.tipo_combo][combo_key]['preco']
            instalacao.valor_arredondado = arredondar_valor(instalacao.valor_original)
            instalacao.comissao = instalacao.valor_arredondado * 0.15
            instalacao.login_cliente = request.form['login_cliente']
            # Salva a data como string no formato ISO
            instalacao.data_instalacao = request.form['data_instalacao']
            instalacao.observacoes = request.form.get('observacoes', '')

            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            return f"Ocorreu um erro ao editar: {e}", 500

    return render_template('editar.html', instalacao=instalacao, COMBOS_JS=json.dumps(COMBOS))

@app.route('/excluir/<int:instalacao_id>', methods=['POST'])
def excluir(instalacao_id):
    instalacao = Instalacao.query.get_or_404(instalacao_id)
    try:
        db.session.delete(instalacao)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Ocorreu um erro ao excluir: {e}", 500

@app.route('/salvar-periodo', methods=['POST'])
def salvar_periodo():
    try:
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        
        # Filtra usando as datas como strings
        instalacoes_periodo = Instalacao.query.filter(
            Instalacao.data_instalacao.between(start_date_str, end_date_str)
        ).all()
        
        if instalacoes_periodo:
            total_comissoes_periodo = sum(inst.comissao for inst in instalacoes_periodo)
            instalacoes_list = [
                {
                    'descricao_combo': i.descricao_combo, 
                    'login_cliente': i.login_cliente, 
                    'data_instalacao': i.data_instalacao, 
                    'comissao': i.comissao,
                    'observacoes': i.observacoes
                } for i in instalacoes_periodo]

            novo_relatorio = RelatorioHistorico(
                data_inicio=start_date_str,
                data_fim=end_date_str,
                total_comissoes=total_comissoes_periodo,
                num_instalacoes=len(instalacoes_periodo),
                instalacoes_json=json.dumps(instalacoes_list)
            )
            db.session.add(novo_relatorio)
            
            Instalacao.query.filter(Instalacao.id.in_([i.id for i in instalacoes_periodo])).delete(synchronize_session=False)

        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        return f"Ocorreu um erro ao salvar o período: {e}", 500

# Rota sem alteração
@app.route('/relatorio-historico/<int:relatorio_id>')
def relatorio_historico(relatorio_id):
    relatorio = RelatorioHistorico.query.get_or_404(relatorio_id)
    instalacoes_lista = json.loads(relatorio.instalacoes_json)
    data_hoje = datetime.datetime.now()
    return render_template('relatorio_historico.html', 
                           relatorio=relatorio, 
                           instalacoes=instalacoes_lista,
                           data_hoje=data_hoje)

# Rota sem alteração
@app.route('/relatorio/imprimir')
def relatorio_imprimir():
    instalacoes = Instalacao.query.order_by(Instalacao.data_instalacao.asc()).all()
    total_comissoes = sum(inst.comissao for inst in instalacoes)
    return render_template('relatorio_imprimir.html', 
                           instalacoes=instalacoes, 
                           total_comissoes=total_comissoes,
                           data_hoje=datetime.datetime.now())

# Rota sem alteração
@app.route('/relatorio-historico/<int:relatorio_id>/imprimir')
def relatorio_historico_imprimir(relatorio_id):
    relatorio = RelatorioHistorico.query.get_or_404(relatorio_id)
    instalacoes_lista = json.loads(relatorio.instalacoes_json)
    return render_template('relatorio_historico_imprimir.html',
                           relatorio=relatorio,
                           instalacoes=instalacoes_lista,
                           data_hoje=datetime.datetime.now())

# --- Ponto de Entrada do Aplicativo ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(host='0.0.0.0', port=5000, debug=True)
