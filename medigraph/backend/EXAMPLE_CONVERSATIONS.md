# Medigraph Chatbot - Example Conversations

Example conversations demonstrating the Medigraph chatbot capabilities.

## 1. Follow-up Questions

**User:** "What are symptoms of hypertension?"
**Bot:** "The symptoms of hypertension include: Headache, Dizziness, Chest pain, and Shortness of breath. (Found 4 symptoms in the knowledge graph)"
**Confidence:** High confidence
**Explanation:** These symptoms are directly connected to Hypertension in the medical knowledge graph. Found 4 associated symptoms.

**User:** "How is it treated?"
**Bot:** "Hypertension can be treated with: Lisinopril, Amlodipine, Metoprolol, and Hydrochlorothiazide. (4 treatment options available)"
**Confidence:** High confidence
**Explanation:** These treatments are documented treatments for Hypertension. The graph contains 4 treatment options.
**Suggestions:** You might also ask: [Learn more about Hypertension] [Check drug interactions]

---

## 2. Disease Prediction

**User:** "I have chest pain and shortness of breath"
**Bot:** "Based on your symptoms (chest pain, shortness of breath), possible conditions include: Hypertension (Severe cardiovascular), Asthma (Moderate respiratory), and COPD (Severe respiratory). (Found 3 matching conditions)"
**Confidence:** Good confidence
**Explanation:** Disease prediction based on matching your symptoms (chest pain, shortness of breath) against the knowledge graph. 3 conditions match.
**Suggestions:** You might also ask: [Get detailed information about each condition] [Learn about treatment options]

---

## 3. Drug Interactions

**User:** "Does warfarin interact with aspirin?"
**Bot:** "Yes, Warfarin and Aspirin may interact. This is a Severe interaction. Consult your healthcare provider."
**Confidence:** High confidence
**Explanation:** Interaction data found between Warfarin and Aspirin in drug relationship graph.
**Suggestions:** You might also ask: [Check side effects] [Find alternatives]

---

## 4. Find Diseases by Symptom

**User:** "What diseases cause fever?"
**Bot:** "Diseases associated with 'fever': Influenza (Moderate infectious), Pneumonia (Moderate infectious), and Hepatitis (Moderate infectious). (Found 3 matching conditions)"
**Confidence:** High confidence
**Explanation:** Diseases were found by matching the symptom 'fever' in the knowledge graph. 3 diseases share this symptom.
**Suggestions:** You might also ask: [Get treatment options for these diseases] [Learn about prevention]

---

## 5. Getting Disease Information

**User:** "Tell me about Alzheimer's disease"
**Bot:** "Alzheimer's is a severe neurodegenerative condition. It is the most common cause of dementia. Common symptoms include: Memory loss, Confusion, and Behavioral changes."
**Confidence:** High confidence
**Explanation:** Information retrieved from the medical knowledge graph for Alzheimer's.
**Suggestions:** You might also ask: [View the knowledge graph] [Find related conditions]

---

## 6. Related Diseases

**User:** "Find diseases similar to Parkinson's"
**Bot:** "Diseases related to Parkinson's: Alzheimer's (Severe neurodegenerative), Dementia (Moderate neurodegenerative), and Epilepsy (Moderate neurological). (3 related conditions)"
**Confidence:** Good confidence
**Explanation:** Related diseases found by analyzing shared symptoms and category with Parkinson's. 3 related conditions.
**Suggestions:** You might also ask: [Learn more about Parkinson's treatments] [View Parkinson's symptoms]

---

## 7. Treatment Options

**User:** "How is diabetes treated?"
**Bot:** "Diabetes can be treated with: Metformin, Insulin, and Atorvastatin. (3 treatment options available)"
**Confidence:** High confidence
**Explanation:** These treatments are documented treatments for Diabetes. The graph contains 3 treatment options.
**Suggestions:** You might also ask: [Learn more about Diabetes] [Check drug interactions] [View Diabetes symptoms]

---

## 8. Empty Results Handling

**User:** "What are symptoms of unknown disease?"
**Bot:** "I couldn't understand that. Try: 'What are symptoms of diabetes?', 'How is hypertension treated?', 'What diseases cause chest pain?'"
**Confidence:** No confidence
**Explanation:** The query could not be processed.

---

## Architecture Flow

```
User Query
    │
    ▼
┌─────────────────┐
│  NLP Processor  │ ─── Intent Detection + Entity Extraction
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Query Service  │ ─── Execute Cypher Query on Neo4j
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ Response Generator   │ ─── Template-based Natural Language Response
└──────────┬───────────┘
           │
           ▼ (optional)
┌─────────────────┐
│   LLM Service   │ ─── Ollama or OpenAI enhancement (if enabled)
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│  Context Manager     │ ─── Store conversation context for follow-ups
└──────────────────────┘
```

## Key Features

### Explainability
Every response includes an "explanation" that explains WHY the answer was given based on the graph data.

### Confidence Scoring
- **High confidence (0.8+)**: Exact match, good data quality
- **Good confidence (0.6-0.8)**: Good match with multiple results
- **Moderate confidence (0.5-0.6)**: Base confidence
- **Low confidence (<0.5)**: Limited matches
- **No confidence (0)**: Error or no data

### Follow-up Context
The chatbot remembers the last discussed disease/symptoms and uses them for context-aware follow-up questions.

### Suggestions
After each response, helpful follow-up suggestions are provided to guide the user.

### LLM Enhancement (Optional)
When enabled, the template-based response can be enhanced by an LLM (Ollama or OpenAI) while always grounding in the graph data.
