# Consumer Spending SME: Cross-SME Answers
## Proteus Requirements Elaboration — Phase 2

---

## Questions from Market Analyst SME

### Question 1: Seasonal Spending Patterns

> What seasonal spending patterns are realistic for synthetic data? Are there specific holidays/events (Prime Day, Black Friday, Super Bowl) that should show distinct spikes? What magnitude of spike is realistic (10%? 50%? 200%?)?

**Answer:**

Consumer transaction data exhibits predictable seasonal patterns that analysts expect to see in any credible dataset. The key is that spikes vary dramatically by category -- a 200% spike in one category is normal while the same magnitude in another would be suspicious.

**Retail Categories (Apparel, Department Stores, Discount Stores):**

| Event/Period | Transaction Volume Change | Duration |
|-------------|---------------------------|----------|
| Black Friday (Nov Friday after Thanksgiving) | +150% to +250% vs. average Friday | Single day, spillover Sat/Sun |
| Cyber Monday | +100% to +180% | Single day |
| Christmas Eve (Dec 24) | +80% to +120% | Single day |
| Dec 15-23 (peak holiday shopping) | +60% to +100% vs. surrounding days | ~9 days |
| Post-Christmas (Dec 26) | +40% to +80% (gift card redemption) | 1-2 days |
| January (post-holiday) | -20% to -35% (normalization) | Full month |

**Grocery and Essentials:**

| Event/Period | Transaction Volume Change | Duration |
|-------------|---------------------------|----------|
| Thanksgiving week | +40% to +70% | 5-7 days |
| Super Bowl week | +25% to +45% (food/beverage) | 5-7 days |
| Christmas week | -15% to -30% (people traveling, eating out) | 5-7 days |

**Restaurant/Dining:**

| Event/Period | Transaction Volume Change | Duration |
|-------------|---------------------------|----------|
| Valentine's Day (Feb 14) | +50% to +80% (fine dining) | 1-2 days |
| Mother's Day | +60% to +100% | Weekend |
| Super Bowl Sunday | +35% to +55% | Single day |
| New Year's Eve | +70% to +120% | Single day |
| Date night (Fri/Sat vs. weekday) | +30% to +50% baseline | Recurring |

**Back-to-School (August-September):**

This is the second-largest retail season. The magnitude varies significantly by subcategory:

| Subcategory | Volume Increase | Duration |
|------------|-----------------|----------|
| Office supplies | +80% to +120% | 4-6 weeks |
| Apparel (youth) | +40% to +70% | 4-6 weeks |
| Electronics | +30% to +60% | 3-5 weeks |
| Department stores (mixed) | +25% to +45% | 4-6 weeks |

**E-commerce Specific Events:**

| Event/Period | Channel Impact | Duration |
|-------------|----------------|----------|
| Prime Day (July, typically) | +200% to +400% on Amazon-specific categories | 2 days |
| Cyber Monday | +100% to +180% online | 1 day |
| Black Friday | +80% to +150% online | 1 day + weekend |

**What NOT to Model:**

- Do NOT create uniform 20% spikes across all categories for any event
- Do NOT make holiday spikes perfectly identical year-over-year (real data has variance)
- Do NOT exceed +300% for any single-day event without explicit event justification

**Minimum Viable Seasonal Pattern Set for Synthetic Data Credibility:**

1. Q4 retail spike: 25-40% category-wide increase Nov-Dec
2. December peak within Q4: 15-25% higher than November
3. January trough: 15-25% below Q4 average
4. August-September back-to-school: 20-35% increase in school-related categories
5. Weekend vs. weekday pattern: Saturday +30-35% vs. Monday baseline for retail

---

### Question 2: Generational Spending Profiles

> What are realistic generational spending patterns? Gen Z tends to prefer X brands, Millennials Y, Boomers Z - what spending ratios are realistic?

**Answer:**

Generational spending profiles are one of the most analytically distinctive patterns. Analysts look for these as a credibility check. The key insight is that it's not just WHAT categories generations prefer but the PROPORTION of their spending going to each category.

**Spending Proportion by Category and Generation:**

| Category | Gen Z (18-27) | Millennials (28-43) | Gen X (44-59) | Boomers (60-78) |
|----------|---------------|---------------------|---------------|------------------|
| Grocery | 18% | 22% | 25% | 28% |
| Restaurant/Dining | 22% | 18% | 14% | 10% |
| Apparel/Footwear | 16% | 11% | 8% | 6% |
| Entertainment | 8% | 7% | 5% | 4% |
| Travel | 4% | 9% | 12% | 14% |
| Health/Personal Care | 6% | 7% | 9% | 12% |
| Home Improvement | 2% | 8% | 12% | 10% |
| Electronics | 8% | 5% | 4% | 3% |
| Gas/Automotive | 6% | 7% | 8% | 10% |
| Streaming/Subscriptions | 6% | 4% | 2% | 1% |

**Brand Affinity by Generation:**

| Generation | Preferred Brand Tier | Example Brands | Avoids |
|------------|---------------------|---------------|--------|
| Gen Z | Budget/Value + Trend | Shein, Temu, Duane Reade, Five Below, Uber Eats, DoorDash | Traditional department stores, Amazon (perceived as "parents' brand") |
| Millennials | Mid-tier + Convenience | Target, Trader Joe's, Amazon, Chipotle, Starbucks | Budget extremes; trending toward premium as income grows |
| Gen X | Quality + Value | Costco, Home Depot, Best Buy, Olive Garden | Fad-driven brands; highly price-sensitive |
| Boomers | Traditional + Premium | Macy's, Kroger, local医疗服务, Disney | Fast fashion, TikTok-linked brands |

**Channel Preferences by Generation (Online vs. In-Store):**

| Generation | In-Store | Online | Mobile |
|------------|----------|--------|--------|
| Gen Z | 35% | 25% | 40% |
| Millennials | 40% | 30% | 30% |
| Gen X | 55% | 35% | 10% |
| Boomers | 70% | 28% | 2% |

**Online Channel Growth Trajectory (2019-2024):**

For synthetic data spanning multiple years, apply this approximate trajectory:

| Year | Gen Z Online % | Millennials Online % | Gen X Online % | Boomers Online % |
|------|---------------|--------------------|--------------|-----------------|
| 2019 | 50% | 50% | 28% | 20% |
| 2020 | 65% | 60% | 38% | 28% |
| 2021 | 68% | 62% | 40% | 30% |
| 2022 | 65% | 60% | 38% | 28% |
| 2023 | 63% | 58% | 36% | 27% |
| 2024 | 65% | 60% | 35% | 30% |

Note: 2020 shows COVID acceleration; subsequent years show slight normalization but not full return to pre-COVID ratios.

**Average Transaction Amount Premium by Generation:**

| Generation | At Trend Brands | At Premium Brands | At Value Brands |
|------------|----------------|-------------------|----------------|
| Gen Z | +15% to +25% | -5% to +5% | -10% to -20% |
| Millennials | +5% to +15% | +10% to +20% | -15% to -5% |
| Gen X | 0% to +10% | +20% to +30% | -20% to -10% |
| Boomers | -5% to +5% | +25% to +35% | -25% to -15% |

**Critical Anti-Patterns to Avoid:**

- Do NOT make all generations have identical category proportions (this screams fake data)
- Do NOT give Gen Z high spending at Walmart (strong negative correlation with reality)
- Do NOT make Millennials predominantly shop at Sears or JCPenney (brand obsolescence must be reflected)
- Do NOT give Boomers high engagement with TikTok-shop or Shein

---

### Question 3: Geographic Spending Variation

> What geographic spending patterns exist? Urban vs. suburban vs. rural? Regional preferences (Southwest vs. Northeast)?

**Answer:**

Geographic spending patterns are multidimensional. Analysts expect variation across multiple geographic axes: urban/suburban/rural classification, US Census region, and climate zone.

**Urban/Suburban/Rural Spending Profiles:**

| Category | Urban | Suburban | Rural |
|----------|-------|----------|-------|
| Grocery | 100 (baseline) | 115 | 125 |
| Restaurant/Dining | 130 | 100 | 75 |
| Entertainment | 140 | 95 | 55 |
| Gas/Automotive | 60 | 110 | 145 |
| Public Transit | 120 | 40 | 15 |
| Home Improvement | 70 | 125 | 130 |
| Health Club/Fitness | 150 | 100 | 40 |
| Apparel | 115 | 105 | 80 |

**Urban/Suburban/Rural Transaction Frequency:**

| Location | Weekly Transaction Frequency | Avg Transaction Amount |
|----------|------------------------------|----------------------|
| Urban Core | 1.8x | 85% of national avg |
| Suburban | 1.3x | 105% of national avg |
| Rural | 1.0x | 95% of national avg |

**US Census Region Multipliers:**

| Region | Median Income Index | Spending Multiplier | Key Category Affinities |
|--------|-------------------|-------------------|------------------------|
| Northeast | 1.10 | 1.12 | Healthcare, dining out, financial services |
| Midwest | 0.96 | 0.97 | Grocery, home improvement, automotive |
| South | 0.94 | 0.93 | Gas/auto, discount retail, church donations |
| West | 1.12 | 1.15 | Dining out, entertainment, fitness, outdoor |

**State-Level Variation (Top 10 States by Median Household Income):**

| State | Income Index | Spending Index | Notable Preferences |
|-------|-------------|---------------|--------------------|
| Massachusetts | 1.35 | 1.28 | Healthcare, education, craft beer |
| New Jersey | 1.32 | 1.30 | Retail, dining, personal care |
| Connecticut | 1.30 | 1.25 | Home improvement, luxury goods |
| New Hampshire | 1.25 | 1.22 | Automotive, home improvement |
| Alaska | 1.22 | 1.35 | Gas, groceries (remote area premium) |
| Washington | 1.18 | 1.20 | Tech-related, coffee, outdoor gear |
| Colorado | 1.15 | 1.18 | Fitness, outdoor, craft beverages |
| Utah | 1.12 | 1.10 | Family spending, home goods |
| Oregon | 1.08 | 1.05 | Organic, natural foods, craft goods |
| Minnesota | 1.07 | 1.08 | Grocery, sporting goods, home |

**Climate Zone Category Affinities:**

| Climate Zone | High Spending Categories | Low Spending Categories |
|--------------|-------------------------|------------------------|
| Hot-Humid (Gulf Coast, Florida) | Pool maintenance, AC, mosquito control, seafood | Heating fuel, winter sports |
| Cold-Snow (Upper Midwest, New England) | Heating fuel, winter sports, hot beverages | Pool maintenance, outdoor furniture |
| Desert (Southwest) | Pool maintenance, AC, desert landscaping | Heating fuel, winter sports |
| Mediterranean (California coast) | Outdoor dining, fitness, wine, produce | Heating fuel, winter sports |
| Temperate (Mid-Atlantic, Pacific NW) | Moderate all categories | None standout |

**CBSA/Metro Area Patterns:**

| Metro Type | Spending Character |
|------------|------------------|
| Major Coastal (NYC, LA, SF, Seattle) | +20-40% dining/entertainment vs. national |
| Sunbelt metros (Phoenix, Houston, Atlanta) | +15-25% outdoor/pool categories |
| Midwest industrial (Detroit, Cleveland, Pittsburgh) | +10-20% automotive, lower dining |
| College towns | +30-50% restaurant/coffee near campus |
| Retirement metros (Phoenix-Scottsdale, Sarasota) | +40-60% healthcare, +20% home improvement |

**What Makes Geographic Data Feel Real:**

- Coastal metros show higher dining and entertainment proportions
- Midwest states show higher grocery and utility proportions
- Sunbelt states show outdoor/pool/recreation category strength
- Rural areas show significantly lower entertainment spending
- Gas prices correlation: states with higher gas prices show different refueling patterns

---

### Question 4: Cross-Shopping Overlap Percentages

> What is a realistic cross-shopping overlap percentage between major brands? Is 30% overlap between two brands reasonable?

**Answer:**

Cross-shopping overlap (the percentage of customers who shop at Brand A who also shop at Brand B) is a nuanced metric that varies dramatically by category relationship, brand positioning, and customer demographics.

**Cross-Shopping Overlap Ranges by Brand Relationship Type:**

| Relationship Type | Overlap Range | Example Pair |
|-----------------|--------------|--------------|
| Direct Competitors (same tier) | 40-60% | Target vs. Walmart |
| Direct Competitors (different tiers) | 20-40% | Walmart vs. Dollar General |
| Adjacent Categories | 15-35% | Target vs. Amazon |
| Complementary (different need) | 8-20% | Chipotle vs. Target |
| No logical connection | 3-10% | Rolex vs. Aldi |

**Major Brand Cross-Shopping Matrix (Illustrative):**

| Brand | Walmart | Target | Amazon | Costco | Whole Foods | Home Depot | Starbucks |
|-------|---------|--------|--------|--------|------------|------------|-----------|
| **Walmart** | 100% | 52% | 45% | 28% | 12% | 18% | 35% |
| **Target** | 52% | 100% | 48% | 22% | 15% | 20% | 42% |
| **Amazon** | 45% | 48% | 100% | 25% | 18% | 15% | 38% |
| **Costco** | 28% | 22% | 25% | 100% | 30% | 35% | 20% |
| **Whole Foods** | 12% | 15% | 18% | 30% | 100% | 8% | 22% |
| **Home Depot** | 18% | 20% | 15% | 35% | 8% | 100% | 10% |
| **Starbucks** | 35% | 42% | 38% | 20% | 22% | 10% | 100% |

**Category-Specific Cross-Shopping:**

| Category Pair | Overlap Range | Explanation |
|--------------|--------------|-------------|
| Discount Retailer to Discount Retailer | 50-65% | Walmart ↔ Target, Dollar General ↔ Dollar Tree |
| Grocery to Warehouse Club | 30-45% | Kroger ↔ Costco, Safeway ↔ Sam's Club |
| Department Store to Department Store | 35-50% | Macy's ↔ Nordstrom, Kohl's ↔ JCPenney |
| Fast Food to Fast Food | 40-60% | McDonald's ↔ Burger King, Chipotle ↔ Qdoba |
| Fast Food to Quick Service Coffee | 45-65% | McDonald's ↔ Starbucks (breakfast overlap) |
| Luxury to Luxury | 25-40% | Nordstrom ↔ Saks, BMW ↔ Mercedes |
| Luxury to Discount | 5-15% | Rolex ↔ Casio, Apple ↔ Samsung budget |

**Demographic Moderators of Cross-Shopping:**

| Demographic Factor | Effect on Overlap |
|-------------------|------------------|
| Higher income | Lower cross-shopping within category (more brand loyalty) |
| Younger age (Gen Z) | Higher cross-shopping (exploring, deal-seeking) |
| Urban location | Higher cross-shopping (more retail options accessible) |
| Suburban location | Lower cross-shopping (fewer options, more trip-chaining) |
| Higher income + Older | Lowest cross-shopping (strong brand loyalty) |

**Key Insight for Synthetic Data:**

A 30% overlap between two brands is **entirely reasonable** for direct competitors in the same tier, especially for mass-market retailers. However:

- 30% between completely unrelated categories (e.g., a luxury jeweler and a discount grocery) would be suspicious
- 30% between mass-market competitors (Target vs. Walmart) is LOW -- expect 50%+
- 30% between adjacent category brands (Target and Amazon) is realistic

**Cross-Shopping Anti-Patterns That Signal Fake Data:**

- 0% or near-zero overlap between any two brands in the same category
- 80%+ overlap between competitors (indicates duplicate customer bases, rare except in very concentrated markets)
- Identical overlap percentages across all brand pairs
- No variation by income band or generation

---

## Questions from AI/NLP Architecture SME

### Question 1: Synthetic Data Correlations

> What real-world correlations are most recognizable? For example: (a) holiday season retail spike, (b) back-to-school category shifts, (c) generational preference for online channel, (d) income-brand correlation. These need to be embedded for the dataset to be analytically credible.

**Answer:**

The four correlations mentioned are all high-priority. In addition, the following are equally critical:

**Priority 1 (Must Have for Credibility):**

1. **Holiday Season Retail Spike (Q4)**
   - Retail categories: 25-40% volume increase Nov-Dec vs. Oct baseline
   - Gift card categories: Dec spike with Jan redemption
   - Restaurant: Moderate Dec increase (family gatherings)
   - See Question 1 above for specific magnitudes

2. **Income-Brand Correlation**
   - Upper income ($150K+): 70-80% of transactions at premium/national brands; <10% at Walmart/dollar stores
   - Mid income ($50K-$100K): Mixed; 40-50% at mid-tier, 30% at value
   - Lower income (<$35K): 50-60% at Walmart/dollar stores, higher % at grocery
   - This correlation is STRONG and analysts will immediately reject data where high-income customers heavily shop at Walmart

3. **Generational Category Proportions**
   - Gen Z: 22%+ to dining/delivery, 16%+ to apparel/fast fashion, low travel
   - Millennials: 18%+ to grocery (family households), 12%+ to home improvement
   - Boomers: 28%+ to healthcare, 14%+ to travel, 10%+ to dining
   - See Question 2 above for full breakdown

4. **Weekend vs. Weekday Patterns**
   - Retail Saturday: +30-35% vs. Monday baseline
   - Restaurant Friday/Saturday: +40-50% vs. Tuesday/Wednesday
   - Grocery Saturday/Sunday: +35-40% vs. weekday average

**Priority 2 (Important for Realism):**

5. **Channel Shift Over Time**
   - Online share growing 2-4 percentage points per year (2019-2024)
   - COVID acceleration in 2020 (+8-12pp in categories that shifted)
   - Subsequent normalization but not full return

6. **Category Seasonality Signatures**
   - Apparel: Strong Q4, weak Q1
   - Home improvement: Spring/Summer peak (March-August)
   - Tourism: Summer peak, December dip
   - Florists: Valentine's Day (Feb), Mother's Day (May) spikes

7. **Geographic Category Mix**
   - Coastal metros: +20-30% dining/entertainment
   - Sunbelt: +15-25% outdoor/recreation
   - Midwest: +10-15% grocery/automotive
   - Rural: +20-30% gas/auto, -30-40% entertainment

**Priority 3 (Subtle but Important):**

8. **Card Type by Category**
   - Credit cards: 65%+ of travel, dining, entertainment transactions
   - Debit: 70%+ of grocery, utilities, everyday spending
   - Prepaid: Concentrated in underbanked demographics, gift cards

9. **Transaction Amount Distribution (Log-Normal)**
   - Real transaction amounts are right-skewed; not normally distributed
   - Mean > median; long tail of high-value purchases
   - Category-specific distributions: grocery mean ~$45, dining mean ~$28

10. **Brand Switching vs. Loyalty by Segment**
    - High-income + older: 70%+ repeat purchase probability
    - Low-income + younger: 40-50% repeat purchase (more exploratory)

---

### Question 2: Dimension Cardinality

> What is realistic cardinality for each dimension in the synthetic dataset? Specifically: how many distinct brands (100+ mentioned in HLRD), merchant categories (10? 20?), geographic granularities (states only, or metro areas too?). This affects both data generation and tool design.

**Answer:**

**Brand Cardinality:**

| Tier | Count | Example Brands | Purpose |
|------|-------|---------------|---------|
| Mass-market retailers | 15-20 | Walmart, Target, Amazon, Costco, Dollar General, Dollar Tree, Aldi, Lidl, Trader Joe's, Whole Foods, Kroger, Safeway, CVS, Walgreens, Best Buy | Primary competitive analysis set |
| Department stores | 8-10 | Macy's, Nordstrom, Kohl's, JCPenney, Sears, Burlington, Ross, TJ Maxx | Reflects retail secular trends |
| Fast food / QSR | 15-20 | McDonald's, Burger King, Wendy's, Taco Bell, Chipotle, Subway, Domino's, Papa John's, Chick-fil-A, Popeyes, Sonic, Arby's | Common analyst queries |
| Casual dining | 10-15 | Applebee's, Chili's, Olive Garden, Red Lobster, Cheesecake Factory, Outback, Buffalo Wild Wings | Dining category |
| Coffee / Quick service | 5-8 | Starbucks, Dunkin', Dutch Bros, Peet's, Philz | Brand-specific analysis |
| Apparel / Footwear | 15-20 | Nike, Adidas, Lululemon, Under Armour, Gap, Old Navy, H&M, Zara, Shein, Temu | Fashion category |
| Automotive | 8-10 | Shell, Exxon, Chevron, BP, Marathon, Speedway, Valero | Gas station category |
| Home improvement | 5-8 | Home Depot, Lowe's, Ace Hardware, Sherwin-Williams | Home category |
| Electronics | 5-8 | Apple, Samsung, Dell, HP, Best Buy (retailer), Microsoft | Tech category |
| Streaming / Entertainment | 8-10 | Netflix, Hulu, Disney+, HBO Max, Spotify, Amazon Prime Video, Apple TV+ | Subscription tracking |

**Total: ~100-125 brands** provides comprehensive coverage without overwhelming

**Merchant Category Cardinality:**

| Category Group | Subcategories | Notes |
|---------------|---------------|-------|
| Grocery | 3-4 | Supermarket, discount grocery, organic, convenience store |
| Restaurant | 4-5 | Fast food, QSR dining, casual dining, fine dining, coffee |
| Retail | 8-10 | Department store, discount, apparel, electronics, home goods, office supplies, pharmacy |
| Gas / Auto | 2-3 | Gas stations, auto parts, car washes |
| Entertainment | 3-4 | Movies, events, sports, gaming |
| Travel | 3-4 | Hotels, airlines, rental cars, travel agencies |
| Healthcare | 2-3 | Pharmacy, health services |
| Utilities | 2-3 | Electric, gas, water |
| Financial Services | 2-3 | Banks, ATMs, insurance |
| Services | 4-5 | Hair salons, dry cleaning, repair |

**Total: 35-45 categories** is sufficient. Full MCC taxonomy (600+ codes) is overkill and fragments analysis.

**Geographic Cardinality:**

| Level | Count | Required for Demo? | Notes |
|-------|-------|-------------------|-------|
| State | 51 | YES | All 50 states + DC |
| Census Region | 4 | YES | NE, MW, S, W |
| CBSA (Metro Area) | 380-400 | RECOMMENDED | Major metros enable regional analysis |
| MSA | 380-400 | Optional | Subset of CBSAs |
| 3-digit ZIP | 800-1000 | Nice-to-have | Too granular for demo; use state or metro |
| Urban/Suburban/Rural | 3 | YES | Derived classification |

**Recommended Minimum: State + CBSA + Urban/Suburban/Rural**

**Time Dimension:**

| Level | Values | Notes |
|-------|--------|-------|
| Daily | 730+ | 2 years of data |
| Weekly | 104 | Useful for smooth trending |
| Monthly | 24 | Standard for reporting |
| Quarterly | 8 | 2 years = 8 quarters |
| Year | 2 | Minimum for YoY comparison |

---

### Question 3: Query Pattern Expectations

> What follow-up queries do analysts typically make after initial results? For example, after seeing market share, do they typically ask "why is that?" (attribution) or "how has that changed?" (trend). This informs multi-turn conversation design.

**Answer:**

**Post-Market Share Query Follow-ups:**

| Follow-up Type | Frequency | Example |
|---------------|-----------|---------|
| Trend drill-down | 65% | "How has that changed over the past 2 years?" / "Show me the quarterly trend" |
| Demographic breakdown | 50% | "Is this share consistent across age groups?" / "Which generations are driving this?" |
| Geographic breakdown | 45% | "Is this share different in the Northeast vs. South?" / "Which states is this strongest?" |
| Competitive context | 40% | "Who is taking this share from them?" / "Which competitors are gaining?" |
| Attribution | 25% | "Why is share declining?" / "What categories are driving this?" |
| Channel context | 20% | "Is this shift happening online or in-store?" / "How is their e-commerce performing?" |

**Post-Growth/Trend Query Follow-ups:**

| Follow-up Type | Frequency | Example |
|---------------|-----------|---------|
| Cause drill-down | 55% | "What's driving that growth?" / "Which categories contributed most?" |
| Comparison | 50% | "How does this compare to the category overall?" / "Is X growing faster than Y?" |
| Outlook/forecast | 30% | "Is this trend expected to continue?" / "What's the projected growth?" |
| Anomaly investigation | 25% | "Why did it spike in March?" / "What happened in Q2?" |
| Customer profile | 20% | "Who's driving this growth?" / "Is this new customers or repeat?" |

**Post-Cross-Shopping Query Follow-ups:**

| Follow-up Type | Frequency | Example |
|---------------|-----------|---------|
| Trend in overlap | 45% | "Has this overlap been increasing or decreasing?" / "When did this relationship start?" |
| Demographic skew | 40% | "Is this overlap higher for younger customers?" / "Which income groups show this?" |
| Causal investigation | 25% | "Why do these brands overlap?" / "What category triggers both?" |
| Competitive threat | 35% | "Should I be worried about Brand X taking customers from Brand Y?" |

**Post-Demographic Query Follow-ups:**

| Follow-up Type | Frequency | Example |
|---------------|-----------|---------|
| Trend over time | 60% | "Is the customer base getting younger or older?" / "How has the income mix changed?" |
| Geographic view | 40% | "Where are these customers located?" / "Is this consistent nationally?" |
| Channel preference | 30% | "How do these customers prefer to shop?" / "What % is online?" |
| Competitive comparison | 35% | "How does this compare to their main competitor?" / "Who's winning the younger demographic?" |

**Query Flow Patterns (High Frequency Sequences):**

1. **Market Share Query Flow:**
   "What's Brand X's share?" → "How has that trended?" → "Who are they losing share to?"

2. **Competitive Battle Flow:**
   "Brand X vs. Brand Y in category" → "Drill into generation breakdown" → "Show by geography"

3. **Trend Investigation Flow:**
   "Show spending trends" → "Why did it spike?" → "What categories drove this?"

4. **New Market Entry Flow:**
   "Show category by geography" → "Where is Brand X underperforming?" → "What's the gap?"

**Key Implication for Conversation Design:**

The system should support:
- Implicit context carry-forward (if user asks "Show me Target's share", then "How has that trended?" should implicitly use Target)
- Dimension drilling ("drill into generation" should maintain brand/category context)
- Comparative follow-ups ("compare to Walmart" should combine with existing context)
- Reference resolution ("that" or "it" must resolve to the most recent query's subject)

---

## Summary of Key Recommendations for Synthetic Data Design

1. **Seasonal Patterns:** Model Q4 retail spike (25-40%) with Dec peak, Jan trough, and Aug-Sep back-to-school (20-35%). Individual events (Black Friday, Prime Day) can show +150-250% spikes but only for specific categories.

2. **Generational Profiles:** Gen Z skews toward dining/delivery/apparel/fast fashion with high online channel usage. Boomers skew toward healthcare/travel/dining-in with high in-store preference. Millennials bridge both with family-spending patterns.

3. **Geographic Variation:** Coastal metros show +20-40% dining/entertainment; Sunbelt shows outdoor/recreation strength; Midwest shows grocery/automotive; Rural shows significantly lower entertainment.

4. **Cross-Shopping:** 30% overlap is reasonable for related but not identical brands. Direct competitors (Target vs. Walmart) show 50%+ overlap. Unrelated brands should show <15% overlap.

5. **Critical Correlations:** Income-brand correlation is the most scrutinized by analysts. High-income customers must shop at premium brands, not Walmart.

6. **Query Follow-ups:** The most common follow-ups are trend queries (65%) and demographic/geographic breakdowns (45-50%). Plan conversation context for these flows.
