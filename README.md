## 🎯 O Problema

Em provedores de internet (ISPs), o cálculo de comissões para técnicos de campo é um 
processo complexo. Ele depende de múltiplos fatores, como o tipo de serviço (instalação, 
reativação) e os diferentes "combos" (pacotes de serviços) que o cliente contrata.

Realizar esse controle manualmente em planilhas é demorado, aumenta significativamente o 
risco de erros de cálculo no pagamento e não oferece transparência para os técnicos sobre seus ganhos.

## 💡 A Solução

Este sistema web, desenvolvido em Python e Flask, automatiza 100% o processo de gerenciamento de comissões. 
A plataforma permite o cadastro dos serviços, dos combos e das regras de negócio (ex: 15% de comissão sobre o valor do serviço).

Com isso, basta lançar as Ordens de Serviço executadas e o sistema calcula automaticamente o valor devido a cada técnico, 
gerando relatórios precisos para o departamento financeiro e um extrato claro para o colaborador.

## ✨ Funcionalidades Principais
- [ ] Cadastro de Técnicos
- [ ] Cadastro de Serviços e Combos (com valores base para a comissão)
- [ ] Lançamento de Ordens de Serviço (Instalação, Reativação, etc.)
- [ ] Cálculo automático da comissão (baseado na regra de 15%)
- [ ] Geração de Relatório de Pagamentos por técnico
- [ ] Painel para o técnico consultar seu extrato de comissões (Planejado)

## 🛠️ Tecnologias Utilizadas
* **Back-end:** Python
* **Framework Web:** Flask
* **Banco de Dados:** SQLite
* **ORM:** Flask-SQLAlchemy (com Flask-Migrate)
* **Front-end:** HTML, Jinja2
* **Framework CSS:** Tailwind CSS
* 
