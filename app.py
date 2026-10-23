
from flask import Flask, request, redirect, url_for, render_template_string, flash
from werkzeug.utils import secure_filename
import sqlite3
import os
import uuid

app = Flask(__name__)
app.secret_key = "cadastro-escolar-123"

# Banco de dados
BANCO = "alunos.db"

# Configuração das fotos
UPLOAD_FOLDER = os.path.join("static", "fotos")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Extensões permitidas
EXTENSOES_PERMITIDAS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "jfif"
}


def foto_permitida(nome):
    return (
        "." in nome
        and nome.rsplit(".", 1)[1].lower()
        in EXTENSOES_PERMITIDAS
    )


def conectar():
    con = sqlite3.connect(BANCO)
    con.row_factory = sqlite3.Row

    con.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT,
            telefone TEXT,
            cpf TEXT,
            nascimento TEXT,
            sexo TEXT,
            curso TEXT,
            foto TEXT
        )
    """)

    # Atualiza bancos antigos que ainda não possuem a coluna foto
    colunas = con.execute(
        "PRAGMA table_info(alunos)"
    ).fetchall()

    if not any(coluna["name"] == "foto" for coluna in colunas):
        con.execute("ALTER TABLE alunos ADD COLUMN foto TEXT")

    con.commit()

    return con


# Página principal
HTML = """
<!DOCTYPE html>
<html lang="pt-br">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Sistema de Cadastro de Alunos</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #eeeeee;
    color: #222222;
}

header {
    background: #2c3e50;
    color: white;
    padding: 18px;
    text-align: center;
}

header h1 {
    margin: 0;
    font-size: 26px;
}

header p {
    margin-bottom: 0;
}

.container {
    max-width: 1100px;
    margin: 20px auto;
    padding: 10px;
}

.card {
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #cccccc;
}

h2 {
    margin-top: 0;
    font-size: 21px;
    color: #2c3e50;
    border-bottom: 1px solid #dddddd;
    padding-bottom: 10px;
}

form {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
}

input,
select {
    width: 100%;
    padding: 10px;
    border: 1px solid #bbbbbb;
    background: white;
    font-size: 14px;
}

input:focus,
select:focus {
    outline: 1px solid #2c3e50;
}

input[type="file"] {
    background: #f7f7f7;
}

button,
.botao {
    padding: 9px 14px;
    border: 1px solid #263747;
    background: #34495e;
    color: white;
    cursor: pointer;
    text-decoration: none;
    font-size: 14px;
    text-align: center;
}

button:hover,
.botao:hover {
    background: #22313f;
}

.cancelar {
    background: #777777;
    border-color: #666666;
}

.excluir {
    background: #b83232;
    border-color: #9e2525;
}

.editar {
    background: #347a98;
    border-color: #28647d;
}

.acoes {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}

.acoes form {
    display: block;
}

.pesquisa {
    display: flex;
    gap: 8px;
    margin-bottom: 15px;
}

.pesquisa input {
    flex: 1;
}

table {
    width: 100%;
    border-collapse: collapse;
    background: white;
}

th,
td {
    padding: 10px;
    text-align: left;
    border: 1px solid #dddddd;
}

th {
    background: #e5e9ed;
    color: #222222;
}

.mensagem {
    padding: 10px;
    background: #e2f0df;
    color: #285b28;
    border: 1px solid #b7d5b1;
    margin-bottom: 15px;
}

.foto-aluno {
    width: 55px;
    height: 55px;
    object-fit: cover;
    border: 1px solid #cccccc;
    border-radius: 3px;
}

.foto-atual {
    display: flex;
    align-items: center;
    gap: 12px;
    grid-column: 1 / -1;
}

.foto-atual img {
    width: 80px;
    height: 80px;
    object-fit: cover;
    border: 1px solid #cccccc;
}

@media (max-width: 700px) {
    .container {
        padding: 8px;
    }

    .card {
        padding: 12px;
    }

    form {
        grid-template-columns: 1fr;
    }

    .pesquisa {
        flex-direction: column;
    }

    table {
        font-size: 12px;
    }

    th,
    td {
        padding: 6px;
    }

    .acoes {
        flex-direction: column;
    }
}
</style>

</head>

<body>

<header>

    <h1>Sistema de Cadastro de Alunos</h1>

    <p>Gerenciamento escolar</p>

</header>

<div class="container">

{% with mensagens = get_flashed_messages() %}

    {% for mensagem in mensagens %}

        <div class="mensagem">
            {{ mensagem }}
        </div>

    {% endfor %}

{% endwith %}

<div class="card">

<h2>
    {{ "Editar aluno" if aluno else "Cadastrar aluno" }}
</h2>

<form action="/salvar"
method="POST"
enctype="multipart/form-data">

<input type="hidden"
name="id"
value="{{ aluno.id if aluno else '' }}">

<input name="nome"
placeholder="Nome completo"
value="{{ aluno.nome if aluno else '' }}"
required>

<input name="email"
type="email"
placeholder="E-mail"
value="{{ aluno.email if aluno else '' }}">

<input name="telefone"
placeholder="Telefone"
value="{{ aluno.telefone if aluno else '' }}">

<input name="cpf"
placeholder="CPF"
value="{{ aluno.cpf if aluno else '' }}">

<input name="nascimento"
type="date"
value="{{ aluno.nascimento if aluno else '' }}">

<select name="sexo">

<option value="">Selecione o sexo</option>

<option value="Masculino"
{% if aluno and aluno.sexo == "Masculino" %}selected{% endif %}>
Masculino
</option>

<option value="Feminino"
{% if aluno and aluno.sexo == "Feminino" %}selected{% endif %}>
Feminino
</option>

<option value="Outro"
{% if aluno and aluno.sexo == "Outro" %}selected{% endif %}>
Outro
</option>

</select>

<select name="curso">

<option value="">Selecione o curso</option>

{% for curso in cursos %}

<option value="{{ curso }}"
{% if aluno and aluno.curso == curso %}selected{% endif %}>

{{ curso }}

</option>

{% endfor %}

</select>

<!-- Foto atual durante a edição -->

{% if aluno and aluno.foto %}

<div class="foto-atual">

<img src="{{ url_for('static', filename='fotos/' + aluno.foto) }}">

<div>
    <strong>Foto atual</strong>
    <p>Escolha outra imagem para substituir.</p>
</div>

</div>

{% endif %}

<!-- Campo para selecionar foto -->

<label for="foto">
    Foto do aluno
</label>

<input type="file"
id="foto"
name="foto"
accept="image/png,image/jpeg,image/gif,image/webp">

<button type="submit">

{{ "Atualizar aluno" if aluno else "Cadastrar aluno" }}

</button>

{% if aluno %}

<a class="botao cancelar" href="/">
    Cancelar
</a>

{% endif %}

</form>

</div>

<div class="card">

<h2>Alunos cadastrados</h2>

<form action="/" method="GET" class="pesquisa">

<input name="busca"
placeholder="Pesquisar por nome, CPF ou curso"
value="{{ busca }}">

<button type="submit">
    Pesquisar
</button>

<a class="botao cancelar" href="/">
    Limpar
</a>

</form>

<p>Total de alunos: {{ alunos|length }}</p>

<table>

<thead>

<tr>

<th>Foto</th>
<th>Nome</th>
<th>Curso</th>
<th>Telefone</th>
<th>Ações</th>

</tr>

</thead>

<tbody>

{% for aluno in alunos %}

<tr>

<td>

{% if aluno.foto %}

<img
class="foto-aluno"
src="{{ url_for('static', filename='fotos/' + aluno.foto) }}"
alt="Foto de {{ aluno.nome }}">

{% else %}

<div class="foto-aluno"
style="display:flex;align-items:center;justify-content:center;background:#e2e8f0;">

</div>

{% endif %}

</td>

<td>{{ aluno.nome }}</td>

<td>{{ aluno.curso }}</td>

<td>{{ aluno.telefone }}</td>

<td>

<div class="acoes">

<a class="botao editar"
href="/editar/{{ aluno.id }}">

Editar

</a>

<form action="/excluir/{{ aluno.id }}"
method="POST"
onsubmit="return confirm('Deseja excluir este aluno?')">

<button class="excluir" type="submit">

Excluir

</button>

</form>

</div>

</td>

</tr>

{% else %}

<tr>

<td colspan="5">
    Nenhum aluno cadastrado.
</td>

</tr>

{% endfor %}

</tbody>

</table>

</div>

</div>

</body>

</html>
"""


CURSOS = [
    "Técnico em Informática",
    "Administração",
    "Enfermagem",
    "Logística",
    "Desenvolvimento de Sistemas",
    "Outro"
]


# Página inicial
@app.route("/")
def inicio():

    busca = request.args.get("busca", "").strip()

    con = conectar()

    if busca:

        alunos = con.execute("""
            SELECT * FROM alunos
            WHERE nome LIKE ?
            OR cpf LIKE ?
            OR curso LIKE ?
            ORDER BY nome
        """, (
            f"%{busca}%",
            f"%{busca}%",
            f"%{busca}%"
        )).fetchall()

    else:

        alunos = con.execute("""
            SELECT * FROM alunos
            ORDER BY nome
        """).fetchall()

    con.close()

    return render_template_string(
        HTML,
        alunos=alunos,
        aluno=None,
        busca=busca,
        cursos=CURSOS
    )


# Salvar cadastro ou edição
@app.route("/salvar", methods=["POST"])
def salvar():

    id_aluno = request.form.get("id")

    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip()
    telefone = request.form.get("telefone", "").strip()
    cpf = request.form.get("cpf", "").strip()
    nascimento = request.form.get("nascimento", "")
    sexo = request.form.get("sexo", "")
    curso = request.form.get("curso", "")

    if not nome:

        flash("O nome do aluno é obrigatório.")

        return redirect(url_for("inicio"))

    con = conectar()

    # Recuperar foto anterior, caso seja uma edição
    foto_antiga = ""

    if id_aluno:

        aluno_antigo = con.execute("""
            SELECT foto FROM alunos WHERE id=?
        """, (id_aluno,)).fetchone()

        if aluno_antigo:
            foto_antiga = aluno_antigo["foto"] or ""

    # Foto enviada pelo formulário
    arquivo_foto = request.files.get("foto")

    foto = foto_antiga

    # Se uma nova foto foi selecionada
    if arquivo_foto and arquivo_foto.filename:

        if not foto_permitida(arquivo_foto.filename):

            con.close()

            flash("Formato de foto inválido. Use PNG, JPG, JPEG, GIF ou WEBP.")

            return redirect(
                url_for("editar", id_aluno=id_aluno)
                if id_aluno
                else url_for("inicio")
            )

        nome_original = secure_filename(
            arquivo_foto.filename
        )

        extensao = nome_original.rsplit(".", 1)[1].lower()

        nome_arquivo = str(uuid.uuid4()) + "." + extensao

        caminho = os.path.join(
            app.config["UPLOAD_FOLDER"],
            nome_arquivo
        )

        arquivo_foto.save(caminho)

        foto = nome_arquivo

    # Atualizar aluno
    if id_aluno:

        con.execute("""
            UPDATE alunos
            SET nome=?,
                email=?,
                telefone=?,
                cpf=?,
                nascimento=?,
                sexo=?,
                curso=?,
                foto=?
            WHERE id=?
        """, (
            nome,
            email,
            telefone,
            cpf,
            nascimento,
            sexo,
            curso,
            foto,
            id_aluno
        ))

        # Excluir foto anterior somente se uma nova foi enviada
        if foto_antiga and foto != foto_antiga:

            caminho_antigo = os.path.join(
                app.config["UPLOAD_FOLDER"],
                foto_antiga
            )

            if os.path.isfile(caminho_antigo):
                os.remove(caminho_antigo)

        flash("Aluno atualizado com sucesso!")

    # Novo aluno
    else:

        con.execute("""
            INSERT INTO alunos
            (
                nome,
                email,
                telefone,
                cpf,
                nascimento,
                sexo,
                curso,
                foto
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome,
            email,
            telefone,
            cpf,
            nascimento,
            sexo,
            curso,
            foto
        ))

        flash("Aluno cadastrado com sucesso!")

    con.commit()
    con.close()

    return redirect(url_for("inicio"))


# Editar aluno
@app.route("/editar/<int:id_aluno>")
def editar(id_aluno):

    con = conectar()

    aluno = con.execute("""
        SELECT * FROM alunos WHERE id=?
    """, (id_aluno,)).fetchone()

    con.close()

    if aluno is None:

        flash("Aluno não encontrado.")

        return redirect(url_for("inicio"))

    return render_template_string(
        HTML,
        alunos=[],
        aluno=aluno,
        busca="",
        cursos=CURSOS
    )


# Excluir aluno
@app.route("/excluir/<int:id_aluno>", methods=["POST"])
def excluir(id_aluno):

    con = conectar()

    aluno = con.execute("""
        SELECT foto FROM alunos WHERE id=?
    """, (id_aluno,)).fetchone()

    if aluno:

        foto = aluno["foto"]

        con.execute("""
            DELETE FROM alunos WHERE id=?
        """, (id_aluno,))

        con.commit()

        # Apagar a foto do aluno
        if foto:

            caminho_foto = os.path.join(
                app.config["UPLOAD_FOLDER"],
                foto
            )

            if os.path.isfile(caminho_foto):
                os.remove(caminho_foto)

        flash("Aluno excluído com sucesso!")

    else:

        flash("Aluno não encontrado.")

    con.close()

    return redirect(url_for("inicio"))


# Iniciar sistema
if __name__ == "__main__":

    conectar().close()

    app.run(debug=True)
