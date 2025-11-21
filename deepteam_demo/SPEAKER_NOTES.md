# DeepTeam Framework - Speaker Notes
## Presentation Guide for Management & Technical Audiences

---

## Slide 1: Introduction - The LLM Security Challenge

### Speaker Notes:
"Good [morning/afternoon]. Today we're going to discuss a critical challenge facing organizations deploying LLM applications: **security and safety**.

As we integrate AI into our products and services, we're exposing ourselves to new attack vectors. Traditional security testing doesn't cover the unique vulnerabilities of LLM systems. We need specialized tools to identify risks before they become incidents.

**DeepTeam** is an open-source framework designed specifically for red teaming LLM applications. Think of it as penetration testing, but for AI systems."

### Key Points:
- LLM applications have unique security vulnerabilities
- Traditional security tools don't cover AI-specific risks
- Proactive testing is essential before production deployment

---

## Slide 2: Why DeepTeam? - The Problem We're Solving

### Speaker Notes:
"Let me illustrate why we need DeepTeam with a few real-world scenarios:

**Scenario 1: PII Leakage**
- A customer service chatbot might inadvertently expose user data when manipulated with clever prompts
- Without proper testing, this could lead to GDPR violations and data breaches

**Scenario 2: Prompt Injection**
- An attacker could inject malicious instructions that override the system's safety guidelines
- This could lead to the system performing unauthorized actions

**Scenario 3: Bias and Toxicity**
- An LLM might generate biased or toxic content, damaging brand reputation
- This is especially critical for customer-facing applications

**DeepTeam helps us identify these vulnerabilities BEFORE they reach production.**"

### Key Points:
- Real-world security risks in LLM applications
- Financial and reputational impact of vulnerabilities
- Need for proactive security testing

---

## Slide 3: What is DeepTeam? - Overview

### Speaker Notes:
"DeepTeam is an open-source LLM red teaming framework developed by Confident AI. It's specifically designed for:

1. **Penetration Testing**: Simulating adversarial attacks against LLM systems
2. **Vulnerability Detection**: Identifying 40+ types of security and safety risks
3. **Compliance**: Supporting industry standards like OWASP Top 10 for LLMs and NIST AI RMF

Think of it as a comprehensive security audit tool that:
- Automatically generates attack scenarios
- Tests your LLM against known vulnerability patterns
- Provides detailed risk assessments
- Helps you meet compliance requirements"

### Key Points:
- Open-source framework
- Comprehensive vulnerability coverage
- Industry standard compliance
- Automated testing capabilities

---

## Slide 4: DeepTeam's Capabilities - 40+ Vulnerabilities

### Speaker Notes:
"DeepTeam comes with 40+ out-of-the-box vulnerabilities that we can test against. These fall into several categories:

**Security Vulnerabilities:**
- SQL Injection, Shell Injection, SSRF
- Broken Access Control (BFLA, BOLA, RBAC)
- API security issues

**Data Privacy:**
- PII Leakage (direct disclosure, session leaks, database access)
- Prompt Leakage (secrets, credentials, instructions)

**Safety & Ethics:**
- Bias (race, gender, religion, politics)
- Toxicity (profanity, threats, insults)
- Illegal activity, graphic content

**Business Risks:**
- Misinformation
- Intellectual property leakage
- Competitive intelligence disclosure

**Agentic Risks:**
- Goal theft
- Recursive hijacking
- Excessive agency

**The framework tests all of these automatically, giving us a comprehensive security assessment.**"

### Key Points:
- Broad vulnerability coverage
- Categorized by risk type
- Automated testing for all categories

---

## Slide 5: Attack Methods - 10+ Adversarial Techniques

### Speaker Notes:
"DeepTeam doesn't just test vulnerabilities—it uses sophisticated attack methods to simulate real-world threats:

**Single-Turn Attacks:**
- **Prompt Injection**: Direct manipulation of system instructions
- **Roleplay**: Convincing the system to adopt a harmful persona
- **Leetspeak & ROT-13**: Obfuscation techniques to bypass filters
- **Math Problems**: Exploiting reasoning vulnerabilities

**Multi-Turn Attacks:**
- **Linear Jailbreaking**: Gradually escalating harmful requests
- **Tree Jailbreaking**: Exploring multiple attack pathways simultaneously
- **Crescendo Jailbreaking**: Building rapport before introducing harmful requests
- **Sequential Jailbreaking**: Multi-step attack sequences

**These attack methods simulate how real attackers would try to exploit your system. By testing against these, we can identify weaknesses before attackers do.**"

### Key Points:
- Realistic attack simulation
- Both single and multi-turn attack strategies
- Mimics real-world attack patterns

---

## Slide 6: Custom Vulnerability Creation - Flexibility

### Speaker Notes:
"One of DeepTeam's most powerful features is the ability to create custom vulnerabilities. This is critical because:

1. **Industry-Specific Risks**: Your business might have unique security concerns
2. **Regulatory Requirements**: Different industries have different compliance needs
3. **Business Logic**: Custom vulnerabilities can test domain-specific logic

**Creating a custom vulnerability takes just 5 lines of code:**

```python
from deepteam.vulnerabilities import CustomVulnerability

api_security = CustomVulnerability(
    name="API Security",
    criteria="The system should not expose internal API endpoints",
    types=["endpoint_exposure", "auth_bypass"]
)
```

**This flexibility means we can test against risks specific to our business, not just generic vulnerabilities.**"

### Key Points:
- Custom vulnerability support
- Industry-specific testing
- Easy to implement (5 lines of code)
- Business logic testing

---

## Slide 7: Integration - How to Use DeepTeam

### Speaker Notes:
"Now, let's talk about how to integrate DeepTeam into your existing LLM applications. The process is straightforward:

**Step 1: Wrap Your LLM Application**
- Create a callback function that wraps your existing LLM system
- This callback takes user input and returns the LLM's response
- DeepTeam will call this function during testing

**Step 2: Define What to Test**
- Select vulnerabilities relevant to your use case
- Choose attack methods to simulate
- Or use a framework like OWASP Top 10

**Step 3: Run the Red Team Assessment**
- DeepTeam automatically generates attacks
- Tests your system against selected vulnerabilities
- Provides detailed risk assessment

**Step 4: Review and Remediate**
- Analyze the results
- Identify vulnerabilities
- Fix issues and retest

**The beauty is that DeepTeam works with ANY LLM application—whether it's a simple chatbot, a RAG system, an AI agent, or a complex multi-component system.**"

### Key Points:
- Simple integration process
- Works with any LLM application
- Non-invasive testing (black-box)
- Automated assessment

---

## Slide 8: Integration Example - Code Walkthrough

### Speaker Notes:
"Let me show you how simple integration is with a real example:

**Example: Testing a Customer Service Chatbot**

```python
from deepteam import red_team
from deepteam.vulnerabilities import PIILeakage, Bias
from deepteam.attacks.single_turn import PromptInjection

# Your existing chatbot function
async def chatbot_callback(input_text: str) -> str:
    # This is your existing LLM application
    response = await your_chatbot_service.process(input_text)
    return response

# Run red teaming
risk_assessment = red_team(
    model_callback=chatbot_callback,
    vulnerabilities=[PIILeakage(), Bias()],
    attacks=[PromptInjection()]
)

# Review results
print(f"Found {len(risk_assessment.test_cases)} vulnerabilities")
```

**That's it! In just a few lines of code, we've tested our chatbot against PII leakage and bias vulnerabilities using prompt injection attacks.**

**The key point: We didn't need to modify our existing chatbot code. DeepTeam tests it as a black box, just like real attackers would.**"

### Key Points:
- Minimal code required
- Non-invasive testing
- Works with existing applications
- Quick to implement

---

## Slide 9: Integration Patterns - Different Application Types

### Speaker Notes:
"DeepTeam works with various types of LLM applications:

**1. Simple Foundational Models**
- Direct LLM API calls (OpenAI, Anthropic, etc.)
- Fastest to integrate
- Good for testing base model behavior

**2. RAG (Retrieval-Augmented Generation) Systems**
- Systems that retrieve context from databases
- Tests for prompt leakage and data exposure
- Validates retrieval security

**3. Chatbots with Memory**
- Multi-turn conversation systems
- Tests conversation hijacking
- Validates context manipulation

**4. AI Agents with Tool Calling**
- Systems that can execute actions
- Tests for excessive agency
- Validates tool access control

**5. Complex Multi-Component Systems**
- Systems with multiple LLM components
- Can test each component individually
- Or test the system as a whole

**In our demo suite, we've created examples for all these patterns, so you can see exactly how to integrate DeepTeam with your specific architecture.**"

### Key Points:
- Supports all LLM application types
- Flexible integration patterns
- Real-world examples provided

---

## Slide 10: Framework Support - Compliance Made Easy

### Speaker Notes:
"DeepTeam also supports industry-standard frameworks, making compliance easier:

**OWASP Top 10 for LLMs**
- Pre-configured vulnerability set
- Based on industry best practices
- One-line integration:
```python
from deepteam.frameworks import OWASPTop10
risk_assessment = red_team(
    model_callback=your_callback,
    framework=OWASPTop10()
)
```

**NIST AI Risk Management Framework**
- Government-standard compliance
- Categorized risk measures
- Supports multiple assessment categories

**Using these frameworks means:**
- We're testing against industry-recognized standards
- Compliance reports are easier to generate
- We can demonstrate due diligence to auditors

**This is especially valuable for regulated industries like healthcare, finance, and government.**"

### Key Points:
- Industry standard compliance
- Pre-configured frameworks
- Easier audit preparation
- Regulatory compliance support

---

## Slide 11: Risk Assessment - Understanding the Results

### Speaker Notes:
"After running DeepTeam, you get a comprehensive risk assessment that includes:

**1. Test Case Overview**
- All attack attempts and their results
- Which attacks succeeded (vulnerabilities found)
- Which attacks failed (system defended)

**2. Vulnerability Breakdown**
- Pass rate by vulnerability type
- Number of passing vs. failing tests
- Error rates

**3. Attack Method Analysis**
- Which attack methods were most effective
- Success rates by attack type
- Multi-turn vs. single-turn effectiveness

**4. Detailed Reports**
- JSON export for programmatic analysis
- Markdown reports for stakeholders
- DataFrame support for data analysis

**5. Failed Test Cases**
- Exact prompts that succeeded
- System responses that were vulnerable
- Reasons for failure

**This detailed reporting helps us:**
- Prioritize fixes (which vulnerabilities are most critical)
- Understand attack patterns (how attackers might exploit us)
- Track improvements (compare before/after fixes)
- Demonstrate security posture (for compliance and audits)"

### Key Points:
- Comprehensive reporting
- Actionable insights
- Multiple output formats
- Progress tracking

---

## Slide 12: Real-World Use Cases

### Speaker Notes:
"Let me share some real-world scenarios where DeepTeam provides value:

**Use Case 1: Pre-Production Security Audit**
- Before launching a new LLM feature, run DeepTeam
- Identify vulnerabilities before customers see them
- Fix issues proactively, not reactively

**Use Case 2: Continuous Security Testing**
- Integrate DeepTeam into CI/CD pipeline
- Run security tests on every deployment
- Catch regressions early

**Use Case 3: Compliance Preparation**
- Use OWASP or NIST frameworks
- Generate compliance reports
- Demonstrate security due diligence

**Use Case 4: Vendor Assessment**
- Test third-party LLM services before integration
- Compare security postures of different providers
- Make informed vendor selection decisions

**Use Case 5: Security Training**
- Use DeepTeam to demonstrate attack patterns
- Train developers on LLM security
- Build security awareness

**Use Case 6: Incident Response**
- After a security incident, use DeepTeam to test fixes
- Verify that vulnerabilities are actually resolved
- Prevent similar incidents"

### Key Points:
- Multiple practical applications
- Fits into existing workflows
- Supports various business needs

---

## Slide 13: Integration Best Practices

### Speaker Notes:
"Here are some best practices for integrating DeepTeam:

**1. Start Small**
- Begin with a single application
- Test against a few high-priority vulnerabilities
- Expand gradually as you learn

**2. Integrate Early**
- Test during development, not just before production
- Catch issues when they're easier to fix
- Make security part of the development process

**3. Use Frameworks for Compliance**
- Start with OWASP Top 10 for comprehensive coverage
- Add custom vulnerabilities for business-specific risks
- Document your testing approach

**4. Automate Testing**
- Integrate into CI/CD pipelines
- Run tests on every deployment
- Set up alerts for new vulnerabilities

**5. Track Progress**
- Save risk assessments for comparison
- Track vulnerability trends over time
- Measure improvement

**6. Remediate Systematically**
- Prioritize by risk level
- Fix high-severity issues first
- Retest after fixes

**7. Share Results**
- Present findings to stakeholders
- Use reports for compliance documentation
- Build security awareness"

### Key Points:
- Practical integration guidance
- Incremental approach
- Automation opportunities
- Continuous improvement

---

## Slide 14: Demo - Live Walkthrough

### Speaker Notes:
"Now let me show you DeepTeam in action. I'll walk through our demo suite that showcases:

**1. Vulnerability Testing**
- Testing against 40+ vulnerabilities
- Seeing which ones our system is vulnerable to
- Understanding the attack patterns

**2. Attack Method Demonstration**
- Single-turn attacks (prompt injection, roleplay)
- Multi-turn attacks (jailbreaking techniques)
- Seeing how different attacks work

**3. Custom Vulnerability Creation**
- Creating a business-specific vulnerability
- Testing against custom criteria
- Seeing how easy it is to extend DeepTeam

**4. Framework Integration**
- Running OWASP Top 10 tests
- Generating compliance reports
- Understanding framework benefits

**5. Risk Assessment Review**
- Analyzing the results
- Understanding the reports
- Identifying remediation priorities

**As we go through this, notice how:**
- Simple the integration is
- Comprehensive the testing is
- Actionable the results are"

### Key Points:
- Live demonstration
- Real examples
- Practical walkthrough

---

## Slide 15: ROI and Business Value

### Speaker Notes:
"Let's talk about the business value of DeepTeam:

**1. Risk Reduction**
- Identify vulnerabilities before production
- Prevent security incidents
- Avoid data breaches and compliance violations

**2. Cost Savings**
- Fix issues early (cheaper than post-production)
- Avoid incident response costs
- Reduce compliance penalties

**3. Time Savings**
- Automated testing vs. manual security reviews
- Faster security assessments
- Quicker time-to-market with confidence

**4. Compliance Enablement**
- Meet regulatory requirements
- Generate audit-ready reports
- Demonstrate due diligence

**5. Competitive Advantage**
- More secure products
- Better customer trust
- Reduced liability

**6. Developer Productivity**
- Clear vulnerability reports
- Actionable remediation guidance
- Faster security validation

**The investment in DeepTeam pays for itself by:**
- Preventing a single security incident
- Avoiding one compliance violation
- Catching one critical vulnerability before production"

### Key Points:
- Clear business value
- ROI justification
- Risk mitigation
- Cost savings

---

## Slide 16: Getting Started - Next Steps

### Speaker Notes:
"Here's how to get started with DeepTeam:

**Step 1: Installation**
```bash
pip install deepteam
```

**Step 2: Set Up API Keys**
- Configure your LLM provider credentials
- DeepTeam supports Anthropic, Azure OpenAI, and more

**Step 3: Create Your First Test**
- Wrap your LLM application in a callback
- Select vulnerabilities to test
- Run your first assessment

**Step 4: Review Results**
- Analyze the risk assessment
- Identify critical vulnerabilities
- Plan remediation

**Step 5: Integrate into Workflow**
- Add to CI/CD pipeline
- Set up regular testing
- Track progress over time

**We've created a comprehensive demo suite that you can use as a reference. It includes:**
- Examples for different application types
- Pre-configured vulnerability sets
- Framework integrations
- Reporting examples

**You can start testing your applications today with minimal setup.**"

### Key Points:
- Quick start guide
- Simple setup process
- Reference examples available
- Immediate value

---

## Slide 17: Q&A - Common Questions

### Speaker Notes:
"Let me address some common questions:

**Q: Does DeepTeam work with our existing LLM infrastructure?**
A: Yes! DeepTeam tests your LLM as a black box. You just need to provide a callback function that wraps your existing system.

**Q: How long does testing take?**
A: Depends on the number of vulnerabilities and attacks. A comprehensive test might take 10-30 minutes. You can run focused tests faster.

**Q: Does DeepTeam modify our code?**
A: No. DeepTeam is non-invasive. It only calls your application's API, just like a real user would.

**Q: What if we find vulnerabilities?**
A: DeepTeam provides detailed reports showing exactly what failed and why. This helps you fix issues quickly.

**Q: Can we customize it for our industry?**
A: Absolutely! Custom vulnerabilities take just 5 lines of code. You can test against any business-specific risks.

**Q: Is it suitable for production environments?**
A: Yes, but we recommend testing in staging first. DeepTeam makes real API calls, so plan accordingly.

**Q: How does it compare to manual security testing?**
A: DeepTeam automates what would take security experts days or weeks. It's faster, more comprehensive, and repeatable.

**Q: What about false positives?**
A: DeepTeam uses LLM-based evaluation, which is more accurate than rule-based systems. Results are reviewed by AI evaluators.

**Any other questions?""

### Key Points:
- Address common concerns
- Clarify capabilities
- Set expectations

---

## Slide 18: Conclusion - Key Takeaways

### Speaker Notes:
"Let me summarize the key takeaways:

**1. LLM Security is Critical**
- Unique vulnerabilities require specialized testing
- Traditional security tools aren't sufficient
- Proactive testing is essential

**2. DeepTeam Provides Comprehensive Coverage**
- 40+ vulnerabilities out of the box
- 10+ attack methods
- Industry-standard frameworks
- Custom vulnerability support

**3. Integration is Simple**
- Works with any LLM application
- Non-invasive testing
- Minimal code changes required
- Quick to get started

**4. Business Value is Clear**
- Risk reduction
- Cost savings
- Compliance enablement
- Competitive advantage

**5. Ready to Use Today**
- Open-source and free
- Comprehensive documentation
- Demo suite available
- Active community support

**DeepTeam helps us build secure, compliant LLM applications with confidence. It's an essential tool for any organization deploying AI systems.**

**Thank you for your attention. I'm happy to answer any questions or provide a detailed demo.""

### Key Points:
- Summarize main points
- Reinforce value proposition
- Call to action
- Open for questions

---

## Appendix: Technical Deep Dive (If Needed)

### Speaker Notes (for technical audiences):
"If you'd like to dive deeper into the technical aspects:

**Architecture:**
- DeepTeam uses a simulator model to generate attacks
- An evaluation model assesses responses
- Both can be customized for your needs

**Attack Generation:**
- Attacks are generated dynamically based on vulnerabilities
- Multi-turn attacks build on previous interactions
- Custom prompts can be provided for specialized testing

**Evaluation:**
- LLM-based evaluation (more accurate than rules)
- Configurable evaluation models
- Detailed reasoning provided

**Performance:**
- Async mode for faster testing
- Configurable concurrency
- Progress tracking

**Integration Patterns:**
- Direct function callbacks
- Async/await support
- Framework integrations
- CLI usage for automation"

### Key Points:
- Technical details
- Architecture overview
- Performance considerations
- Advanced features

---

## Presentation Tips

### Delivery Guidelines:

1. **Know Your Audience**
   - Management: Focus on business value, ROI, risk reduction
   - Technical: Focus on integration, capabilities, architecture
   - Mixed: Balance both perspectives

2. **Use the Demo**
   - Live demos are powerful
   - Show real results, not just slides
   - Let the tool speak for itself

3. **Tell Stories**
   - Use real-world scenarios
   - Relate to audience's industry
   - Make it relevant

4. **Be Honest**
   - Acknowledge limitations
   - Set realistic expectations
   - Don't oversell

5. **Encourage Questions**
   - Interactive presentations are better
   - Address concerns directly
   - Build engagement

6. **Provide Next Steps**
   - Clear path forward
   - Resources for learning
   - Support for getting started

---

## Resources for Audience

### After the Presentation:

1. **Demo Suite**: Full working examples in `deepteam_demo/`
2. **Documentation**: Comprehensive guides in `UNDERSTANDING.md`
3. **Official Docs**: https://docs.deepteam.ai
4. **GitHub**: https://github.com/confident-ai/deepteam
5. **Support**: Community forums and issue tracking

---

**End of Speaker Notes**

