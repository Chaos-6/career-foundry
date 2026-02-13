"""
Seed the company_profiles table with 22+ tier 1 tech companies.

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
