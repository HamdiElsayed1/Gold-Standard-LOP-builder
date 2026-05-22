# Agentic Solution Input - Transcribed Notes

_Source: handwritten workshop canvas photographed on paper._

## 1) Persona
**Question on sheet:** What will be the persona of this agent?

- Structured
- Output focused
- Expert always available

## 2) Role
**Question on sheet:** What is their role? What are their areas of expertise?

- Assistant / fellow for LOP building

## 3) Scenario
**Question on sheet:** What is the scenario in which the squad is inserted?

- Beach resource with limited context asked to deliver
- LOP winner on tight timeline
- Partners have context and limited time

## 4) Transformation Area
**Question on sheet:** What is the area of transformation being addressed within the software development lifecycle (SWE)?

- Beach resource / client development

## 5) Evaluation
**Question on sheet:** Describe the criteria, metrics, or validation methods that will be used to evaluate the agent's effectiveness and performance. Consider how to measure success, impact, or quality.

- Win rate
- Time saved
- Quality of output
- Time spent
- Faults

## 6) Agent Guidance
**Question on sheet:** Description of what the agent does

- An agent that helps speed up high-standard LOP generation
- Gathers CST and client input

## 7) Workflow
**Question on sheet:** Briefly describe how the work flows from start to finish, including how the agent interacts with humans and other tools throughout the process.

### Inputs / contents to gather
- Context and objectives
- Why McKinsey?
  - Have we done this before? / comparable cases (written as “have we done this 100x?” or similar; handwriting unclear)
- Team
- Credentials
- Market trends
- Approach
- Fees
- Appendix
  - References
  - Team CVs

### Guidance / structuring inputs
- Guidelines
  - Per chapter guidelines
  - Best practices
  - Stakeholders
  - Specific sources

### Main workflow
1. Human data gathering
   - Voice inputs 
2. Squad synthesizing
   - Problem statement
3. Draft output
   - Clarifying questions
   - Contents table
4. Feedback loop
5. Output

### Supporting artifact
- Progress tracker

### “Our Workflow” line at the bottom of the page
1. Workflow
2. Information gathering
3. Identify agents
4. Divide work
5. Work on elements
6. Review / iterate

## 8) Tools (Ferramentas)
**Question on sheet:** Tools are like the “hands” of the agent. What tools does the agent need to perform its actions?

- LOP coach to check output
- PPT / Excel / HTML
- Connectors to Know / MVI (McKinsey Value intelligence) 
- Connectors to web
- Voice to text
- Email connector

## 9) Data Sources
**Question on sheet:** Which data sources do the squad and agents need access?

- Best practice LOPs
  - Competitive vs non-competitive
  - Explorative
  - Building on relationship
- Tenders / RFP
- CST context / previous work
- Partner input
- Market input

## 10) Output
**Question on sheet:** Is there an expected output? A specific output format?

- Winning LOP, PPT / HTML

## 11) Risks and Errors
**Question on sheet:** List the possible problems, failures, or risks that the agent may face during its operation.

- Hallucination
- Wrong prioritization of input  
- Opposing inputs

## 12) Suggested Structured Schema for Agent Design
Below is the same content reformatted as a concise build-ready schema.

```yaml
persona:
  - structured
  - output_focused
  - expert_always_available

role:
  title: assistant_fellow_for_lop_building

scenario:
  - beach_resource_with_limited_context
  - asked_to_deliver_fast
  - lop_winner_on_tight_timeline
  - partners_have_context_but_limited_time

transformation_area:
  - beach_resource_enablement
  - client_development

evaluation_metrics:
  - win_rate
  - time_saved
  - quality_of_output
  - time_spent
  - faults

agent_guidance:
  purpose:
    - speed_up_high_standard_lop_generation
    - gather_cst_and_client_input

workflow:
  required_inputs:
    - context_and_objectives
    - why_mckinsey
    - prior_examples_or_comparable_cases
    - team
    - credentials
    - market_trends
    - approach
    - fees
    - appendix
    - references
    - team_cvs
  structuring_guidance:
    - per_chapter_guidelines
    - best_practices
    - stakeholders
    - specific_sources
  process_steps:
    - human_data_gathering
    - squad_synthesizing
    - draft_output
    - clarifying_questions
    - contents_table
    - feedback_loop
    - final_output
  support_tools:
    - progress_tracker
  operating_model:
    - information_gathering
    - identify_agents
    - divide_work
    - work_on_elements
    - review_and_iterate

tools:
  - lop_coach_output_checker
  - ppt
  - excel
  - html
  - connectors_to_internal_knowledge
  - web_connectors
  - voice_to_text
  - email_connector

data_sources:
  - best_practice_lops
  - tender_and_rfp_materials
  - cst_context
  - previous_work
  - partner_input
  - market_input
  - relationship_based_examples
  - competitive_and_non_competitive_examples
  - explorative_examples

output:
  primary: winning_lop
  formats:
    - ppt
    - html

risks_and_errors:
  - hallucination
  - wrong_prioritization_of_input
  - conflicting_or_opposing_inputs
```

## 13) Notes on Unclear Handwriting
A few phrases were difficult to read with full certainty. The most uncertain items are:

- “Have we done this 100x?” under **Why McKinsey?**
- “Connectors to Know / MVI” under **Tools**
- “Wrong prio of input” under **Risks and Errors**
- “Voice inputs (7 zones)” under **Workflow**

These have been transcribed as faithfully as possible while keeping the file usable for solution design.
