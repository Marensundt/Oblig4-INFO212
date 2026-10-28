# Ekte Mat Online

INFO212 Obligatory assignment 4: a Flask web application for the fictional Bergen caterer Ekte Mat AS, with a customer site (menu, cart, orders, questions) and an admin panel (food items, images, orders, questions). All data is synthetic.

Architecture: Model–View–Controller with Flask. See `CLAUDE.md` and `docs/plans/01-implementation-plan.md`.

## Requirements
- Python **3.11 or newer**
- Git

## Install
```bash
git clone https://github.com/Marensundt/Oblig4-INFO212.git
cd Oblig4-INFO212
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # optional: set SECRET_KEY; never commit .env
```

## Seed the database
Not available yet — the seed command (sample food items, an admin and test customers) is added in phase 1.

## Run
```bash
flask --app run run
```
Open http://127.0.0.1:5000

## Test
```bash
pytest
```
Tests also run automatically on GitHub (Actions) for every pull request and push to `main`, on Python 3.11 and 3.13.

## Project structure
```
app/
  models/            model layer: domain classes and data access (repositories)
  views/templates/   view layer: Jinja2 templates
  controllers/       controller layer: blueprints shop, account, admin
  static/            CSS and JavaScript
tests/               pytest tests
docs/plans/          agreed plans (one per larger feature)
docs/backlog/        user stories, acceptance criteria, NFRs, traceability
docs/design/         UML diagrams (PlantUML + PNG)
```
