Aqui está uma versão melhorada do seu README, aproveitando os comandos do **Makefile** que você já tem definidos, organizando melhor as seções e deixando o uso mais direto:

---

# 🎸 Dashboard - The Band

> 🧠 *"The idea is that each ontology-based service in the architecture is like a musician that plays an instrument (representing ontology concepts, relations, and rules). Together, these services create music (information) from musical notes (application data) to satisfy a public (the organization)."*

**Dashboard - The Band** is the orchestrator of a semantic, modular, and intelligent service architecture. Each service acts like a band member, transforming structured and unstructured data into meaningful insights — like musicians creating harmony from notes.

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=The-Band-Solution_dashboard\&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=The-Band-Solution_dashboard) 
---

## 🚀 Tech Stack

* [Python 3.10](https://www.python.org/)
* [Django](https://www.djangoproject.com/)
* [Gunicorn](https://gunicorn.org/)
* [Docker & Docker Compose](https://docs.docker.com/)
* PostgreSQL (via Docker)

---

## 📦 Project Structure

```
src/
├── dashboard/          # Django settings and core
├── apps/               # Business apps
├── features/           # Functional modules
├── static/             # Static files
├── staticfiles/        # Collected by collectstatic
├── manage.py
├── requirements.txt
```

---

## ⚙️ Setup & Usage

### 1. Create the environment file

```bash
cp .env.example .env
```

### 2. Using Makefile

The project provides a `Makefile` to simplify common tasks:

```bash
make up         # Start the app
make stop       # Stop containers
make build      # Build and start (force rebuild)
make down       # Stop and remove containers
make destroy    # Remove containers and volumes (clean state)
make superuser  # Create Django superuser
```

---

## 🐳 Running with Docker

If you prefer direct Docker commands:

```bash
docker compose up --build
```

The app will be available at: [http://localhost:8000](http://localhost:8000)

---

## 👤 Creating a superuser

You can create a Django superuser with:

```bash
make superuser
```

This runs the `create_superuser.sh` script, which executes the Python script inside the container.

---

## 🐍 Running Django commands

Access the container and run:

```bash
docker exec -it dashboard_the_band bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 🧪 Running tests

```bash
docker exec -it dashboard_the_band python manage.py test
```

---

## 🛠️ Scripts and utilities

* `create_superuser.py`: Creates the superuser if it doesn't exist.
* `create_superuser.sh`: Executes the script inside the container.
* `Makefile`: Provides shortcuts for build, dev, test, and deploy commands.

---

## 📊 Example Query (Neo4j)

```cypher
MATCH (i:Issue)-[:created_by]->(a:Person)
OPTIONAL MATCH (i)-[:assigned_to]->(assignee:Person)
RETURN 
  a.login AS author, 
  coalesce(assignee.login, a.login) AS assignee, 
  count(*) AS total
ORDER BY author, assignee, total DESC;
```

---

## 📁 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙋 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

---

## ✨ Author

Made with 💙 by **The Band Dev Team**

---

Quer que eu adicione também uma seção **🌍 Environment Variables (.env)** explicando cada variável obrigatória (como DB configs, Django settings, etc.), baseado no seu `.env` que vimos antes? Isso deixaria o README ainda mais completo.
