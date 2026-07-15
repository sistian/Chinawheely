# Chinawheely SEO Strategy & Implementation Plan

## 1. Keyword Research & Targeting

### Primary Keywords (High Volume, High Intent)
| Keyword | Monthly Search Volume | Difficulty | Target Page |
|---------|----------------------|------------|-------------|
| airport transfer china | 1,200 | Medium | Homepage / Booking |
| china airport transfer | 900 | Medium | Homepage |
| beijing airport transfer | 2,400 | High | City-specific landing |
| shanghai airport transfer | 2,100 | High | City-specific landing |
| private car service china | 600 | Low | Services page |
| china car service with driver | 480 | Low | Services page |
| english speaking driver china | 320 | Low | FAQ / Homepage |
| guangzhou airport transfer | 800 | Medium | City-specific landing |
| china airport pickup | 500 | Low | Homepage |
| transfer from beijing airport | 400 | Low | Beijing landing |

### Long-Tail Keywords (High Conversion)
- "how to get from beijing airport to city center"
- "shanghai pudong airport to downtown taxi alternative"
- "reliable car service for foreigners in china"
- "english speaking driver beijing airport"
- "private car great wall day trip from beijing"
- "chengdu panda base car service"
- "xi'an terracotta warriors private tour with car"
- "guangzhou airport to hotel transfer"

### LSI Keywords (Semantic)
- china travel, visiting china, 144 hour visa free transit
- china ground transportation, china car hire
- business travel china, corporate travel china
- family travel china, china with kids
- china tour, china itinerary

## 2. On-Page SEO Implementation

### Meta Tags (Already implemented in HTML)
- Title tag: "Chinawheely | Airport Transfers & Private Car Service in China"
- Description: "Professional airport transfers and private car service across 40+ cities in China. English-speaking drivers, fixed prices, 24/7 support."
- Canonical URL: Set for all pages
- Hreflang: en (English primary), zh (Chinese secondary)

### Heading Structure
- H1: "Your China Journey, Started Right" (Homepage)
- H2: Services, Cities, How It Works, Pricing, FAQ
- H3: Individual service cards, city names, pricing tiers
- H4: Process steps, testimonial names

### Schema.org Structured Data (JSON-LD)

```json
{
  "@context": "https://schema.org",
  "@type": "TravelAgency",
  "name": "Chinawheely",
  "description": "Professional airport transfers and private car service across China",
  "url": "https://www.chinawheely.com",
  "logo": "https://www.chinawheely.com/logo.png",
  "telephone": "+86-15527771775",
  "email": "15527771775@qq.com",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Office 2622, Wuhan Hang Lung Plaza, No. 688 Jinghan Avenue",
    "addressLocality": "Wuhan",
    "addressRegion": "Hubei",
    "addressCountry": "CN"
  },
  "areaServed": [
    {"@type": "City", "name": "Beijing"},
    {"@type": "City", "name": "Shanghai"},
    {"@type": "City", "name": "Guangzhou"},
    {"@type": "City", "name": "Xi'an"},
    {"@type": "City", "name": "Chengdu"}
  ],
  "priceRange": "$$",
  "paymentAccepted": ["PayPal", "Alipay"]
}
```

### FAQ Schema
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What happens if my flight is delayed?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "We track your flight in real-time. For airport pickups, we include 60-90 minutes of free waiting time."
      }
    }
  ]
}
```

## 3. Technical SEO

### URL Structure
- / (Homepage)
- /booking (Booking page)
- /beijing-airport-transfer (City-specific landing)
- /shanghai-airport-transfer
- /chengdu-car-service
- /about
- /careers
- /faq
- /blog (Future content marketing)

### Site Speed Optimization
- All CSS in single file (no render-blocking)
- Lazy load images for city cards
- Preconnect to Google Fonts
- Use WebP format for images
- Minify CSS and JS

### Mobile Optimization
- Responsive design (already implemented)
- Mobile-first indexing ready
- Touch-friendly buttons (min 44px)
- Fast mobile load times

## 4. Content Strategy (Blog)

### Target Topics (SEO-driven)
1. "Complete Guide to Beijing Airport Transfers 2026"
2. "How to Get from Shanghai Pudong to Downtown"
3. "144-Hour Visa Free Transit: What to Do in China"
4. "Best Way to Visit the Great Wall from Beijing"
5. "Chengdu Panda Base: Complete Visitor Guide"
6. "Xi'an Terracotta Warriors: How to Get There"
7. "Do You Need a Car Service in China?"
8. "China Travel Tips for First-Time Visitors"
9. "How to Pay in China as a Foreigner"
10. "Best Cities to Visit in China (Ranked)"

### Content Calendar
- Week 1: Publish 2 city guides
- Week 2: Publish 1 travel tip + 1 FAQ expansion
- Week 3: Publish 1 visa guide + 1 city guide
- Week 4: Publish 1 comparison post + 1 customer story

## 5. Off-Page SEO

### Link Building Strategy
1. **Travel Directories**: List on TripAdvisor, Viator, Klook partner program
2. **Blog Outreach**: Guest post on travel blogs (Nomadic Matt, The Culture Trip)
3. **PR**: Pitch to travel media (Lonely Planet, Travel + Leisure)
4. **Partnerships**: Hotel partnerships with link exchanges
5. **Social Signals**: Active Instagram, TikTok, YouTube presence

### Local SEO (Google Business Profile)
- Create GBP for China operations (if possible)
- Encourage customer reviews
- Post updates and offers

## 6. Analytics & Tracking

### Google Analytics 4 Setup
- Track: bookings, page views, bounce rate, conversion rate
- Events: form submission, button clicks, page scroll depth
- Goals: booking completion, contact form submission

### Google Search Console
- Submit sitemap.xml
- Monitor indexing status
- Track keyword rankings
- Fix crawl errors

### Key Metrics to Track
| Metric | Target (Month 1) | Target (Month 6) |
|--------|-----------------|-----------------|
| Organic Traffic | 500/month | 5,000/month |
| Keyword Rankings (Top 10) | 5 | 50 |
| Domain Authority | 10 | 25 |
| Backlinks | 10 | 100 |
| Booking Conversion Rate | 2% | 5% |

## 7. Implementation Priority

### Phase 1 (Week 1-2): Foundation
- [ ] Implement Schema.org structured data
- [ ] Create XML sitemap
- [ ] Set up Google Analytics 4
- [ ] Set up Google Search Console
- [ ] Submit sitemap to Google
- [ ] Add canonical tags to all pages
- [ ] Optimize image alt text
- [ ] Add Open Graph tags for social sharing

### Phase 2 (Week 3-4): Content
- [ ] Create 5 city-specific landing pages
- [ ] Start blog with 4 posts
- [ ] Optimize existing FAQ for rich snippets
- [ ] Add internal linking between pages
- [ ] Create city comparison pages

### Phase 3 (Month 2-3): Growth
- [ ] Launch link building campaign
- [ ] Partner with 10 hotels for backlinks
- [ ] Submit to travel directories
- [ ] Start guest posting
- [ ] Create video content for YouTube

### Phase 4 (Month 3-6): Scale
- [ ] Expand to 20 city landing pages
- [ ] Launch multi-language versions (CN, JP, KR)
- [ ] Implement advanced analytics
- [ ] A/B test landing pages
- [ ] Retargeting campaigns

## 8. Quick Wins (Immediate)

1. Add FAQ schema to get rich snippets in Google
2. Create city-specific meta titles and descriptions
3. Add "China airport transfer" in H1 and first paragraph
4. Create a blog and publish 2 posts this week
5. Set up Google Business Profile
6. Add review request to post-booking email
7. Create shareable infographics (e.g., "China Airport Transfer Guide")

## 9. Competitive Advantage

### What Competitors Are Missing
- No competitor has comprehensive city-specific landing pages
- No competitor has FAQ schema implemented
- No competitor has a strong blog/content strategy
- No competitor has a dedicated careers page (attracts talent, shows legitimacy)

### Our Unique SEO Angles
- "English-speaking drivers in China" (unique positioning)
- "Fixed price guarantee" (trust signal for SEO)
- "Wuhan-based company with nationwide coverage" (local + national)
- "Travel agency license L-HUB-101603" (trust signal)

## 10. Tools to Use

- **Keyword Research**: Ahrefs, SEMrush, Google Keyword Planner
- **Technical SEO**: Screaming Frog, Google Search Console
- **Analytics**: Google Analytics 4, Google Tag Manager
- **Content**: Surfer SEO, Clearscope
- **Backlinks**: Ahrefs, Moz
- **Local SEO**: BrightLocal
- **Rank Tracking**: AccuRanker, SEMrush

---

*Prepared by Chinawheely SEO Team*
*Date: 2026-06-11*
