# 08 — Plan: phase 8, questions (C5 and A4)

Status: **agreed 2026-10-29** — implements the phase 8 row of `docs/plans/01-implementation-plan.md` (§2, §5, §8).
Labels: **[OFFICIAL]** Oblig 4 · **[ASSUMPTION]** our proposal (from `docs/backlog/user-stories.md`).

## Requirements
**[OFFICIAL] C5 Questions:** "Ask a question about a specific order and read Ekte Mat's answer."
**[OFFICIAL] A4 Questions:** "Read and answer customers' questions about their orders."
Stories: **US-18** ask, **US-19** read the answer, **US-20** read and answer (admin).

## Scope
| Route | Purpose | Story |
|---|---|---|
| `GET /account/orders/<id>` (extended) | Questions on the order with date and time; answer and its date under each question, or "waiting for an answer"; form to ask a new question | US-18 AC1, US-19 |
| `POST /account/orders/<id>/questions` | Ask a question on one of my orders; empty text rejected; others' orders → 404 | US-18 |
| `GET /admin/questions` | All questions, unanswered first, then oldest first; order number (link), customer, asked at; answer form for unanswered questions | US-20 AC1 |
| `POST /admin/questions/<id>/answer` | Store answer with admin and time; empty answer rejected | US-20 AC2, AC3 |
| `GET /admin/orders/<id>` (extended) | The order's questions with answer forms | US-20 |
| `GET /admin/` (extended) | Count of unanswered questions with link (01-plan §8 "dashboard counts") | — |

Customer routes `@login_required`, admin routes `@admin_required`; POSTs carry CSRF tokens. "My orders" shows how many questions per order are waiting for an answer.

## Rules (in `app/models/questions.py`)
| Rule | Label |
|---|---|
| A customer can only ask about their own orders (others → not found) | ASSUMPTION (US-18 AC3) |
| Question and answer text required after trimming spaces; at most 1 000 characters | ASSUMPTION (US-18 AC2, US-20 AC3) |
| Questions allowed on orders in any status (e.g. "why was it rejected?") | ASSUMPTION |
| A question is answered once; the answer is stored with the admin and the time and is not edited afterwards (keeps the record the customer has read) | ASSUMPTION |
| No guest names or personal health data should be written in questions; the form says so | ASSUMPTION (GDPR note) |

## Design
- Model: `ask_question(repos, customer, order_id, text)` and `answer_question(repos, admin, question_id, text)` raising `InvalidQuestion` (new), `NotFound`, or `AlreadyAnswered` (new). New repository method `QuestionRepository.get(id)`.
- Controllers: `account.ask_question`; `admin.question_list`, `admin.question_answer` (returns to the order page or the list it was sent from).
- Forms: `QuestionForm`, `AnswerForm`.
- Views: `_partials/questions.html` (thread, used by customer and admin order pages), `admin/questions/list.html`.

## Tests
`tests/unit/test_questions.py` (rules), `tests/repositories/test_question_repository.py` (`get`), `tests/controllers/test_account_questions.py` (ask, empty, too long, others' order, waiting/answered display, round trip), `tests/controllers/test_admin_questions.py` (list order and links, answer, empty answer, already answered, unknown id, customer 403, dashboard count, answer from order page).

## Acceptance (01-plan §8)
No questions on others' orders; empty text rejected; question → answer round trip works; all tests pass.
