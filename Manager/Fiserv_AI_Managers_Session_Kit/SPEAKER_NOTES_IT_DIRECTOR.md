# IT Director Speaker Notes — AI Agents Presentation
## For Fiserv EMEA IT Directors (35-Minute Session)

**Purpose:** Concise, technical, team-focused speaking cues. Use as reference during presentation.

**Format:** Key message → Talking points → Simple guidance

---

## SLIDE 1: Title Slide (1 minute)

**Key Message:** Practical implementation, team impact, secure deployment

**Talking Points:**
- "Today is about enabling IT teams to use AI agents safely and productively."
- "Not high-level strategy — real workflows."

**Guidance:** Keep it short, 1 minute max

---

## SLIDE 2: What AI Agents Actually Do (2 minutes)

**Key Message:** Simple explanation — engineering assistants

**Talking Points:**
- "Explain simply — no deep maths. Emphasise that these are engineering assistants, not magic."
- "LLM = Brain, RAG = IT Documentation Warehouse, Agent = The Engineer Assistant, Tools = Scripts, APIs, CLI commands"

**Guidance:** Keep it simple, focus on what agents do. This is foundational — they need to understand what agents are before we talk about threats.

**Transition:** "So why do IT teams need this? Let me show you the pressure."

---

## SLIDE 3: Why IT Needs This Now (2 minutes)

**Key Message:** IT teams are overloaded, competitors are automating

**Talking Points:**
- "Your teams are overloaded. AI agents directly reduce workload in ops, DevOps, monitoring, and ITSM."
- "Competitors are already doing this."
- "Agentic AI can remove 30-50% manual effort in ticket triage, code review, environment provisioning."

**Guidance:** Keep it moving, focus on team impact

**Transition:** "Now let me show you what these agents can actually do for your teams."

---

## SLIDE 4: Practical IT Automations (Realistic) (4 minutes)

**Key Message:** Real workflows, real time savings

**Talking Points:**
- "These are not hypothetical. These can be implemented in 30 days with current tools."
- "Automated MR Review, Incident Triage, Infrastructure Diagnostics, ITSM Ticket Processing"

**Guidance:** Emphasize these are real, practical automations, not theoretical

**Transition:** "But we need to work within Fiserv constraints. Let me show you what that means."

---

## SLIDE 5: Fiserv-Relevant Considerations (3 minutes)

**Key Message:** Compliance requirements and IT stack realities

**Talking Points:**
- "Make it Fiserv-specific. They care about internal constraints."
- "Azure OpenAI, GitLab, internal proxies, German compliance."
- "Your teams need to log all agent actions. Complete audit trails."

**Guidance:** Keep it brief, focus on Fiserv constraints and compliance

**Transition:** "Now that you understand what agents are and what they can do, let me show you why governance matters."

---

## SLIDE 6: Where Anthropic's AI-Espionage Incident Matters to IT (5 minutes)

**Key Message:** Real-world threat to CI/CD pipelines and IT workflows

**Talking Points:**
- "Now that you understand what agents are, here's why governance matters."
- "Attackers used an agentic model to scan networks, generate exploits, move laterally, extract credentials — automatically."
- "This same pattern could target your GitLab pipelines."
- "Agents could be tricked into pulling wrong repositories or executing harmful commands."
- "Use the incident to highlight why governance matters. Don't scare — educate."

**Guidance:** Let the gravity sink in, but don't panic. Now they understand what agents are, so the threat has context.

**Transition:** "So how do we control this? Let me show you MCP."

---

## SLIDE 7: MCP (Model Context Protocol) for IT (3 minutes)

**Key Message:** MCP is the safety barrier — controlled and auditable

**Talking Points:**
- "MCP is your safety barrier. It's essentially RBAC for AI. Directors love hearing 'controlled' and 'auditable'."
- "MCP turns LLMs into safe, controlled, auditable engineering assistants."
- "MCP = gateway that ensures AI cannot misuse infrastructure."

**Guidance:** Focus on safety and control, not technical details

**Transition:** "Let me show you the complete architecture."

---

## SLIDE 8: Architecture of an IT-Safe Agent (3 minutes)

**Key Message:** Architecture that works within Fiserv constraints

**Talking Points:**
- "Show that everything is controlled. Directors worry about AI running wild — reassure them."
- "Sandboxed execution, tool whitelisting, complete audit trails."
- "Pattern: Agent → MCP → Azure OpenAI → Internal APIs"

**Guidance:** Focus on control and safety, reassure about governance

**Transition:** "But we need governance. Let me show you what IT Directors must implement."

---

## SLIDE 9: Governance IT Directors Must Implement (5 minutes)

**Key Message:** Built-in governance and security controls

**Talking Points:**
- "End with actions they must take. IT Directors need clear next steps."

**Transition:** "Now let me be specific about what your teams should start doing next week."

---

## SLIDE 10: What Your Teams Should Start Doing Next Week (3 minutes)

**Key Message:** Immediate actions for IT teams

**Talking Points:**
- "Week 1: Identify 3 workflows. Assign one team member."
- "Audit where LLMs are used informally. Establish standards."

**Guidance:** Be specific about actions, not implementation details

---

## SLIDE 11: Investment & Team Impact (2 minutes)

**Key Message:** Small investment, big team impact

**Talking Points:**
- "40-60% reduction in manual work. 70-80% time savings for GitLab MR review."
- "€50K-€100K for pilots. Positive ROI in 60 days."

**Guidance:** Keep it brief, focus on team impact and ROI

---

## SLIDE 12: The Ask — 3 Decisions (2 minutes)

**Key Message:** Three clear decisions this week

**Talking Points:**
- "I need three decisions from you this week."
- "Pilot approval. Team assignment. Workflow identification."
- "Your teams can start building next week."

**Guidance:** Be clear and direct about what you need

---

## SLIDE 13: Q&A (10 minutes)

**Key Message:** Address technical questions, reinforce team impact

**Prepared Answers:**

**Q: How does this integrate with GitLab?**  
A: "MCP provides secure API access. Agents can review MRs, analyze code, check security. All actions logged and auditable."

**Q: What about Azure OpenAI costs?**  
A: "Per-request pricing. Estimated €5K-€10K/month for pilots. Scales with usage. ROI covers costs within 60 days."

**Q: How do we prevent credential exposure?**  
A: "Sandboxing prevents direct system access. Tool whitelisting. No hardcoded secrets. MCP scoped permissions. All credentials managed securely."

**Q: What if agents make wrong decisions?**  
A: "HITL gates for high-risk operations. Rollback procedures. Complete audit trails. We can suspend agents immediately if needed."

**Q: How do we measure success?**  
A: "Time saved, accuracy improvement, false positive reduction, ROI metrics. We set baselines, measure improvement. Data-driven."

**Q: What about team training?**  
A: "We provide training on MCP, Azure OpenAI, agent architecture. One team member becomes expert, trains others. Phased approach."

**Ending:**
- "Thank you for your time and attention."
- "Let's build this together. Your teams can start next week."
- "I'll send a follow-up email with team assignment coordination. Please respond with workflow priorities by [date]."

---

## General Delivery Tips

### Opening (Slides 1-3)
- Smart, confident, practical
- Establish understanding first (what are agents?)
- Then create motivation (why do we need them?)
- Keep momentum, don't get bogged down

### Middle (Slides 4-8)
- Show value (practical automations)
- Set context (Fiserv constraints)
- Introduce risk (Anthropic incident — now they understand the threat)
- Show control (MCP and architecture)

### Governance (Slide 9)
- Focus on what they need to do
- Security, compliance, controls

### Closing (Slides 10-12)
- Specific next week actions
- Emphasize team benefits
- "Your teams can start building next week"

### Q&A (Slide 13)
- Answer GitLab, Azure, security questions directly
- Focus on practical, not theory
- Emphasize team enablement

---

## Key Messages to Emphasize

1. **Team Impact:** "40-60% reduction in manual work. 70-80% time savings."
2. **Practical Automations:** "GitLab MR Review, Incident Triage, Infrastructure Diagnostics."
3. **Fiserv Constraints:** "Azure OpenAI, GitLab, internal proxies, German compliance."
4. **MCP Safety:** "MCP = gateway that ensures AI cannot misuse infrastructure."
5. **Next Week Actions:** "Identify 3 workflows. Assign one team member. Start building."

---

## Delivery Guidance

- Keep it concise and practical
- Focus on what IT Directors need to know
- Emphasize team impact and actionable next steps
- Use simple language, avoid corporate jargon

---

## Key Messages

- IT teams are overloaded — AI agents reduce workload
- These are engineering assistants, not magic
- MCP is the safety barrier — controlled and auditable
- Practical automations — can be implemented in 30 days
- Governance is required — IT Directors must implement controls

---

## Common Objections & Responses

**"We don't have time to build this."**  
→ "Start with one workflow. GitLab MR Review Agent. 70-80% time savings. Your team gets time back."

**"This is too risky for production."**  
→ "We start with low-risk, read-only pilots. Sandboxed execution. HITL gates. Rollback procedures. We prove it works before production."

**"How do we integrate with GitLab?"**  
→ "MCP provides secure API access. Agents can review MRs, analyze code, check security. All actions logged. We'll show you the integration pattern."

**"What about Azure OpenAI costs?"**  
→ "Per-request pricing. €5K-€10K/month for pilots. ROI covers costs within 60 days. Time savings more than pay for it."

**"Our teams aren't ready for this."**  
→ "We provide training. One team member becomes expert, trains others. Start with one workflow, then expand. Gradual rollout."

---

## Final Reminders

1. **Technical Leadership Tone:** Smart, technical, practical, not corporate
2. **Team Impact Focus:** "This removes 30-50% of manual work" not "strategic lever"
3. **Concise Language:** "LLM = Brain, RAG = IT Documentation Warehouse, Agent = The Engineer Assistant"
4. **Fiserv-Specific:** Azure OpenAI, GitLab, internal proxies, German compliance
5. **Actionable:** "What your teams should start doing next week"
6. **Visual Aids:** Mermaid diagrams for technical clarity

**Remember:** This is for IT Directors. They want practical implementation, team impact, technical architecture. Keep it technical, keep it practical, keep it actionable.

