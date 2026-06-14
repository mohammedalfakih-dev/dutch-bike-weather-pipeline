# AI Assistance Log

Document every time you used an AI tool during this project: what you asked, what it gave you, and what you changed before using it.

This is not about proving you worked hard. It is about building the habit of treating AI output as a first draft, not a final answer.

## Tools used

<!-- List the AI tools you used, e.g. Claude, GitHub Copilot, ChatGPT -->

## Claude, ChatGPT, GitHub Copilot

## Log

<!-- One entry per significant AI interaction. Add as many as you need. -->

### Entry 1

**What I asked:** <!-- Paste or summarise the prompt -->
I asked for a few ideas for a live API data pipeline that would fit the project requirements.
**What it gave me:** <!-- Summarise the output -->
It suggested a few possible project ideas, such as a weather pipeline, an air quality pipeline, a public transport pipeline, a currency exchange pipeline, and an events or city data pipeline. One idea was a Dutch Bike Weather Pipeline.
**What I changed:** <!-- What you added, removed, or corrected before using it -->
chose the Dutch Bike Weather Pipeline because I liked the idea of using weather data for something practical and easy to understand. Since cycling is very common in the Netherlands, the project felt realistic and useful. I adapted the idea to fetch weather forecasts for Dutch cities and calculate my own bike score and bike advice.

---

### Entry 2

**What I asked:**

I asked for help with the data model and validation.

**What it gave me:**

It suggested using a Pydantic model for one weather reading, with fields like city, forecast time, temperature, precipitation, wind speed, and weather code. It also suggested including bike score and bike advice as part of the model.

**What I changed:**

I adjusted the model to match only the exact raw data I fetch from Open-Meteo. I decided not to put `bike_score` and `bike_advice` in the Pydantic model, because those values are not coming from the API. Instead, I calculate them later in the pandas transformation step. I also added tests for valid data, negative precipitation, empty city names, and invalid timestamps.

---

### Entry 3

**What I asked:**

I asked for debugging help when local commands failed, including `psql` not being found, Azure Storage connection string problems, and Docker environment behavior.

**What it gave me:**

It explained how to add PostgreSQL `bin` to PATH on Windows/Git Bash, how quoted connection strings behave differently in Bash and Docker `--env-file`, and how to verify Blob Storage output.

**What I changed:**

I applied the fixes manually, reran the pipeline, checked Postgres with SQL queries, and confirmed that raw JSON files were uploaded to Blob Storage.

---

### Entry 4

**What I asked:**

I asked for help checking my Docker setup and understanding why the container was downloading packages when it started.

**What it gave me:**

It explained that using uv run in the Docker command could cause the environment to be checked again at runtime. It suggested using the virtual environment created during the Docker build.
**What I changed:**

I updated the Dockerfile, rebuilt the image, and tested it again. After that, the container ran successfully and uploaded data to both Postgres and Blob Storage.

---

### Entry 5

**What I asked / how I used it:**

I used GitHub Copilot autocomplete while writing some parts of the code. I did not ask it to design the full project, but I used its suggestions when it predicted code that matched what I was already planning to write.
**What it gave me:**

t suggested small completions, such as parts of function bodies, comments, docstrings, repeated field names, and similar lines

**What I changed:**

I only accepted suggestions that I understood and agreed with. I checked the suggested code against my own project logic, changed names or values when needed, and tested the project afterwards with Ruff, pytest, Docker, Postgres, and Blob Storage verification.

---

### Entry 6

**What I asked:**

I asked for help updating the README so it matched my actual project instead of the starter template placeholders.

**What it gave me:**

It suggested wording for the project description, architecture, local run instructions, Docker instructions, Azure deployment commands, and verification queries.

**What I changed:**

kept the same README structure from the starter template and replaced the placeholder values with my actual project details, such as my table name, schema, Docker image, Blob Storage prefix, and Container App Job name.

---
