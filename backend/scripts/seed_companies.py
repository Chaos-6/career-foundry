"""
Seed the company_profiles table with 43 tech companies.

Each company includes:
- Guiding principles (Leadership Principles, Core Values, etc.)
- Interview focus notes for the evaluator
- Additional interview tips

Run: python -m scripts.seed_companies (from backend/)
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal, init_db
from app.models import CompanyProfile

# fmt: off

COMPANIES = [
    # -----------------------------------------------------------------------
    # FAANG + Major Tech
    # -----------------------------------------------------------------------
    {
        "name": "Amazon",
        "slug": "amazon",
        "principle_type": "Leadership Principles",
        "principles": [
            {"name": "Customer Obsession", "description": "Leaders start with the customer and work backwards. They work vigorously to earn and keep customer trust."},
            {"name": "Ownership", "description": "Leaders are owners. They think long term and don't sacrifice long-term value for short-term results."},
            {"name": "Invent and Simplify", "description": "Leaders expect and require innovation and invention from their teams, and always find ways to simplify."},
            {"name": "Are Right, A Lot", "description": "Leaders are right a lot. They have strong judgment and good instincts. They seek diverse perspectives and work to disconfirm their beliefs."},
            {"name": "Learn and Be Curious", "description": "Leaders are never done learning and always seek to improve themselves."},
            {"name": "Hire and Develop the Best", "description": "Leaders raise the performance bar with every hire and promotion."},
            {"name": "Insist on the Highest Standards", "description": "Leaders have relentlessly high standards. They continually raise the bar and drive their teams to deliver high-quality products, services, and processes."},
            {"name": "Think Big", "description": "Thinking small is a self-fulfilling prophecy. Leaders create and communicate a bold direction that inspires results."},
            {"name": "Bias for Action", "description": "Speed matters in business. Many decisions and actions are reversible and do not need extensive study."},
            {"name": "Frugality", "description": "Accomplish more with less. Constraints breed resourcefulness, self-sufficiency, and invention."},
            {"name": "Earn Trust", "description": "Leaders listen attentively, speak candidly, and treat others respectfully."},
            {"name": "Dive Deep", "description": "Leaders operate at all levels, stay connected to the details, audit frequently, and are skeptical when metrics and anecdotes differ."},
            {"name": "Have Backbone; Disagree and Commit", "description": "Leaders are obligated to respectfully challenge decisions when they disagree, even when doing so is uncomfortable or exhausting."},
            {"name": "Deliver Results", "description": "Leaders focus on the key inputs for their business and deliver them with the right quality and in a timely fashion."},
            {"name": "Strive to be Earth's Best Employer", "description": "Leaders work every day to create a safer, more productive, higher performing, more diverse, and more just work environment."},
            {"name": "Success and Scale Bring Broad Responsibility", "description": "We started in a garage, but we're not there anymore. We are big, we impact the world, and we are far from perfect."},
        ],
        "interview_focus": "Demonstrate 2-3 LPs per answer with specific examples. STAR structure is critical. Use 'I' not 'we'. Quantify results.",
        "interview_tips": [
            "Amazon interviewers are trained to map answers to specific LPs",
            "Each interviewer typically probes for 2-3 assigned LPs",
            "Data and metrics are essential — quantify everything",
            "Show ownership: use 'I did' not 'we did'",
            "The bar raiser looks for signals across ALL LPs",
        ],
    },
    {
        "name": "Meta",
        "slug": "meta",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Move Fast", "description": "Moving fast enables us to build more things and learn faster. We're less afraid of making mistakes than we are of losing opportunities by moving too slowly."},
            {"name": "Be Bold", "description": "Building great things means taking risks. We have a saying: 'The riskiest thing is to take no risks.'"},
            {"name": "Focus on Impact", "description": "To have the biggest impact, we need to focus on solving the most important problems. Be good at finding these problems."},
            {"name": "Be Open", "description": "We believe that a more open world is a better world. We work hard to make sure people have access to as much information as possible."},
            {"name": "Build Social Value", "description": "Our mission is to give people the power to build community. Every engineering decision should advance that mission."},
        ],
        "interview_focus": "Emphasize impact, speed of execution, and data-driven decision making. Show boldness and willingness to take calculated risks.",
        "interview_tips": [
            "Meta values speed and iteration over perfection",
            "Quantify the impact of your work in terms of users or revenue",
            "Show how you identified and solved high-impact problems",
            "Demonstrate comfort with ambiguity and rapid change",
        ],
    },
    {
        "name": "Google",
        "slug": "google",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Focus on the User", "description": "Focus on the user and all else will follow. Everything we do starts with the user experience."},
            {"name": "Think 10x, Not 10%", "description": "If you're trying to make something 10 times better, you're going to approach the problem differently than if you're trying to make it 10% better."},
            {"name": "Deliver and Iterate", "description": "Don't wait for perfect. Ship, learn, and iterate."},
            {"name": "Collaborate", "description": "Great things are built by teams that work well together across boundaries."},
            {"name": "Be Googley (Do the Right Thing)", "description": "Don't be evil. Act with integrity, transparency, and respect for users."},
        ],
        "interview_focus": "Show innovation, technical excellence, Googleyness, and collaborative problem-solving. Demonstrate 10x thinking.",
        "interview_tips": [
            "Googleyness is a real evaluation criterion — show intellectual humility, collaboration, and doing the right thing",
            "Demonstrate systems thinking and ability to see the big picture",
            "Show how you collaborated across teams or organizations",
            "Technical depth matters — don't shy away from details",
        ],
    },
    {
        "name": "Microsoft",
        "slug": "microsoft",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Growth Mindset", "description": "We believe in the power of learning. We encourage curiosity, experimentation, and continuous improvement in ourselves and others."},
            {"name": "Innovation", "description": "We push the boundaries of what's possible through technology, creating solutions that empower every person and organization."},
            {"name": "Diversity and Inclusion", "description": "We are committed to creating a workplace where every individual can thrive, contribute, and feel valued."},
            {"name": "Trustworthy Computing", "description": "We build products and services that people can trust — secure, private, reliable, and responsible."},
            {"name": "Customer Focus", "description": "We exist to serve our customers. Understanding their needs drives everything we build."},
        ],
        "interview_focus": "Demonstrate growth mindset, collaboration, customer-centricity, and learning from failure. Show how you've grown.",
        "interview_tips": [
            "Growth mindset is central — show how you learned from failures",
            "Satya Nadella's 'learn-it-all vs. know-it-all' philosophy is key",
            "Demonstrate how you empowered others or lifted up a team",
            "Show cross-team collaboration and influence without authority",
        ],
    },
    {
        "name": "Apple",
        "slug": "apple",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Excellence", "description": "We don't settle for anything less than excellence in every product we create, every service we provide, and every interaction we have."},
            {"name": "Innovation", "description": "We believe in the power of human creativity and innovation. We push the boundaries of what's possible."},
            {"name": "Privacy", "description": "Privacy is a fundamental human right. We design our products to protect our customers' personal data."},
            {"name": "Environmental Responsibility", "description": "We are committed to leaving the world better than we found it."},
            {"name": "Attention to Detail", "description": "The details matter. Every pixel, every interaction, every experience is intentionally crafted."},
        ],
        "interview_focus": "Show attention to detail, design thinking, product excellence, and craftsmanship. Quality over quantity.",
        "interview_tips": [
            "Apple values secrecy and discretion — demonstrate trustworthiness",
            "Show obsession with user experience and polish",
            "Demonstrate ability to say no to good ideas to focus on great ones",
            "Cross-functional collaboration is highly valued",
        ],
    },

    # -----------------------------------------------------------------------
    # High-Growth Tech
    # -----------------------------------------------------------------------
    {
        "name": "Netflix",
        "slug": "netflix",
        "principle_type": "Core Principles",
        "principles": [
            {"name": "The Dream Team", "description": "A dream team is one in which all of your colleagues are extraordinary at what they do and are highly effective collaborators."},
            {"name": "People Over Process", "description": "Our goal is to inspire people more than manage them. We trust people to use good judgment."},
            {"name": "Uncomfortably Exciting", "description": "We want to entertain the world. If we succeed, there is no prize for making it easy. We take smart risks."},
            {"name": "Great and Always Better", "description": "We focus on being great at what we do and continuously improving. The Keeper Test: would you fight to keep this person?"},
        ],
        "interview_focus": "Show freedom with responsibility, high performance, boldness, and continuous improvement. Keeper Test mindset.",
        "interview_tips": [
            "Netflix values radical candor — show you give and receive direct feedback",
            "Demonstrate high autonomy and sound judgment without supervision",
            "The 'Keeper Test': show why you'd be someone a manager would fight to keep",
            "Context over control — show how you made good decisions independently",
        ],
    },
    {
        "name": "Uber",
        "slug": "uber",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Do the Right Thing", "description": "Act with integrity, be ethical, and make decisions you'd be proud to explain."},
            {"name": "Build with Heart", "description": "We build products that move the world. We care deeply about our riders, drivers, and the communities we serve."},
            {"name": "Customer Obsessed", "description": "We put our customers at the center of everything we do."},
            {"name": "Win Together", "description": "We collaborate across teams, celebrate wins, and support each other."},
            {"name": "Embrace the Challenge", "description": "We are resilient. We tackle the toughest problems and thrive under pressure."},
        ],
        "interview_focus": "Emphasize integrity, customer impact, and teamwork under pressure. Show resilience and grit.",
        "interview_tips": [
            "Uber values resilience — show how you thrived in challenging situations",
            "Customer obsession should be evident in every story",
            "Demonstrate collaboration across diverse teams",
            "Show integrity in difficult ethical situations",
        ],
    },
    {
        "name": "Airbnb",
        "slug": "airbnb",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Champion the Mission", "description": "We are united behind our mission to create a world where anyone can belong anywhere."},
            {"name": "Be a Host", "description": "Caring for others is our superpower. We show up for our community, guests, and each other."},
            {"name": "Embrace the Adventure", "description": "We are driven by curiosity, openness, and the belief that every person has something to teach us."},
            {"name": "Be a Cereal Entrepreneur", "description": "We are resourceful, creative, and scrappy. During tough times, our founders sold cereal boxes to fund the company."},
        ],
        "interview_focus": "Show mission alignment, hospitality mindset, resourcefulness, and entrepreneurial creativity.",
        "interview_tips": [
            "Airbnb deeply values belonging and inclusion — weave this into stories",
            "The 'cereal entrepreneur' value prizes resourcefulness over resources",
            "Show genuine care for users/customers in your stories",
            "Mission-driven work is highly valued — show how your work connected to a larger purpose",
        ],
    },
    {
        "name": "Stripe",
        "slug": "stripe",
        "principle_type": "Operating Principles",
        "principles": [
            {"name": "Users First", "description": "We exist to help our users succeed. We build what they need, not just what's technically interesting."},
            {"name": "Move with Urgency and Focus", "description": "Speed matters. We prioritize ruthlessly and ship quickly."},
            {"name": "Create with Craft and Beauty", "description": "We care deeply about quality in everything — code, writing, design, even internal docs."},
            {"name": "Collaborate Egolessly", "description": "The best idea wins, regardless of who proposed it. We debate vigorously and commit fully."},
            {"name": "Obsess Over Talent", "description": "We set an extraordinarily high bar for talent and invest deeply in developing our people."},
        ],
        "interview_focus": "Demonstrate user-centricity, speed, craftsmanship, egoless collaboration, and high talent bar.",
        "interview_tips": [
            "Stripe values exceptional writing — clear communication is paramount",
            "Show craft: attention to quality, well-considered solutions",
            "Egoless collaboration: credit others, show you put team success first",
            "Demonstrate urgency without sacrificing quality",
        ],
    },
    {
        "name": "Salesforce",
        "slug": "salesforce",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Trust", "description": "Trust is our #1 value. Nothing is more important than the trust of our customers, employees, and partners."},
            {"name": "Customer Success", "description": "When our customers succeed, we succeed. We are relentlessly focused on customer outcomes."},
            {"name": "Innovation", "description": "We innovate together with our customers. Every employee is an innovator."},
            {"name": "Equality", "description": "We believe in equal rights and opportunities for all. We are committed to creating a diverse and inclusive workplace."},
            {"name": "Sustainability", "description": "We are committed to building a sustainable future for all stakeholders and the planet."},
        ],
        "interview_focus": "Show trust-building, customer empathy, innovation, and inclusive leadership. Ohana (family) culture.",
        "interview_tips": [
            "Salesforce's Ohana culture means treating everyone like family",
            "Trust is the foundation — show integrity and transparency in your stories",
            "Customer success should be front and center",
            "Show commitment to equality and diverse perspectives",
        ],
    },

    # -----------------------------------------------------------------------
    # AI / Chip / Enterprise
    # -----------------------------------------------------------------------
    {
        "name": "NVIDIA",
        "slug": "nvidia",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Innovation", "description": "We push the boundaries of computing and AI. We invent the technologies that shape the future."},
            {"name": "Intellectual Honesty", "description": "We speak up, admit mistakes quickly, and seek the truth even when it's uncomfortable."},
            {"name": "Speed and Agility", "description": "We move fast, iterate quickly, and adapt to changing circumstances with agility."},
            {"name": "One Team", "description": "We work as one company, without silos or politics. Collaboration across teams is how we win."},
        ],
        "interview_focus": "Show technical depth, intellectual honesty (admit mistakes fast), speed, and no-politics collaboration.",
        "interview_tips": [
            "NVIDIA deeply values technical excellence — show your depth",
            "Intellectual honesty: admit what you don't know, show how you learned",
            "Demonstrate working across team boundaries without politics",
            "AI/GPU knowledge is appreciated but not required for all roles",
        ],
    },
    {
        "name": "LinkedIn",
        "slug": "linkedin",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Members First", "description": "Our members are at the center of everything we do."},
            {"name": "Trust and Care", "description": "We build relationships based on trust. We care for our members, employees, and communities."},
            {"name": "Open and Honest Communication", "description": "We communicate with transparency and candor. We share information openly."},
            {"name": "Diversity and Belonging", "description": "We strive to create a sense of belonging where everyone can bring their authentic self to work."},
            {"name": "Collaboration and Ownership", "description": "We work together and take ownership. Great results come from diverse teams working toward common goals."},
            {"name": "Innovation and Fun", "description": "We innovate boldly and have fun along the way. We believe joy fuels creativity."},
        ],
        "interview_focus": "Show member empathy, transparent communication, and collaborative ownership.",
        "interview_tips": [
            "LinkedIn values trust and care — show empathy in your stories",
            "Open communication is key — show how you handled transparency",
            "Demonstrate belonging and inclusion in your leadership",
            "Fun and innovation are valued — show passion for your work",
        ],
    },
    {
        "name": "Oracle",
        "slug": "oracle",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Integrity", "description": "We act with the highest standards of integrity and ethics in everything we do."},
            {"name": "Teamwork", "description": "We succeed together. Collaboration and mutual respect drive our achievements."},
            {"name": "Innovation", "description": "We are always pushing to develop cutting-edge technologies that transform industries."},
            {"name": "Customer Satisfaction", "description": "We are committed to helping our customers succeed with our products and services."},
            {"name": "Quality", "description": "We strive for excellence in every product, service, and interaction."},
            {"name": "Communication", "description": "Clear, transparent communication is essential to our success."},
        ],
        "interview_focus": "Show technical excellence, collaborative problem-solving, and customer focus.",
        "interview_tips": [
            "Oracle values enterprise-scale thinking — show large-scale impact",
            "Demonstrate database/cloud/infrastructure knowledge where relevant",
            "Technical depth combined with business impact is highly valued",
            "Show experience with complex, mission-critical systems",
        ],
    },

    # -----------------------------------------------------------------------
    # AI-First Companies
    # -----------------------------------------------------------------------
    {
        "name": "OpenAI",
        "slug": "openai",
        "principle_type": "Core Values",
        "principles": [
            {"name": "AGI Focus", "description": "We are focused on building artificial general intelligence that benefits all of humanity."},
            {"name": "Intense and Scrappy", "description": "We work with intensity and urgency. We are resourceful and move fast to solve hard problems."},
            {"name": "Scale", "description": "We think about scale from the start. Our systems serve hundreds of millions of users."},
            {"name": "Make Something People Love", "description": "We build products that delight users and have real impact on people's lives."},
            {"name": "Team Spirit", "description": "We support each other, share credit, and collaborate to achieve our mission."},
        ],
        "interview_focus": "Show mission-driven intensity, scrappy problem-solving, and building for users at scale.",
        "interview_tips": [
            "OpenAI values intensity and urgency — show you can move fast on hard problems",
            "Mission alignment is critical — show why AGI safety matters to you",
            "Demonstrate experience shipping products at scale",
            "Show scrappiness: solving hard problems with creative approaches",
        ],
    },
    {
        "name": "Anthropic",
        "slug": "anthropic",
        "principle_type": "Core Values",
        "principles": [
            {"name": "AI Safety and Ethics", "description": "We are committed to building AI systems that are safe, beneficial, and understandable."},
            {"name": "Trust and Transparency", "description": "We operate with transparency in our research and business practices."},
            {"name": "Collaboration and Learning", "description": "We foster an environment of intellectual curiosity, collaboration, and continuous learning."},
            {"name": "Drive Clarity", "description": "We seek clarity in our thinking, communication, and decision-making."},
        ],
        "interview_focus": "Show safety-conscious thinking, intellectual humility, transparent decision-making, and curiosity.",
        "interview_tips": [
            "Anthropic values intellectual humility — show you can change your mind with evidence",
            "Safety consciousness is paramount — show you think about risks and unintended consequences",
            "Demonstrate clear, rigorous thinking in your stories",
            "Show genuine curiosity and continuous learning",
        ],
    },
    {
        "name": "Databricks",
        "slug": "databricks",
        "principle_type": "Cultural Principles",
        "principles": [
            {"name": "Customer Obsession", "description": "We are obsessed with our customers' success. Everything starts with understanding their needs."},
            {"name": "Raise the Bar", "description": "We continuously raise the bar on quality, talent, and performance."},
            {"name": "Truth-Seeking", "description": "We pursue the truth through data, debate, and intellectual honesty."},
            {"name": "First Principles", "description": "We think from first principles, questioning assumptions and finding the best path forward."},
            {"name": "Bias for Action", "description": "We prefer action over analysis paralysis. Ship, learn, iterate."},
            {"name": "Company First", "description": "We put the company's success above individual or team interests."},
        ],
        "interview_focus": "Show data-driven decision-making, first principles thinking, and customer focus.",
        "interview_tips": [
            "Databricks values truth-seeking — show how you used data to find answers",
            "First principles thinking: show you questioned assumptions",
            "Demonstrate customer obsession with concrete examples",
            "Show bias for action: shipping fast and learning from results",
        ],
    },
    {
        "name": "Snowflake",
        "slug": "snowflake",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Put Customers First", "description": "Our customers are the reason we exist. Their success drives our success."},
            {"name": "Get It Done", "description": "We are results-oriented. We set ambitious goals and deliver."},
            {"name": "Make Each Other the Best", "description": "We push each other to grow, learn, and perform at our highest levels."},
            {"name": "Integrity", "description": "We do the right thing, even when it's hard."},
            {"name": "Innovation", "description": "We constantly innovate to solve our customers' most challenging data problems."},
            {"name": "Ownership", "description": "We take ownership of our work and our impact on the company."},
        ],
        "interview_focus": "Show customer-centricity, execution focus, and team development.",
        "interview_tips": [
            "Snowflake values execution — show you get things done",
            "Demonstrate how you've helped teammates grow",
            "Customer focus should be central to every story",
            "Show ownership and accountability for results",
        ],
    },

    # -----------------------------------------------------------------------
    # Disruptors
    # -----------------------------------------------------------------------
    {
        "name": "Tesla",
        "slug": "tesla",
        "principle_type": "Core Principles",
        "principles": [
            {"name": "Move Fast", "description": "Speed is a competitive advantage. We iterate quickly and don't wait for perfect."},
            {"name": "Do the Impossible", "description": "We tackle problems others consider impossible. We push the boundaries of what's achievable."},
            {"name": "Constantly Innovate", "description": "We never stop innovating. Every product, process, and system can be improved."},
            {"name": "Think Like Owners", "description": "Every employee acts like an owner. We take personal responsibility for the company's success."},
        ],
        "interview_focus": "Show speed, ambitious problem-solving, ownership mentality, and mission-driven work.",
        "interview_tips": [
            "Tesla values first-principles thinking — show how you rethought assumptions",
            "Speed and urgency are paramount — show you move fast",
            "Mission alignment: sustainable energy, transportation revolution",
            "Show you can handle intense, demanding environments",
        ],
    },
    {
        "name": "Palantir",
        "slug": "palantir",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Mission-Driven Engineering", "description": "We build technology that solves the world's hardest problems for the most important institutions."},
            {"name": "Privacy and Civil Liberties", "description": "We build technology that protects privacy and upholds civil liberties."},
            {"name": "Technical Excellence", "description": "We hold ourselves to the highest standards of engineering quality."},
            {"name": "Customer Focus", "description": "We deploy alongside our customers, understanding their problems deeply."},
        ],
        "interview_focus": "Show mission-driven intensity, ethical thinking, and deep technical problem-solving.",
        "interview_tips": [
            "Palantir values mission alignment — show you care about real-world impact",
            "Technical depth is critical — be prepared to go deep",
            "Show how you've worked with end users to understand their problems",
            "Demonstrate comfort with complex, ambiguous problem spaces",
        ],
    },

    # -----------------------------------------------------------------------
    # Fintech / Crypto
    # -----------------------------------------------------------------------
    {
        "name": "Coinbase",
        "slug": "coinbase",
        "principle_type": "Cultural Tenets",
        "principles": [
            {"name": "Clear Communication", "description": "We communicate clearly, concisely, and directly."},
            {"name": "Efficient Execution", "description": "We execute efficiently, minimizing meetings and maximizing output."},
            {"name": "Act Like an Owner", "description": "We treat the company as if it were our own. We are accountable for outcomes."},
            {"name": "Top Talent", "description": "We hire the best and hold everyone to high standards."},
            {"name": "Championship Team", "description": "We operate like a championship team — high performance, high trust, direct feedback."},
            {"name": "Continuous Learning", "description": "We are always learning and improving. Curiosity drives us forward."},
            {"name": "Customer Focus", "description": "We obsess over our customers and their experience with crypto."},
            {"name": "Repeatable Innovation", "description": "We innovate systematically, not just once, but repeatedly."},
            {"name": "Positive Energy", "description": "We bring positive energy and optimism to our work and our team."},
        ],
        "interview_focus": "Show ownership, clear communication, and mission-first execution.",
        "interview_tips": [
            "Coinbase values efficient execution — show you minimize waste and maximize output",
            "Clear, direct communication is essential",
            "Mission alignment with crypto/financial freedom is valued",
            "Show championship team mentality: high performance with direct feedback",
        ],
    },
    {
        "name": "Block (Square)",
        "slug": "block",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Economic Empowerment", "description": "We build tools that make financial systems more fair, accessible, and inclusive."},
            {"name": "Transparency", "description": "We operate with transparency, sharing information openly with our teams and users."},
            {"name": "Empathy", "description": "We design with empathy, understanding the needs of underserved communities and small businesses."},
            {"name": "Collaboration", "description": "We build together, valuing diverse perspectives and cross-functional teamwork."},
        ],
        "interview_focus": "Show empathy for underserved users, inclusive design thinking, and collaborative building.",
        "interview_tips": [
            "Block values economic empowerment — show how your work helped real people",
            "Empathy for underserved users is key — demonstrate inclusive thinking",
            "Show transparency and openness in your communication",
            "Demonstrate collaborative problem-solving across teams",
        ],
    },

    # -----------------------------------------------------------------------
    # AI / ML Companies
    # -----------------------------------------------------------------------
    {
        "name": "Hugging Face",
        "slug": "hugging-face",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Open Source First", "description": "We believe AI should be open and accessible. We build in the open and contribute to the community."},
            {"name": "Community-Driven", "description": "Our community shapes our roadmap. We listen to researchers, developers, and users and build what they need."},
            {"name": "Democratize AI", "description": "We make state-of-the-art AI accessible to everyone, not just large corporations with massive compute budgets."},
            {"name": "Ethics and Responsibility", "description": "We take AI safety and ethics seriously, building tools for responsible AI development."},
            {"name": "Collaboration", "description": "We believe the best AI is built together. We foster collaboration across the global ML community."},
        ],
        "interview_focus": "Show passion for open-source AI, community building, and making ML accessible. Demonstrate strong technical depth in NLP/ML.",
        "interview_tips": [
            "Hugging Face values open-source contributions — mention your OSS work",
            "Show how you've made complex AI concepts accessible to others",
            "Demonstrate community engagement and collaborative development",
            "Technical depth in transformers, NLP, or ML infrastructure is valued",
            "Show you care about responsible AI and ethics",
        ],
    },
    {
        "name": "Cohere",
        "slug": "cohere",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Ship with Purpose", "description": "We build AI that solves real enterprise problems. Every feature should drive customer value."},
            {"name": "Rigor and Excellence", "description": "We hold ourselves to the highest standards in research and engineering. Quality is non-negotiable."},
            {"name": "Customer Partnership", "description": "We work alongside our customers, understanding their needs deeply and building solutions together."},
            {"name": "Transparency", "description": "We communicate openly about what our models can and cannot do. We set honest expectations."},
            {"name": "Move Decisively", "description": "The AI landscape moves fast. We make decisions quickly, learn from outcomes, and iterate."},
        ],
        "interview_focus": "Demonstrate enterprise AI experience, rigorous ML engineering, and customer-centric product thinking. Show you can balance research ambition with shipping.",
        "interview_tips": [
            "Cohere focuses on enterprise NLP — show production ML experience",
            "Demonstrate understanding of LLM deployment challenges at scale",
            "Customer partnership is key — show how you've worked with enterprise clients",
            "Balance research depth with practical engineering pragmatism",
        ],
    },
    {
        "name": "Scale AI",
        "slug": "scale-ai",
        "principle_type": "Operating Principles",
        "principles": [
            {"name": "Data Quality Obsession", "description": "Great AI starts with great data. We obsess over data quality, labeling accuracy, and annotation consistency."},
            {"name": "Mission-Driven", "description": "We accelerate the development of AI applications. Every decision should advance AI adoption."},
            {"name": "Move Fast and Ship", "description": "Speed is a competitive advantage. We ship rapidly, measure outcomes, and iterate."},
            {"name": "Customer First", "description": "Our customers build the future of AI. We succeed when they succeed."},
            {"name": "High Standards", "description": "We hire exceptional people and hold everyone to exceptional standards. Mediocrity is not tolerated."},
        ],
        "interview_focus": "Show intensity, high standards, and passion for AI infrastructure. Demonstrate experience with data quality at scale and fast execution.",
        "interview_tips": [
            "Scale AI values intensity and high performance — show you operate at a high bar",
            "Demonstrate understanding of data pipelines, labeling, and quality at scale",
            "Show how you've shipped quickly while maintaining quality",
            "Mission-driven culture — connect your work to advancing AI",
            "Be prepared for rigorous technical evaluations",
        ],
    },
    {
        "name": "Midjourney",
        "slug": "midjourney",
        "principle_type": "Creative Principles",
        "principles": [
            {"name": "Imagination First", "description": "We build tools that expand human imagination. Technology serves creativity, not the other way around."},
            {"name": "Craft and Quality", "description": "We care deeply about the quality and beauty of what we create. Details matter."},
            {"name": "Small Team, Big Impact", "description": "We stay lean and focused. Every person has outsized impact and ownership."},
            {"name": "User Delight", "description": "We aim to surprise and delight users. The experience should feel magical, not mechanical."},
        ],
        "interview_focus": "Show creative thinking alongside technical depth. Demonstrate passion for generative AI and user experience. Emphasize doing more with less.",
        "interview_tips": [
            "Midjourney is a very small team — show you can wear many hats",
            "Demonstrate passion for the intersection of AI and creativity",
            "Quality and craft matter — show attention to detail in your work",
            "User experience focus is paramount — think about delight, not just functionality",
        ],
    },
    {
        "name": "Stability AI",
        "slug": "stability-ai",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Open AI for Everyone", "description": "We believe AI models should be open and accessible, enabling innovation across the world."},
            {"name": "Community Empowerment", "description": "We empower communities of developers, artists, and researchers to build on our models."},
            {"name": "Responsible Development", "description": "We develop AI responsibly, considering societal impact and working to mitigate harms."},
            {"name": "Innovation at the Frontier", "description": "We push the boundaries of generative AI, exploring new architectures and applications."},
            {"name": "Transparency", "description": "We publish our research, share our models, and communicate openly about our work."},
        ],
        "interview_focus": "Show commitment to open-source AI, generative model expertise, and responsible development. Demonstrate frontier research or engineering capabilities.",
        "interview_tips": [
            "Stability AI values open-source commitment — show your OSS contributions",
            "Demonstrate deep knowledge of diffusion models or generative AI",
            "Show awareness of responsible AI practices and societal impact",
            "Community building and collaboration are valued",
        ],
    },

    # -----------------------------------------------------------------------
    # Fintech
    # -----------------------------------------------------------------------
    {
        "name": "PayPal",
        "slug": "paypal",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Inclusion", "description": "We build products that serve everyone. Financial services should be accessible regardless of background."},
            {"name": "Innovation", "description": "We continuously innovate to simplify commerce and make money management easier for everyone."},
            {"name": "Collaboration", "description": "We work across teams and geographies to deliver seamless financial experiences."},
            {"name": "Wellness", "description": "We care about our employees and communities. Healthy teams build better products."},
            {"name": "Customer Champion", "description": "We put customers at the center of everything. Their trust is our most important asset."},
        ],
        "interview_focus": "Demonstrate experience with payments, security, or large-scale financial systems. Show customer empathy and inclusion mindset.",
        "interview_tips": [
            "PayPal values financial inclusion — show how your work helps underserved populations",
            "Security and trust are paramount in fintech — demonstrate risk awareness",
            "Show experience with high-throughput, low-latency systems",
            "Collaboration across global teams is important — show cross-cultural teamwork",
        ],
    },
    {
        "name": "Revolut",
        "slug": "revolut",
        "principle_type": "Cultural Principles",
        "principles": [
            {"name": "Think Deeper", "description": "We question assumptions and dig into the details. Surface-level analysis is not enough."},
            {"name": "Deliver Wow", "description": "We aim to deliver experiences that make customers say 'wow.' Good enough is never enough."},
            {"name": "Get It Done", "description": "We are relentless in execution. We set ambitious targets and find ways to hit them."},
            {"name": "Dream Team", "description": "We hire the best and expect the best. High performers thrive here."},
            {"name": "Never Settle", "description": "We are never satisfied. There is always a way to improve the product, the process, or ourselves."},
        ],
        "interview_focus": "Show extreme ownership, high performance, and customer obsession. Demonstrate ability to work at very high velocity.",
        "interview_tips": [
            "Revolut has an intense, high-performance culture — show drive and resilience",
            "Quantify everything — metrics-driven thinking is essential",
            "Show you can deliver under pressure and tight deadlines",
            "Customer experience obsession is key — show product thinking",
            "Be prepared for very rigorous, multi-round interviews",
        ],
    },
    {
        "name": "Plaid",
        "slug": "plaid",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Start with Why", "description": "We understand why before we build what. Every project starts with a clear problem statement."},
            {"name": "Build Together", "description": "We build great products through cross-functional collaboration and shared ownership."},
            {"name": "Iterate and Learn", "description": "We ship, measure, learn, and iterate. We're comfortable with uncertainty and rapid change."},
            {"name": "Win for Developers", "description": "Our customers are developers. We build APIs they love and documentation they can actually use."},
            {"name": "Act with Integrity", "description": "We handle financial data responsibly. Trust is foundational to everything we do."},
        ],
        "interview_focus": "Demonstrate API design expertise, developer empathy, and financial data responsibility. Show iterative product development skills.",
        "interview_tips": [
            "Plaid is developer-focused — show experience building APIs or developer tools",
            "Financial data security and compliance awareness is important",
            "Show how you've iterated on products based on developer feedback",
            "Cross-functional collaboration is valued — show teamwork examples",
        ],
    },
    {
        "name": "Affirm",
        "slug": "affirm",
        "principle_type": "Core Values",
        "principles": [
            {"name": "People Come First", "description": "We put people before profits. Our products are designed to help, not exploit, consumers."},
            {"name": "No Fine Print", "description": "We are radically transparent. No hidden fees, no gotchas, no confusing terms."},
            {"name": "It's On Us", "description": "We take responsibility. When something goes wrong, we own it and fix it."},
            {"name": "Simplify", "description": "We make complex financial concepts simple and accessible to everyone."},
            {"name": "Endure", "description": "We build for the long term. Short-term hacks are not acceptable when they compromise trust."},
        ],
        "interview_focus": "Show commitment to ethical financial products, consumer advocacy, and transparency. Demonstrate long-term thinking over short-term gains.",
        "interview_tips": [
            "Affirm deeply values honesty and transparency — show ethical decision-making",
            "Consumer financial health focus — demonstrate empathy for borrowers",
            "Show how you've simplified complex systems or concepts",
            "Long-term thinking matters — avoid examples of cutting corners",
        ],
    },
    {
        "name": "Robinhood",
        "slug": "robinhood",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Democratize Finance", "description": "We make financial markets accessible to everyone, not just the wealthy."},
            {"name": "Customer First", "description": "Every decision should improve the experience for our customers."},
            {"name": "Radical Transparency", "description": "We communicate openly with customers, regulators, and each other."},
            {"name": "Pioneering Spirit", "description": "We challenge the status quo and aren't afraid to try new approaches."},
            {"name": "Responsible Growth", "description": "We grow thoughtfully, ensuring our platform is safe and reliable."},
        ],
        "interview_focus": "Demonstrate passion for financial democratization, consumer-first product thinking, and building reliable financial infrastructure.",
        "interview_tips": [
            "Robinhood's mission is financial democratization — connect your work to broadening access",
            "Reliability and trust are critical — show experience with high-uptime systems",
            "Show product intuition for consumer-facing financial features",
            "Be prepared to discuss regulatory awareness and compliance",
        ],
    },

    # -----------------------------------------------------------------------
    # Big Tech / Hardware / Semiconductor
    # -----------------------------------------------------------------------
    {
        "name": "Samsung",
        "slug": "samsung",
        "principle_type": "Core Values",
        "principles": [
            {"name": "People", "description": "We value our people and dedicate ourselves to giving them a wealth of opportunities."},
            {"name": "Excellence", "description": "We dedicate ourselves to making the best products and services through relentless pursuit of quality."},
            {"name": "Change", "description": "We embrace change and drive innovation. Standing still is falling behind."},
            {"name": "Integrity", "description": "We operate ethically, with transparency and fairness in all business dealings."},
            {"name": "Co-Prosperity", "description": "We pursue mutual growth with our partners, communities, and the world at large."},
        ],
        "interview_focus": "Show hardware-software integration expertise, global mindset, and relentless quality focus. Demonstrate innovation in consumer electronics or semiconductor domains.",
        "interview_tips": [
            "Samsung values quality obsession — show rigorous testing and engineering discipline",
            "Global company — demonstrate cross-cultural communication skills",
            "Innovation in hardware-software integration is highly valued",
            "Show how you've driven change or adopted new technologies",
        ],
    },
    {
        "name": "Intel",
        "slug": "intel",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Customer First", "description": "We listen to and learn from our customers. Their success is our success."},
            {"name": "Fearless Innovation", "description": "We push boundaries and embrace bold ideas. Innovation requires courage."},
            {"name": "Inclusion", "description": "We value diverse perspectives. The best solutions come from diverse teams."},
            {"name": "Quality", "description": "We set and achieve the highest standards of excellence in everything we do."},
            {"name": "One Intel", "description": "We work as one team, collaborating across boundaries to achieve shared goals."},
            {"name": "Results Orientation", "description": "We focus on outcomes, not just activity. Execution matters."},
        ],
        "interview_focus": "Demonstrate deep technical expertise in hardware, silicon, or systems engineering. Show innovation mindset and collaborative problem-solving.",
        "interview_tips": [
            "Intel values deep technical expertise — be ready for detailed technical discussions",
            "Show innovation in hardware, systems, or architecture domains",
            "Cross-team collaboration is important — show 'One Intel' mindset",
            "Results-oriented — quantify impact of your work",
        ],
    },
    {
        "name": "Qualcomm",
        "slug": "qualcomm",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Innovation", "description": "We pioneer breakthrough technologies that transform how the world connects, computes, and communicates."},
            {"name": "Execution", "description": "Great ideas need great execution. We deliver reliably and efficiently."},
            {"name": "Partnership", "description": "We work closely with our ecosystem partners to create solutions greater than any of us could build alone."},
            {"name": "Integrity", "description": "We conduct business with the highest ethical standards and respect for intellectual property."},
            {"name": "Quality", "description": "We build products that work reliably in the most demanding environments — from phones to cars to IoT."},
        ],
        "interview_focus": "Show wireless/mobile technology expertise, strong execution skills, and ecosystem partnership thinking. Demonstrate experience shipping at scale.",
        "interview_tips": [
            "Qualcomm values deep wireless/mobile/embedded expertise",
            "Show experience with shipping products that serve billions of devices",
            "Partnership ecosystem thinking is valued — show cross-company collaboration",
            "IP and innovation focus — demonstrate original thinking and invention",
        ],
    },
    {
        "name": "AMD",
        "slug": "amd",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Innovation", "description": "We design high-performance computing and graphics solutions that push the boundaries of what's possible."},
            {"name": "Passion", "description": "We are passionate about our technology, our customers, and making a difference in people's lives."},
            {"name": "Integrity", "description": "We are honest, ethical, and committed to doing the right thing."},
            {"name": "Accountability", "description": "We take responsibility for our commitments and deliver on our promises."},
            {"name": "One AMD", "description": "We collaborate as one global team, leveraging diverse perspectives to achieve shared goals."},
        ],
        "interview_focus": "Demonstrate high-performance computing expertise, competitive engineering mindset, and collaborative team spirit. Show passion for pushing performance boundaries.",
        "interview_tips": [
            "AMD values competitive engineering drive — show how you've outperformed alternatives",
            "High-performance computing expertise is critical — CPU, GPU, or systems-level",
            "Show passion for technology and performance optimization",
            "Accountability matters — demonstrate owning commitments and delivering",
        ],
    },

    # -----------------------------------------------------------------------
    # Cloud / Developer Tools
    # -----------------------------------------------------------------------
    {
        "name": "Cloudflare",
        "slug": "cloudflare",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Build a Better Internet", "description": "Our mission is to help build a better internet. Every product should make the internet faster, safer, and more reliable."},
            {"name": "Curiosity", "description": "We are endlessly curious about how the internet works and how we can improve it."},
            {"name": "Transparency", "description": "We share what we learn, publish our research, and communicate openly with our users."},
            {"name": "Empathy", "description": "We care about our customers and each other. We build products that work for everyone, from small blogs to Fortune 500 companies."},
            {"name": "Bias for Action", "description": "We move quickly to protect and serve our customers. Security threats don't wait, and neither do we."},
        ],
        "interview_focus": "Show passion for internet infrastructure, security, and performance. Demonstrate systems-level thinking and ability to operate at massive scale.",
        "interview_tips": [
            "Cloudflare handles a significant portion of internet traffic — show scale experience",
            "Security mindset is essential — demonstrate threat awareness and defensive thinking",
            "Systems-level engineering is valued — show deep networking or infrastructure knowledge",
            "Transparency is cultural — Cloudflare blogs extensively, show your communication skills",
        ],
    },
    {
        "name": "Vercel",
        "slug": "vercel",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Developer Experience", "description": "We obsess over developer experience. If it's hard to use, we haven't finished building it."},
            {"name": "Ship Early, Ship Often", "description": "We believe in incremental delivery. Small, frequent deploys beat big-bang releases."},
            {"name": "Performance by Default", "description": "Performance shouldn't require configuration. Our products are fast out of the box."},
            {"name": "Open Source", "description": "We build on and contribute to open source. Next.js is our gift to the web community."},
        ],
        "interview_focus": "Demonstrate frontend/fullstack expertise, developer tooling passion, and obsession with performance. Show experience with modern web frameworks.",
        "interview_tips": [
            "Vercel is the company behind Next.js — deep React/Next.js knowledge is expected",
            "Developer experience obsession is core — show how you've simplified complex workflows",
            "Performance optimization is valued — demonstrate web performance expertise",
            "Open-source contributions and community engagement are strong signals",
        ],
    },
    {
        "name": "Netlify",
        "slug": "netlify",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Empower Web Developers", "description": "We make web development simpler, faster, and more enjoyable for developers everywhere."},
            {"name": "Open Web Standards", "description": "We champion the open web and build on standards that benefit the entire ecosystem."},
            {"name": "Composable Architecture", "description": "We believe in modular, composable approaches to web development over monolithic frameworks."},
            {"name": "Remote-First Culture", "description": "We are remote-first by design, building a culture of trust, autonomy, and asynchronous communication."},
        ],
        "interview_focus": "Show passion for web development, JAMstack architecture, and developer experience. Demonstrate comfort with remote-first work culture.",
        "interview_tips": [
            "Netlify pioneered the JAMstack — show knowledge of modern web architecture",
            "Developer experience and simplicity are paramount",
            "Remote-first culture — demonstrate async communication and self-direction",
            "Open web standards and composable architecture knowledge is valued",
        ],
    },
    {
        "name": "Supabase",
        "slug": "supabase",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Open Source", "description": "We are open source to the core. Our products are built on and contribute to PostgreSQL and the open-source ecosystem."},
            {"name": "Developer Love", "description": "We build tools that developers love to use. Great DX is our competitive advantage."},
            {"name": "Ship Fast", "description": "We ship features fast, gather feedback, and iterate. Launch weeks are a Supabase tradition."},
            {"name": "Transparency", "description": "We build in public, share our metrics, and communicate openly with our community."},
            {"name": "PostgreSQL First", "description": "We bet on PostgreSQL. We don't abstract it away — we make it more accessible."},
        ],
        "interview_focus": "Demonstrate PostgreSQL expertise, open-source passion, and developer-first product thinking. Show ability to ship fast and iterate.",
        "interview_tips": [
            "Supabase is built on PostgreSQL — deep database knowledge is valued",
            "Open-source contributions are a strong signal",
            "Show you can ship quickly — Supabase has a culture of rapid iteration",
            "Developer experience focus — show how you've built tools developers love",
            "Building in public and transparency are cultural values",
        ],
    },

    # -----------------------------------------------------------------------
    # Enterprise / SaaS
    # -----------------------------------------------------------------------
    {
        "name": "Twilio",
        "slug": "twilio",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Write It Down", "description": "We document our thinking. Written proposals drive clarity and better decisions."},
            {"name": "Be an Owner", "description": "We act like owners, not renters. We take responsibility for outcomes, not just tasks."},
            {"name": "Empower Others", "description": "We build APIs that empower millions of developers to build communication experiences."},
            {"name": "Don't Settle", "description": "We set high standards and continuously raise the bar. Good enough is never enough."},
            {"name": "Be Bold", "description": "We take calculated risks and pursue ambitious goals. Playing it safe limits our impact."},
        ],
        "interview_focus": "Show API design expertise, developer empathy, and strong written communication. Demonstrate ownership mentality and technical depth.",
        "interview_tips": [
            "Twilio values strong written communication — 'Write It Down' is a real practice",
            "API and developer platform experience is highly relevant",
            "Show ownership of outcomes, not just individual contributions",
            "Demonstrate how you've empowered other developers through your work",
        ],
    },
    {
        "name": "Atlassian",
        "slug": "atlassian",
        "principle_type": "Core Values",
        "principles": [
            {"name": "Open Company, No Bullshit", "description": "We share information openly and communicate honestly, even when it's uncomfortable."},
            {"name": "Build with Heart and Balance", "description": "We bring passion to our work and care about sustainable, balanced effort."},
            {"name": "Don't #@!% the Customer", "description": "We put customers first and never ship something we know will hurt their experience."},
            {"name": "Play, as a Team", "description": "We collaborate joyfully, celebrate wins together, and have fun building great products."},
            {"name": "Be the Change You Seek", "description": "We take initiative and drive improvement. We don't wait for someone else to fix things."},
        ],
        "interview_focus": "Show customer-first mindset, collaborative team spirit, and transparent communication. Demonstrate values alignment with openness and integrity.",
        "interview_tips": [
            "Atlassian values radical honesty — 'Open Company, No Bullshit' is a real value",
            "Customer obsession is critical — show how you've protected user experience",
            "Team collaboration and joyful work culture are important signals",
            "Show initiative and proactive problem-solving — don't wait to be told",
            "Atlassian has a strong values interview — prepare values-aligned stories",
        ],
    },

    # -----------------------------------------------------------------------
    # Generic / Catch-All
    # -----------------------------------------------------------------------
    {
        "name": "Startup (Generic)",
        "slug": "startup",
        "principle_type": "Common Startup Traits",
        "principles": [
            {"name": "Ownership", "description": "In a startup, everyone owns everything. You don't wait for permission — you take initiative."},
            {"name": "Resourcefulness", "description": "Startups don't have infinite resources. You find creative solutions with what's available."},
            {"name": "Adaptability", "description": "Plans change. Markets shift. Startups thrive on flexibility and rapid pivoting."},
            {"name": "Bias for Action", "description": "Done is better than perfect. Ship fast, learn from users, and iterate."},
            {"name": "Scrappiness", "description": "You wear multiple hats, figure things out from scratch, and get things done without a playbook."},
        ],
        "interview_focus": "Emphasize versatility, speed, and thriving in ambiguity. Show you can do more with less.",
        "interview_tips": [
            "Startups value generalists who can wear multiple hats",
            "Show comfort with ambiguity — no playbook, figure it out",
            "Speed of execution is paramount — show you ship fast",
            "Demonstrate ownership: you don't wait for instructions",
        ],
    },
    {
        "name": "Other",
        "slug": "other",
        "principle_type": "General Tech Values",
        "principles": [
            {"name": "Technical Excellence", "description": "Strong engineering fundamentals, clean code, and thoughtful architecture."},
            {"name": "Collaboration", "description": "Working effectively with diverse teams across functions and geographies."},
            {"name": "Impact Focus", "description": "Prioritizing work that creates meaningful business or user impact."},
            {"name": "Continuous Learning", "description": "Staying current with technology trends and always improving your craft."},
        ],
        "interview_focus": "Focus on clear impact, technical competence, and teamwork. Universal behavioral qualities.",
        "interview_tips": [
            "Focus on universal qualities: impact, collaboration, technical depth",
            "Quantify your results wherever possible",
            "Show adaptability and learning from failure",
            "Demonstrate clear STAR structure in every answer",
        ],
    },
]

# fmt: on


async def seed():
    """Insert all companies (skip duplicates by slug)."""
    await init_db()

    async with AsyncSessionLocal() as db:
        for company_data in COMPANIES:
            # Check if already exists
            from sqlalchemy import select

            result = await db.execute(
                select(CompanyProfile).where(
                    CompanyProfile.slug == company_data["slug"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  ⏭  {company_data['name']} already exists, skipping")
                continue

            company = CompanyProfile(**company_data)
            db.add(company)
            print(f"  ✅ {company_data['name']} ({len(company_data['principles'])} principles)")

        await db.commit()

    print(f"\n🏢 Seeded {len(COMPANIES)} company profiles")


if __name__ == "__main__":
    asyncio.run(seed())
