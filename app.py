# -*- coding: utf-8 -*-
import os
import math
import datetime
import json
from flask import Flask, render_template, request, redirect, url_for, Response, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

# --- Configuração do Flask e Extensões ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura-e-dificil-de-adivinhar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "info"

# --- Modelos do Banco de Dados ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    instalacoes = db.relationship('Instalacao', backref='author', lazy=True)
    relatorios = db.relationship('RelatorioHistorico', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Instalacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_combo = db.Column(db.String(50), nullable=False)
    descricao_combo = db.Column(db.String(100), nullable=False)
    valor_original = db.Column(db.Float, nullable=False)
    valor_arredondado = db.Column(db.Float, nullable=False)
    login_cliente = db.Column(db.String(100), nullable=False)
    data_instalacao = db.Column(db.String(20), nullable=False)
    porcentagem_comissao = db.Column(db.Float, nullable=False, default=15.0)
    comissao = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.String(300), nullable=True)
    data_registro = db.Column(db.DateTime, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class RelatorioHistorico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_inicio = db.Column(db.String(20), nullable=False)
    data_fim = db.Column(db.String(20), nullable=False)
    total_comissoes = db.Column(db.Float, nullable=False)
    num_instalacoes = db.Column(db.Integer, nullable=False)
    data_salva = db.Column(db.DateTime, default=datetime.datetime.now)
    instalacoes_json = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- Dicionário de Combos e Funções Auxiliares ---
COMBOS = {
    "CIDADE_FIBRA": { "300_MEGAS": {"preco": 99.90, "descricao": "300 MEGAS - CIDADE FIBRA ÓPTICA"}, "650_MEGAS": {"preco": 119.90, "descricao": "650 MEGAS - CIDADE FIBRA ÓPTICA"}, "800_MEGAS": {"preco": 139.90, "descricao": "800 MEGAS - CIDADE FIBRA ÓPTICA"}},
    "RURAL_FIBRA": { "300_MEGAS": {"preco": 109.90, "descricao": "300 MEGAS - RURAL FIBRA ÓPTICA"}, "650_MEGAS": {"preco": 129.90, "descricao": "650 MEGAS - RURAL FIBRA ÓPTICA"}, "800_MEGAS": {"preco": 149.90, "descricao": "800 MEGAS - RURAL FIBRA ÓPTICA"}},
    "RURAL_RADIO": { "4_MEGAS": {"preco": 109.90, "descricao": "4 MEGAS - RURAL VIA RÁDIO"}, "8_MEGAS": {"preco": 129.90, "descricao": "8 MEGAS - RURAL VIA RÁDIO"}, "14_MEGAS": {"preco": 159.90, "descricao": "14 MEGAS - RURAL VIA RÁDIO"}}
}

def arredondar_valor(valor):
    return math.ceil(valor) if valor % 1 != 0 else valor

@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if isinstance(date, str):
        try: date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except (ValueError, TypeError): return date
    return date.strftime(fmt or '%d/%m/%Y')

# --- Rotas de Autenticação ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login inválido. Verifique o seu nome de utilizador e senha.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('As senhas não coincidem!', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Este nome de utilizador já existe. Por favor, escolha outro.', 'warning')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('A sua conta foi criada com sucesso! Agora pode fazer o login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Rotas da Aplicação Principal (Protegidas) ---
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        try:
            nova_instalacao = Instalacao(
                tipo_combo=request.form['tipo_combo'],
                descricao_combo=COMBOS[request.form['tipo_combo']][request.form['combo_key']]["descricao"],
                valor_original=COMBOS[request.form['tipo_combo']][request.form['combo_key']]["preco"],
                valor_arredondado=arredondar_valor(COMBOS[request.form['tipo_combo']][request.form['combo_key']]["preco"]),
                login_cliente=request.form['login_cliente'],
                data_instalacao=request.form['data_instalacao'],
                porcentagem_comissao=float(request.form['porcentagem_comissao']),
                comissao=arredondar_valor(COMBOS[request.form['tipo_combo']][request.form['combo_key']]["preco"]) * (float(request.form['porcentagem_comissao']) / 100.0),
                observacoes=request.form.get('observacoes', ''),
                author=current_user
            )
            db.session.add(nova_instalacao)
            db.session.commit()
            flash('Instalação registada com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            return f"Ocorreu um erro: {e}", 500

    instalacoes = Instalacao.query.filter_by(author=current_user).order_by(Instalacao.data_registro.desc()).all()
    total_comissoes = sum(inst.comissao for inst in instalacoes)
    historico = RelatorioHistorico.query.filter_by(author=current_user).order_by(RelatorioHistorico.data_salva.desc()).all()
    
    return render_template('index.html', instalacoes=instalacoes, total_comissoes=total_comissoes, historico=historico, COMBOS_JS=json.dumps(COMBOS))

@app.route('/editar/<int:instalacao_id>', methods=['GET', 'POST'])
@login_required
def editar(instalacao_id):
    instalacao = Instalacao.query.get_or_404(instalacao_id)
    if instalacao.author != current_user:
        flash("Você não tem permissão para editar este registo.", "danger")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            instalacao.tipo_combo = request.form['tipo_combo']
            combo_key = request.form['combo_key']
            instalacao.porcentagem_comissao = float(request.form['porcentagem_comissao'])
            instalacao.descricao_combo = COMBOS[instalacao.tipo_combo][combo_key]['descricao']
            instalacao.valor_original = COMBOS[instalacao.tipo_combo][combo_key]['preco']
            instalacao.valor_arredondado = arredondar_valor(instalacao.valor_original)
            instalacao.comissao = instalacao.valor_arredondado * (instalacao.porcentagem_comissao / 100.0)
            instalacao.login_cliente = request.form['login_cliente']
            instalacao.data_instalacao = request.form['data_instalacao']
            instalacao.observacoes = request.form.get('observacoes', '')
            db.session.commit()
            flash('Registo atualizado com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            return f"Ocorreu um erro ao editar: {e}", 500
    return render_template('editar.html', instalacao=instalacao, COMBOS_JS=json.dumps(COMBOS))

@app.route('/excluir/<int:instalacao_id>', methods=['POST'])
@login_required
def excluir(instalacao_id):
    instalacao = Instalacao.query.get_or_404(instalacao_id)
    if instalacao.author != current_user:
        flash("Você não tem permissão para excluir este registo.", "danger")
        return redirect(url_for('index'))
    try:
        db.session.delete(instalacao)
        db.session.commit()
        flash('Registo excluído com sucesso!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        return f"Ocorreu um erro ao excluir: {e}", 500

@app.route('/salvar-periodo', methods=['POST'])
@login_required
def salvar_periodo():
    try:
        start_date_str = request.form['start_date']
        end_date_str = request.form['end_date']
        
        instalacoes_periodo = Instalacao.query.filter(
            Instalacao.author == current_user,
            Instalacao.data_instalacao.between(start_date_str, end_date_str)
        ).all()
        
        if instalacoes_periodo:
            total_comissoes_periodo = sum(inst.comissao for inst in instalacoes_periodo)
            instalacoes_list = [{'descricao_combo': i.descricao_combo, 'login_cliente': i.login_cliente, 'data_instalacao': i.data_instalacao, 'comissao': i.comissao, 'porcentagem_comissao': i.porcentagem_comissao, 'observacoes': i.observacoes} for i in instalacoes_periodo]
            novo_relatorio = RelatorioHistorico(data_inicio=start_date_str, data_fim=end_date_str, total_comissoes=total_comissoes_periodo, num_instalacoes=len(instalacoes_periodo), instalacoes_json=json.dumps(instalacoes_list), author=current_user)
            db.session.add(novo_relatorio)
            Instalacao.query.filter(Instalacao.id.in_([i.id for i in instalacoes_periodo])).delete(synchronize_session=False)
            db.session.commit()
            flash('Período salvo no histórico com sucesso!', 'success')
        else:
            flash('Nenhuma instalação encontrada no período selecionado.', 'warning')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        return f"Ocorreu um erro ao salvar o período: {e}", 500

# --- Rotas de Relatório ---
@app.route('/relatorio-historico/<int:relatorio_id>')
@login_required
def relatorio_historico(relatorio_id):
    relatorio = RelatorioHistorico.query.get_or_404(relatorio_id)
    if relatorio.author != current_user:
        flash("Você não tem permissão para ver este relatório.", "danger")
        return redirect(url_for('index'))
    instalacoes_lista = json.loads(relatorio.instalacoes_json)
    data_hoje = datetime.datetime.now()
    return render_template('relatorio_historico.html', relatorio=relatorio, instalacoes=instalacoes_lista, data_hoje=data_hoje)

@app.route('/relatorio/imprimir')
@login_required
def relatorio_imprimir():
    instalacoes = Instalacao.query.filter_by(author=current_user).order_by(Instalacao.data_instalacao.asc()).all()
    total_comissoes = sum(inst.comissao for inst in instalacoes)
    return render_template('relatorio_imprimir.html', instalacoes=instalacoes, total_comissoes=total_comissoes, data_hoje=datetime.datetime.now())

@app.route('/relatorio-historico/<int:relatorio_id>/imprimir')
@login_required
def relatorio_historico_imprimir(relatorio_id):
    relatorio = RelatorioHistorico.query.get_or_404(relatorio_id)
    if relatorio.author != current_user:
        flash("Você não tem permissão para ver este relatório.", "danger")
        return redirect(url_for('index'))
    instalacoes_lista = json.loads(relatorio.instalacoes_json)
    return render_template('relatorio_historico_imprimir.html', relatorio=relatorio, instalacoes=instalacoes_lista, data_hoje=datetime.datetime.now())

# --- Rotas de PWA ---
@app.route('/manifest.json')
def manifest():
    return Response(json.dumps({"name": "Gerenciador de Comissões", "short_name": "Comissões", "start_url": "/", "display": "standalone", "background_color": "#1e293b", "theme_color": "#1e293b", "icons": [{"src": "/static/img/ic_launcher.png", "sizes": "512x512", "type": "image/png"}]}), mimetype='application/json')

@app.route('/service-worker.js')
def service_worker():
    return Response("self.addEventListener('fetch', (event) => { event.respondWith(fetch(event.request)); });", mimetype='application/javascript')

# --- Ponto de Entrada ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)