# Context Genie prototypes

This project demonstrates a high-fidelity “Context Genie” keyboard prototype alongside a control design, powered by a lightweight Python backend that returns multilingual autocorrect suggestions. Designers can supply their own OpenAI-style API key or rely on built-in heuristics.

## Backend

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```
2. Run the API:
   ```bash
   uvicorn backend.app:app --reload
   ```
3. _Optional:_ set `OPENAI_API_KEY` or enter a key from the Genie overlay to enable LLM-powered suggestions. You can also customize the model via `CONTEXT_GENIE_MODEL`.

## Frontend prototypes

1. Serve the HTML files (`context-genie-prototype.html` and `control-group-prototype.html`) so the browser allows `fetch` (e.g., `python3 -m http.server 5173` from the repo root).
2. Open each prototype in a browser tab.
3. In the Genie overlay:
   - Toggle the slider to switch passive/balanced/aggressive modes.
   - Choose a tone (casual/neutral/formal) and flip the transliteration switch to force non-English text into Latin characters.
   - Enter an API key (e.g., OpenAI `sk-...`) if you want live LLM suggestions; the key stays in local storage.
   - Add languages by choosing from the dropdown, remove them with the `×` on each pill, and reset to defaults anytime; the active list drives backend requests.
4. Type within the composer to see backend suggestions and autocorrect behavior; the control prototype hits a simpler endpoint that mimics stock autocorrect chips.

## Notes

- The backend defaults to fast heuristics when no key is provided.
- Both prototypes expect the backend at `http://localhost:8000/api`. Update `API_BASE_URL` in the HTML if you serve the API elsewhere.
- Run `python3 -m compileall backend/app.py` before demos to verify syntax.
- The backend now accepts `tone` (`casual`, `neutral`, `formal`) and `transliteration` flags so you can steer formality and Latin transliteration preferences.
