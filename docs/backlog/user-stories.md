# Product backlog — epics, user stories and acceptance criteria

Status: **draft v1 for team review** (2026-10-28). Replaces the missing Lab 7 backlog; see `docs/plans/02-backlog-and-design-plan.md`.

## Conventions
- **Priority (MoSCoW, adapted to Oblig 4):** **Must** = needed for Oblig 4 approval · **Should** = official "going further" item (OB4 §2) · **Could** = other data-pack need that fits the first version · **Won't** = outside this release.
- **Trace:** every story cites an Oblig 4 ID and/or a source file with a short quote. Anything inferred is marked **ASSUMPTION**.
- **Roles:** *customer* (private or corporate person with an account), *visitor* (not logged in), *admin* (Ekte Mat staff, e.g. Ingrid, Sunniva, Mateo), *assessor* (course staff).
- Acceptance criteria (AC) use Given/When/Then and are written to become automated tests.
- **Official vs assumption in AC:** an AC **without a tag** follows directly from the Oblig 4 text cited in the story's *Trace*. Every AC that adds a rule not stated in Oblig 4 is tagged *(ASSUMPTION)*.

### Source keys
| Key | Source |
|---|---|
| OB4 | Official assignment *INFO212 Oblig 4 — Building Ekte Mat Online with Claude Code* (§ = section) |
| INT-I / INT-S / INT-M / INT-F | `interview_Ingrid_owner.txt` / `interview_Sunniva_event_coordinator.txt` / `interview_Mateo_head_chef.txt` / `interview_Fjordtek_customer.txt` |
| MTG | `notes meeting 12 aug FINAL.txt` |
| ASIS | `asis_order_process.md` |
| IT | `current_IT_landscape.txt` |
| GDPR | `GDPR note from consultant.txt` |
| MENU | `lunch menu autumn.txt` |
| VIS | `vision_draft_v0.3.docx` |
| ORD | `orders_2024_2025_export.xlsx` |
| E0xx | e-mail ID in `customer_emails_export.csv` |

## Coverage of the official minimum requirements (review 2026-10-28)
Every clause of A1–A4 and C1–C5 is covered by at least one Must story and acceptance criterion.

| OB4 | Clause | Story / AC |
|---|---|---|
| A1 | add / edit / remove | US-01, US-02, US-03 AC1 |
| A1 | name, description, price NOK, min order qty, event categories, allergens, dietary labels | US-01 AC1 |
| A1 | whether the item is published | US-01 AC4, US-03 AC3 |
| A2 | upload a picture for each item | US-04 AC1–AC3 |
| A2 | instruction → AI agent/image service creates **or modifies** the picture | US-05 AC1 (create), AC2 (modify) |
| A2 | admin previews before saving | US-04 AC1–AC2, US-05 AC1 |
| A3 | list of all orders, filter by status / by event date | US-14 AC1, AC2, AC3 |
| A3 | page per order to manage it | US-15 AC1 |
| A3 | submitted → approved → in preparation → delivered | US-15 AC2, AC2b |
| A3 | or rejected / cancelled | US-15 AC2, AC4 |
| A3 | payment status (not paid, deposit paid, invoiced, paid) | US-16 AC1–AC2 |
| A4 | read and answer customers' questions about their orders | US-20 AC1–AC2 |
| C1 | cards grouped by kind of event (birthday, confirmation, wedding, conference, julebord, …) | US-06 AC1 |
| C1 | card shows picture, price, minimum order, allergens | US-06 AC2 |
| C2 | add / change / remove items | US-08 AC1, US-09 AC2, AC3 |
| C2 | estimated total cost | US-09 AC1 |
| C2 | quantities below minimum not accepted | US-08 AC2, US-09 AC2 |
| C3 | log in (or register) | US-10 AC1, US-11 AC1–AC2 |
| C3 | event date, number of guests, delivery address | US-12 AC1 |
| C3 | allergy and dietary notes per guest group | US-13 AC1, AC3 |
| C3 | no payment solution | US-12 AC4, US-16 |
| C4 | own orders with current status and payment status | US-17 AC1, AC3 |
| C5 | ask a question about a specific order | US-18 AC1 |
| C5 | read Ekte Mat's answer | US-19 AC1–AC2 |

## Epic overview
| Epic | Stories | Oblig 4 | Priority |
|---|---|---|---|
| E1 Menu and food items | US-01 – US-07 | A1, A2, C1 | Must (US-07 Could) |
| E2 Cart and ordering | US-08 – US-13 | C2, C3 | Must |
| E3 Order management | US-14 – US-17 | A3, C4 | Must |
| E4 Questions | US-18 – US-20 | A4, C5 | Must |
| E5 Access and running the system | US-21 – US-22 | OB4 §3 | Must |
| E6 Going further | US-23 – US-27 | OB4 §2 "Going further" | Should |
| E7 Other data-pack needs | US-28 – US-31 | — | Could |
| — Not in this release | W-01 – W-10 | — | Won't |

---

## E1 Menu and food items

### US-01 Add a food item — **Must**
As an **admin** I want to add a food item with name, description, price in NOK, minimum order quantity, event categories, allergens, dietary labels and a published flag, so that customers can order it online.
- **Trace:** OB4 A1 "Add, edit and remove the food Ekte Mat caters…"; INT-M "I want to edit the menu myself"; MENU "Allergens to be labelled: fish, milk, gluten, nuts, celery, mustard."
- **AC1** Given I am logged in as admin, when I submit the form with all fields valid, then the item is saved and shown in the admin item list with the values I entered.
- **AC2** Given the name is empty, the price is negative or the minimum order is below 1, when I submit, then the item is not saved and each invalid field shows an error message. *(limits: ASSUMPTION)*
- **AC3** Given no event category is selected, when I submit, then the item is not saved. *(ASSUMPTION: every item belongs to at least one category, so it appears in C1)*
- **AC4** Given I save an item with "published" unticked, when a visitor opens the menu, then the item is not shown.

### US-02 Edit a food item — **Must**
As an **admin** I want to change any field of an existing food item, so that the menu stays correct when it changes with the season.
- **Trace:** OB4 A1; INT-M "Menus change with the season, four times a year."
- **AC1** Given an existing item, when I change its price and save, then the admin list and the customer menu show the new price.
- **AC2** Given an order already contains the item, when I change the item's price, then that order keeps the price it was submitted with. *(ASSUMPTION: price snapshot on order line)*
- **AC3** Given invalid input, when I save, then the stored item is unchanged and errors are shown.

### US-03 Remove or unpublish a food item — **Must**
As an **admin** I want to remove a food item or hide it from the menu, so that customers cannot order food we no longer offer.
- **Trace:** OB4 A1 "remove … and whether the item is published"; MENU "Rakfisk tasting (seasonal, Nov only)".
- **AC1** Given an item that is in no order, when I delete it and confirm, then it disappears from the admin list and the menu.
- **AC2** Given an item that is part of an existing order, when I try to delete it, then it is not deleted and I am offered to unpublish it instead. *(ASSUMPTION: keeps order history intact)*
- **AC3** Given a published item, when I untick "published" and save, then it is hidden from the menu but still listed (marked as unpublished) in the admin list.

### US-04 Upload a picture for an item — **Must**
As an **admin** I want to upload a picture for a food item and preview it before saving, so that customers see what they order.
- **Trace:** OB4 A2 "Upload a picture for each item … The admin previews the result before it is saved."
- **AC1** Given an item, when I upload a JPG, PNG, WebP or SVG file of at most 2 MB, then a preview is shown and the item's picture is **not yet** changed. *(formats/size: ASSUMPTION)*
- **AC2** Given a preview, when I click *Save*, then the item's picture is replaced and shown on its menu card; when I click *Discard*, then the item keeps its old picture.
- **AC3** Given a file of another type or larger than 2 MB, when I upload it, then it is rejected with a message and nothing is stored.

### US-05 Create or modify a picture from an instruction — **Must**
As an **admin** I want to write an instruction that an AI agent or image service uses to create a new picture or modify the current one, and preview the result, so that every item can have a picture without a photographer.
- **Trace:** OB4 A2 "or write an instruction that an AI agent or image service uses to create or modify the picture"; OB4 §3 "make sure that your project does not include Claude API key".
- **AC1** Given an item, when I submit an instruction, then a generated picture is shown as a preview and the item is unchanged until I click *Save*.
- **AC2** Given the item already has a picture, when I submit an instruction to modify it, then the preview is based on the current picture.
- **AC3** Given no AI service is configured, when I open the instruction form, then a fallback (placeholder) service is used or a clear message is shown; the application does not crash. *(ASSUMPTION — see 01-plan OPEN-4)*
- **AC4** Given the repository, when it is searched for API keys, then none are found (keys come only from environment variables).

### US-06 Browse the menu by kind of event — **Must**
As a **visitor** I want to see the food as cards grouped by kind of event, so that I can find suitable food for my event at any time.
- **Trace:** OB4 C1 "Food items as cards, grouped by kind of event … Each card shows picture, price, minimum order and allergens."; INT-I "Customers must be able to see our menus and prices … at any hour."; E012 "Is your menu available in English with allergens marked?"
- **AC1** Given published items in several categories, when I open the menu, then items are shown as cards under headings such as birthday, confirmation, wedding, conference and julebord.
- **AC2** Given a published item, when it is shown, then its card shows picture (or a placeholder if none), price in NOK, minimum order and allergens.
- **AC3** Given an item in two categories, when I open the menu, then it appears under both headings. *(ASSUMPTION: an item may belong to several categories)*
- **AC4** Given an unpublished item, when I open the menu, then it is not shown.

### US-07 See dietary labels on menu cards — **Could**
As a **customer with dietary needs** I want vegetarian, vegan, gluten-free and similar labels on each card, so that I do not have to guess.
- **Trace:** E019 "Please label gluten-free items clearly on the buffet. Last time we had to guess."; MTG "health-conscious" customer group; OB4 A1 stores "dietary labels" (C1 only requires allergens).
- **AC1** Given an item with dietary labels, when its card is shown, then the labels are visible next to the allergens.

## E2 Cart and ordering

### US-08 Add items to the cart — **Must**
As a **visitor** I want to add food items to a cart, so that I can put together an order for my event.
- **Trace:** OB4 C2 "Add, change and remove items … Quantities below an item's minimum order are not accepted."
- **AC1** Given an item with minimum order 10, when I add it with quantity 10 or more, then it is in the cart with that quantity.
- **AC2** Given an item with minimum order 10, when I add it with quantity 9, then it is not added and I see a message stating the minimum order.
- **AC3** Given the item is already in the cart, when I add it again, then the quantities are added together. *(ASSUMPTION)*

### US-09 Change, remove and see the estimated total — **Must**
As a **visitor** I want to change quantities, remove items and see the estimated total cost, so that I know roughly what the event will cost.
- **Trace:** OB4 C2 "with an estimated total cost"; E015 "We need a quote … by Friday for internal approval."
- **AC1** Given a cart, when I open it, then each line shows price × quantity and the page shows an estimated total in NOK equal to the sum of the lines.
- **AC2** Given a cart line, when I change the quantity to a value at or above the minimum, then the line and total are recalculated; when I change it to a value below the minimum, then the change is rejected with a message and the old quantity is kept.
- **AC3** Given a cart line, when I remove it, then it disappears and the total is updated.
- **AC4** Given an item in my cart is unpublished by an admin, when I open the cart, then the item is removed and I am told why. *(ASSUMPTION)*

### US-10 Register as a customer — **Must**
As a **visitor** I want to register an account, so that I can submit orders and follow them later.
- **Trace:** OB4 C3 "Log in (or register)"; IT "No customer database; customer details only in e-mail threads".
- **AC1** Given a new e-mail address and a valid password, when I register, then my account is created and I am logged in.
- **AC2** Given an e-mail address that is already registered, when I register, then no account is created and I see an error.
- **AC3** Given a registered account, when the stored data is inspected, then the password is stored only as a hash. *(also NFR, step 4)*

### US-11 Log in and out — **Must**
As a **customer** I want to log in and out, so that only I can submit and see my orders.
- **Trace:** OB4 C3; OB4 §3 "Only customer login pages are fine."
- **AC1** Given a registered account, when I log in with the correct password, then I am logged in; with a wrong password, then I see a general error that does not reveal whether the e-mail exists. *(error wording: ASSUMPTION)*
- **AC2** Given I am not logged in and have items in the cart, when I go to checkout, then I am sent to log in or register and afterwards returned to checkout with my cart unchanged. *(return to checkout and kept cart: ASSUMPTION)*
- **AC3** Given I am logged in, when I log out, then pages that need login send me to the login page.

### US-12 Submit an order — **Must**
As a **customer** I want to submit my cart as an order with event date, number of guests and delivery address, so that Ekte Mat receives my request at any hour and it is not lost.
- **Trace:** OB4 C3 "submit the order: event date, number of guests, delivery address … No payment solution is needed."; INT-I "We lose inquiries."; E006 "I sent a request 6 days ago and have not heard back."; E011 "We never got a confirmation e-mail."
- **AC1** Given I am logged in with a non-empty cart, when I submit a valid order form, then an order is stored with status *submitted* and payment status *not paid*, my cart is emptied, and I see a confirmation page with the order number. *(initial statuses follow OB4 A3; order number and confirmation page: ASSUMPTION)*
- **AC2** Given an event date in the past or a number of guests below 1, when I submit, then the order is not stored and the errors are shown. *(ASSUMPTION; proposed rules DV-01, DV-04)*
- **AC3** Given an empty cart, when I open checkout, then I cannot submit and am sent back to the menu. *(ASSUMPTION)*
- **AC4** Given the checkout, when I submit, then no payment step is shown.

### US-13 Allergy and dietary notes per guest group — **Must**
As a **customer** I want to describe allergies and diets per guest group, so that the kitchen knows exactly what to prepare and nobody gets ill.
- **Trace:** OB4 C3 "allergy and dietary notes per guest group"; INT-S "Every order has to show allergies and diets per guest group … We had a nut incident in 2024"; GDPR "Store per guest group, not per named guest"; E002 "To av gjestene har nøtteallergi og en er cøliaki."
- **AC1** Given the order form, when I add two or more guest groups with a label, number of guests, allergies and dietary notes, then all groups are stored with the order and shown on the confirmation.
- **AC2** Given guest groups whose counts add up to more than the number of guests, when I submit, then the order is rejected with a message. *(ASSUMPTION)*
- **AC3** Given the order form, when I look at the guest-group fields, then there is no field for a guest's name.

## E3 Order management

### US-14 See and filter all orders — **Must**
As an **admin** I want a list of all customer orders that I can filter by status and event date, so that I have one reliable overview instead of e-mail, Excel and printouts.
- **Trace:** OB4 A3 "A list of all customer orders that can be filtered by status and event date"; INT-I "I want a proper order overview for the kitchen"; ASIS step 7 "Coordinator prints the order and pins it on the kitchen board."; VIS "one reliable overview of every order and allergy".
- **AC1** Given orders with different statuses, when I filter by one status, then only orders with that status are listed.
- **AC2** Given orders on different event dates, when I filter by a date range, then only orders with an event date inside the range are listed.
- **AC3** Given no filter, when I open the list, then all orders are listed sorted by event date, each with order number, customer, event date, guests, status and payment status. *(sorting and columns: ASSUMPTION)*

### US-15 Manage an order and its status — **Must**
As an **admin** I want a page per order where I can see all details and move the order through its statuses, so that customers and staff always know where an order stands.
- **Trace:** OB4 A3 "a page per order to manage it: order status (submitted → approved → in preparation → delivered, or rejected/cancelled)"; INT-S "Sometimes I forget."; ASIS step 8 "(sometimes forgotten)".
- **AC1** Given an order, when I open its page, then I see customer, event date, guests, delivery address, order lines, total and every guest group with allergies highlighted.
- **AC2** Given an order with status *submitted*, when I change it to *approved* or *rejected*, then the new status is saved and shown.
- **AC2b** Given an *approved* order, when I change it to *in preparation* and later to *delivered*, then each status is saved and shown in that order.
- **AC3** Given an order with status *delivered*, *rejected* or *cancelled*, when I try to change its status, then the change is refused. *(transition rules: ASSUMPTION, see OQ-04)*
- **AC4** Given an order that is not final, when I set it to *cancelled*, then it is saved as cancelled. *(which states allow cancel: ASSUMPTION)*
- *(AC1 "allergies highlighted" on the admin order page: ASSUMPTION — supports INT-S "the kitchen must confirm they have seen it")*

### US-16 Set payment status — **Must**
As an **admin** I want to set the payment status of an order, so that we can track deposits and invoices without a payment solution.
- **Trace:** OB4 A3 "payment status (e.g. not paid, deposit paid, invoiced, paid)"; OB4 C3 "No payment solution is needed."; INT-I "30 % deposit"; INT-S "corporate clients hate prepayment"; ASIS step 6 "sends a Vipps payment request for a deposit (sometimes forgotten)". Resolves CF-01 for Oblig 4.
- **AC1** Given a new order, when it is created, then its payment status is *not paid*.
- **AC2** Given an order, when I choose *not paid*, *deposit paid*, *invoiced* or *paid* and save, then that payment status is stored and shown on the order list and order page.

### US-17 See my orders — **Must**
As a **customer** I want to see my own orders with their current status and payment status, so that I do not have to e-mail or phone to ask.
- **Trace:** OB4 C4 "The customer's own orders with their current status … and payment status."; E011 "Is our order for tomorrow confirmed?"; E003 "I called yesterday but nobody picked up."
- **AC1** Given I am logged in and have orders, when I open "My orders", then I see each of my orders with order number, event date, status and payment status, and no orders of other customers.
- **AC2** Given another customer's order ID, when I open its page, then I get "not found". *(OB4 "own orders"; 404 rather than 403: ASSUMPTION)*
- **AC3** Given an admin has changed my order's status or payment status, when I reload "My orders", then I see the new values.

## E4 Questions

### US-18 Ask a question about an order — **Must**
As a **customer** I want to ask a question about a specific order, so that the question is linked to the order and not lost in e-mail.
- **Trace:** OB4 C5 "Ask a question about a specific order"; INT-I "We lose inquiries."; E013 "What are your cancellation terms?"; E003.
- **AC1** Given one of my orders, when I submit a question, then it is stored with date and time and shown on the order page.
- **AC2** Given an empty question, when I submit, then nothing is stored and I see an error. *(ASSUMPTION)*
- **AC3** Given another customer's order, when I try to post a question to it, then it is refused. *(ASSUMPTION)*

### US-19 Read Ekte Mat's answer — **Must**
As a **customer** I want to read Ekte Mat's answer under my question, so that I have the answer in one place.
- **Trace:** OB4 C5 "and read Ekte Mat's answer".
- **AC1** Given my question has been answered, when I open the order page, then the answer and its date are shown under the question.
- **AC2** Given my question has not been answered, when I open the order page, then it is marked as waiting for an answer.

### US-20 Read and answer customer questions — **Must**
As an **admin** I want to see all customer questions, unanswered first, and answer them, so that customers get quick replies even in peak season.
- **Trace:** OB4 A4 "Read and answer customers' questions about their orders."; INT-S "On a normal week one or two days. In December and in May it can be a week. People get annoyed."; ORD median reply time 22 h (00-analysis).
- **AC1** Given unanswered and answered questions, when I open the question list, then all questions are listed, unanswered first, each with a link to its order. *(order of list: ASSUMPTION)*
- **AC2** Given a question, when I submit an answer, then the answer is stored with my user and the time, and the customer sees it (US-19).
- **AC3** Given an empty answer, when I submit, then nothing is stored. *(ASSUMPTION)*

## E5 Access and running the system

### US-21 Restrict the admin panel to staff — **Must**
As the **owner** I want only Ekte Mat staff to use the admin panel, so that customer and allergy data are protected.
- **Trace:** GDPR "Allergy and dietary information … can be health data"; INT-F "Our IT department will ask where our data is stored"; OB4 §3 "Only customer login pages are fine." *(ambiguous — admin login is an ASSUMPTION, see OQ-08)*
- **AC1** Given I am a logged-in customer, when I open any `/admin` page, then access is refused (403).
- **AC2** Given I am not logged in, when I open any `/admin` page, then I am sent to the login page.
- **AC3** Given I am logged in as admin, when I open `/admin`, then I see the admin panel.

### US-22 Install, seed, run and test from the README — **Must**
As an **assessor** I want to set up the application with a few documented commands and synthetic sample data, so that I can check every feature.
- **Trace:** OB4 §3 "A seed script creates sample food items, an admin and test customers, and the README gives the commands to install, seed, run and test the application."; OB4 "To be approved: the application should be executable".
- **AC1** Given a fresh clone, when I follow the README, then I can install, seed, run and test with the listed commands.
- **AC2** Given the seed script has run, when I open the app, then there are sample food items in several event categories, one admin account and at least two test customers, all synthetic. *(numbers: ASSUMPTION)*
- **AC3** Given the seed script runs twice, when I open the menu, then items are not duplicated. *(ASSUMPTION)*

## E6 Going further — official optional ideas (Should)

Priority order for the team if time allows: US-23, US-24, US-26, then US-25, US-27 (01-plan §1).

### US-23 Kitchen view of today's orders — **Should**
As the **head chef** I want one screen with today's orders, portions per dish and allergies highlighted, so that the kitchen prepares the right food safely.
- **Trace:** OB4 §2 "a kitchen view of the day's orders with allergies highlighted (Mateo)"; INT-M "For each day: which orders, how many portions of each dish, allergies in red."
- **AC1** Given approved or in-preparation orders for today, when I open the kitchen view, then I see each order with portions per dish and every guest group's allergies in red.
- **AC2** Given orders on other days or with status submitted/rejected/cancelled, when I open the kitchen view, then they are not shown.

### US-24 Check the daily kitchen capacity — **Should**
As the **event coordinator** I want to be warned when an order would exceed the kitchen's daily capacity, so that we do not overbook.
- **Trace:** OB4 §2 "a check against the kitchen's daily capacity (Sunniva)"; INT-S "about 400 covers a day, 250 if there is a wedding with a served dinner"; ORD 20 days above capacity (00-analysis).
- **AC1** Given approved orders for a date totalling 380 guests, when I approve an order for 30 guests on that date, then I see a capacity warning.
- **AC2** Given a served wedding dinner on a date, when the total for that date exceeds 250 guests, then the warning is shown. *(hard block vs warning: see CF-07)*

### US-25 Company account that copies last week's order — **Should**
As a **corporate office manager** I want to copy last week's order, so that I do not have to type the same lunch order every week.
- **Trace:** OB4 §2 "company accounts that can copy last week's order (Fjordtek)"; INT-F "copy last week's order"; E028 "Could we just get exactly the same as our order in September?"; E007.
- **AC1** Given a previous order, when I choose "copy", then the cart is filled with the same items and quantities (published items only).
- **AC2** Given a company with several users, when one user orders, then other users of the same company can see the order. *(company model: ASSUMPTION)*

### US-26 Norwegian/English interface — **Should**
As a **customer** I want to use the site in Norwegian or English, so that both local and international guests can order.
- **Trace:** OB4 §2 "a Norwegian/English interface"; IT "Norwegian and English UI"; E012 "Our company has many international employees."
- **AC1** Given the language switch, when I choose English or Norwegian, then all fixed texts on customer pages are shown in that language.

### US-27 Origin of the food on every card — **Should**
As a **customer** I want to see where the food comes from, so that I can choose local, honest food.
- **Trace:** OB4 §2 "the origin of the food on every card (Ingrid)"; INT-I "where the lamb or the fish comes from - the farm, the boat."; E008 "Which farm is the lamb from?"
- **AC1** Given an item with an origin text (e.g. "Lamb from Voss"), when its card is shown, then the origin is visible.

## E7 Other data-pack needs (Could)

| ID | Story | Trace |
|---|---|---|
| US-28 | As a customer I want to choose pick-up instead of delivery, so that I can collect the food myself. | E014 "Kan vi hente maten selv i stedet for levering?"; ORD `delivery_method` Pick-up in 126 of 820 orders |
| US-29 | As a customer I want a confirmation e-mail when I submit an order, so that I know it was received. | E011 "We never got a confirmation e-mail." |
| US-30 | As a customer I want to change guest numbers and allergies before a deadline, so that I do not have to phone. | VIS "book and change orders any time"; INT-F "change the number of people until 10:00 the day before"; CF-04, CF-05 |
| US-31 | As an admin I want to register an order on behalf of a phone customer, so that customers without internet can still order. | E024 "Kan jeg fortsatt bestille på telefon?"; CF-02 |

## Not in this release (Won't)

| ID | Need | Trace | Reason |
|---|---|---|---|
| W-01 | Online deposit/payment with Vipps | INT-I "Vipps for private customers, definitely."; E009 | OB4 C3 "No payment solution is needed." |
| W-02 | Invoices to Fiken, EHF with PO/cost-centre | INT-I (Fiken); INT-F "One EHF invoice per month"; E004 | Integration outside Oblig 4 |
| W-03 | Approval of company orders above 15 000 NOK | INT-F "only I should approve anything above 15 000 NOK" | Needs company model (US-25) first |
| W-04 | Standing (recurring) orders | E007 "lunch for 12 every Tuesday"; INT-F "standing orders" | Outside Oblig 4; US-25 covers copy |
| W-05 | Automatic reminders 7 days before the event | INT-S "automatic reminders … seven days before the event" | Needs e-mail sending/scheduling |
| W-06 | Kitchen prep list (kg per ingredient, 3 days) | INT-M "total kilos of each ingredient for the next three days" | Needs ingredient model |
| W-07 | Kitchen screen offline, PIN login | INT-M "The kitchen must still see today's orders."; "a PIN is fine" | Outside Oblig 4 |
| W-08 | GDPR self-service access/deletion, retention | GDPR; E010; INT-F | Synthetic data only in Oblig 4 |
| W-09 | Show free dates to customers | E001 "Is it possible to see online which dates are free?" | Depends on US-24 |
| W-10 | ESG/CO₂ data per order | E021 | No data source |
