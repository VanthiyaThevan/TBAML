# TBAML System - POC Workflow
## Complete End-to-End Process Flow

**System**: Trade-Based Anti-Money Laundering (TBAML)  
**Use Case**: UC1 - Line of Business Verification  
**Type**: Functional Proof of Concept

---

## Workflow Overview

The TBAML POC system performs automated Line of Business (LOB) verification by collecting data from multiple public sources, analyzing it using AI/ML, and generating risk assessments with compliance flags.

**Complete Process**: User Input → Data Collection → Data Storage → AI Analysis → Risk Assessment → Results Display

---

## Detailed Workflow

### PHASE 1: USER INPUT

#### Step 1.1: User Provides Information
**Input Required**:
- **Client/Company Name**: Name of the company to verify
- **Client Country**: Country code (e.g., "US", "GB", "RU")
- **Client Role**: "Import" or "Export"
- **Product Name**: Description of the product/service (optional)

**Entry Points**:
1. **Frontend Web Interface** (React Application)
   - User fills out form in browser
   - Form fields: Company Name, Country, Role (dropdown), Product (optional)
   - Submit button triggers API request

2. **API Endpoint** (Direct API Call)
   - POST request to `/api/v1/lob/verify`
   - JSON payload with input data

#### Step 1.2: Input Validation
**Process**:
- FastAPI validates input using Pydantic schemas
- Checks required fields are present
- Validates country code format
- Validates role is "Import" or "Export"
- Logs the verification request

**Validation Rules**:
- Company name: Required, string
- Country: Required, 2-letter country code
- Role: Required, must be "Import" or "Export"
- Product: Optional string

---

### PHASE 2: DATA COLLECTION

#### Step 2.1: Initialize Data Sources
**Process**:
- System initializes `DataConnector` to manage multiple data sources
- Registers three primary data sources:
  1. **WebScraper**: Scrapes company websites
  2. **CompanyRegistryFetcher**: Fetches company registry data
  3. **SanctionsChecker**: Checks sanctions/watchlists

**Configuration**:
- Each source has rate limiting to prevent abuse
- Sources configured with timeouts and error handling

#### Step 2.2: Website Discovery & Scraping (WebScraper)

**Sub-Step 2.2.1: Automatic Website Discovery**
- If URL not provided, system attempts to find company website automatically
- **Strategy 1**: Try common domain patterns
  - Generates candidate URLs: `www.{companyname}.com`, `{companyname}.com`, etc.
  - Tries country-specific domains (e.g., `.co.uk` for UK)
  - Validates URLs with HTTP HEAD/GET requests
  - Checks if company name appears in page content
  - **Success**: Returns URL if found
  - **Time**: ~1-2 seconds

- **Strategy 2**: Try name variations (if Strategy 1 fails)
  - Generates variations by removing suffixes (Inc, Ltd, Corp, plc, OAO, Group, etc.)
  - Handles parentheses (e.g., "BP (British Petroleum)" → "BP")
  - Handles special abbreviations (e.g., "Exxon Mobil" → "exxonmobil")
  - Tries domain patterns with variations
  - **Success**: Returns URL if found
  - **Time**: ~2-5 seconds

- **Strategy 3**: Tavily API Fallback (if Strategies 1 & 2 fail)
  - Searches Tavily API: `"{company_name} official website {country}"`
  - Gets top 5 search results
  - Validates each result until finding valid match
  - **Success**: Returns URL if found
  - **Time**: ~5-10 seconds (requires API key)
  - **Cost**: Uses API quota (only if needed)

**Sub-Step 2.2.2: Website Scraping**
- Once URL found (or provided), system scrapes the website:
  - Sends HTTP GET request with proper User-Agent header
  - Parses HTML using BeautifulSoup
  - Extracts text content (removes scripts, styles)
  - Extracts metadata: title, description
  - Extracts links (for navigation context)
  - Limits content to 5000 characters for processing
  - Extracts publication dates if available

**Output from WebScraper**:
- Website URL
- Website content (text, links)
- Publication date (if found)
- Metadata (title, description)
- Timestamp of collection

#### Step 2.3: Company Registry Lookup (CompanyRegistryFetcher)

**US Companies (SEC EDGAR)**:
- Searches SEC EDGAR company tickers database (10,142 companies)
- Loads pre-downloaded `company_tickers.json` file
- Searches by company name or ticker symbol
- Supports exact match and partial match
- Returns: Company name, ticker, CIK, SEC URL (if publicly traded)
- **Note**: Only covers publicly traded US companies

**UK Companies (Companies House)**:
- Placeholder: Not implemented (requires API key)
- Would query UK Companies House API
- Would return: Company number, registration date, status

**AU Companies (ASIC)**:
- Placeholder: Not implemented (requires API key)
- Would query Australian Securities and Investments Commission

**Output from CompanyRegistryFetcher**:
- Registry match status (found/not found)
- Company details (ticker, CIK, etc. if applicable)
- Source attribution

#### Step 2.4: Sanctions & Watchlist Check (SanctionsChecker)

**OFAC SDN List Check (US Sanctions)**:
- Loads pre-downloaded OFAC SDN Advanced XML file (17,711 entities)
- Parses XML using efficient iterparse method
- Searches entity names with partial matching
- Checks: Whole names, aliases, programs, dates of birth, places of birth
- Returns: Match status, match details, profile IDs, programs

**EU Consolidated Sanctions List Check**:
- Loads pre-downloaded EU sanctions XML file (5,579 entities)
- Parses XML using efficient iterparse method
- Searches entity names with partial matching
- Checks: Names, regulations, subject types, citizenships, birthdates
- Returns: Match status, match details, logical IDs, regulations

**UN Sanctions**:
- Placeholder: Not implemented (requires API integration)

**Output from SanctionsChecker**:
- Sanctions match status (True/False/Error)
- Match details (names, programs, regulations)
- Source attribution (OFAC, EU, UN)
- Risk level indication

#### Step 2.5: Data Aggregation
**Process**:
- `DataConnector` aggregates results from all sources
- Merges data from successful sources
- Tracks source attribution (which sources provided data)
- Handles failures gracefully (continues if one source fails)
- Calculates success rate (how many sources succeeded)

**Output**:
- Aggregated data dictionary
- List of sources used
- Success/failure status per source
- Timestamp of collection

---

### PHASE 3: DATA VALIDATION & STORAGE

#### Step 3.1: Data Validation
**Process**:
- Validates collected data using `DataValidator`
- Checks data quality:
  - Required fields present
  - Data format correct
  - Content not empty
  - Sanctions data format valid
  - Company registry data format valid

**Validation Rules**:
- Website content: Must have text if URL found
- Sanctions data: Must have match status
- Company registry: Must have match status
- Sources: Must have at least one successful source

#### Step 3.2: Data Storage (Initial Record)
**Process**:
- Creates initial `LOBVerification` record in SQLite database
- Stores:
  - Input data (client, country, role, product)
  - Collected data (sources, raw data)
  - Aggregated data (merged results)
  - Website URL (if found)
  - Publication date (if extracted)
  - Data collection timestamp
  - Data freshness score

**Database Fields Populated**:
- `client`, `client_country`, `client_role`, `product_name`
- `website_source`, `publication_date`
- `sources` (JSON: list of source names and data)
- `data_collected_at`, `data_freshness_score`
- `created_at`, `updated_at`

**AI Fields** (Not populated yet):
- `ai_response`: NULL (to be filled in Phase 4)
- `activity_level`: NULL (to be filled in Phase 4)
- `flags`: Empty (to be filled in Phase 4)
- `confidence_score`: NULL (to be filled in Phase 4)
- `is_red_flag`: False (to be updated in Phase 4)

**Returns**: Verification ID (used for later updates)

---

### PHASE 4: AI/ML ANALYSIS

#### Step 4.1: Prepare AI Input
**Process**:
- Retrieves stored verification record using verification ID
- Prepares input for AI analysis:
  - Company name, country, role, product
  - Collected data from all sources
  - Website content (if available)
  - Sanctions information (if matches found)

**Data Preparation**:
- Extracts evidence text from collected data
- Combines website content, company registry info, sanctions info
- Prepares context for LLM

#### Step 4.2: Text Processing & Feature Extraction
**Process**:
- `TextProcessor` processes evidence text:
  - Cleans text (removes noise, normalizes)
  - Extracts features (text quality, length, keywords)
  - Prepares text for LLM (limits to 4000 characters)
  - Extracts entities (company names, locations, activities)

**Features Extracted**:
- Text quality score
- Text length
- Keyword density
- Entity mentions

#### Step 4.3: LLM Analysis (Ollama - Local)
**Process**:
- `AIOrchestrator` coordinates AI analysis
- Calls Ollama LLM (llama3.2 model running locally)
- Generates main AI response about company legitimacy

**LLM Prompt Structure**:
- **System Prompt**: Defines role as compliance analyst
- **User Prompt**: 
  - Company information
  - Collected evidence
  - Website content
  - Sanctions information
  - Request for legitimacy assessment

**LLM Response Includes**:
- Legitimacy assessment
- Business activity description
- Compliance concerns (if any)
- Risk indicators

#### Step 4.4: Activity Level Classification
**Process**:
- `ActivityClassifier` classifies business activity level
- Uses LLM to determine: Active, Dormant, Inactive, Suspended, Unknown

**Classification Logic**:
- Analyzes evidence text for activity indicators
- Looks for keywords: "active", "operational", "dormant", "suspended"
- Uses LLM reasoning for final classification
- Returns: Activity level + confidence

**Activity Levels**:
- **Active**: Company is operational and conducting business
- **Dormant**: Company exists but not actively trading
- **Inactive**: Company has ceased operations
- **Suspended**: Company operations suspended
- **Unknown**: Insufficient data to determine

#### Step 4.5: Risk Assessment
**Process**:
- `RiskClassifier` assesses risk level
- Considers:
  - Sanctions matches (HIGH risk if found)
  - Company registry status
  - Activity level
  - Evidence quality
  - Compliance indicators

**Risk Calculation**:
- Base risk score: 0.3
- Sanctions match: +0.5 (if found)
- High-risk keywords: +0.1 per keyword
- Medium-risk keywords: +0.05 per keyword
- Flags count: +0.1 per flag

**Risk Levels**:
- **High**: Risk score >= 0.7
- **Medium**: Risk score >= 0.4
- **Low**: Risk score < 0.4

#### Step 4.6: Flag Generation
**Process**:
- `FlagGenerator` generates compliance flags
- Checks multiple categories:
  1. **Sanctions Match**: If entity in sanctions lists → HIGH severity flag
  2. **High Risk**: If risk score >= 0.7 → HIGH severity flag
  3. **Compliance Issues**: Unregistered company, suspicious patterns
  4. **Data Quality**: Limited evidence, unreliable sources
  5. **Source Reliability**: Few sources, inconsistent data

**Flag Categories**:
- `sanctions_match`: Entity found in sanctions lists
- `high_risk`: High risk score identified
- `compliance_issue`: Potential compliance problems
- `data_quality`: Low data quality concerns
- `source_reliability`: Limited or unreliable sources

**Flag Format**: `[SEVERITY] category: message`
- Examples:
  - `[HIGH] sanctions_match: Sanctioned according to OFAC sanctions list`
  - `[MEDIUM] data_quality: Limited evidence available`
  - `[LOW] source_reliability: Limited number of data sources`

#### Step 4.7: Confidence Score Calculation
**Process**:
- Calculates confidence in analysis results
- **Logic**:
  - Sanctions match = HIGH confidence (concrete evidence)
  - Red flags = HIGH confidence (clear risk indicators)
  - Multiple data sources = Higher confidence
  - Good text quality = Higher confidence
  - Limited evidence = LOW confidence

**Confidence Levels**:
- **High**: Strong evidence found (sanctions match or red flags)
- **Medium**: Moderate evidence (multiple sources, good quality)
- **Low**: Limited evidence (single source, poor quality)

#### Step 4.8: Red Flag Determination
**Process**:
- Determines if this is a "red flag" case requiring immediate attention
- **Criteria**:
  1. High risk score (>= 0.7) → Red flag
  2. 2+ high severity flags → Red flag
  3. Sanctions match → Red flag

**Red Flag Status**:
- **True**: Requires immediate review/action
- **False**: Normal processing, no immediate concerns

---

### PHASE 5: DATABASE UPDATE

#### Step 5.1: Update Verification Record
**Process**:
- Updates existing `LOBVerification` record with AI analysis results
- Populates fields:
  - `ai_response`: LLM-generated analysis text
  - `activity_level`: Classified activity level (Active/Dormant/etc.)
  - `flags`: List of compliance flags (JSON array)
  - `confidence_score`: Confidence level (High/Medium/Low)
  - `is_red_flag`: Red flag status (True/False)
  - `last_verified_at`: Timestamp of AI analysis

**Database Update**:
- SQL UPDATE query on `lob_verifications` table
- Commits transaction
- Refreshes record from database

---

### PHASE 6: RESPONSE FORMATTING & DELIVERY

#### Step 6.1: Format Output
**Process**:
- Retrieves updated verification record
- Formats response according to `LOBVerificationOutput` schema
- Includes all UC1 required outputs:
  1. **AI Response**: Text analysis
  2. **Website Source**: URL of company website
  3. **Publication Date**: Date information was published
  4. **Activity Level**: Active/Dormant/Inactive/etc.
  5. **Flags**: List of alerts/warnings
  6. **Sources**: List of data sources used
  7. **Confidence Score**: How confident in results
  8. **Red Flag**: Whether immediate attention needed

#### Step 6.2: Return Response
**Process**:
- Returns JSON response to user
- Includes:
  - Verification ID
  - All UC1 output fields
  - Metadata (timestamps, confidence)
  - Source citations

**Response Format**:
```json
{
  "id": 123,
  "client": "Company Name",
  "client_country": "US",
  "client_role": "Export",
  "product_name": "Product Description",
  "ai_response": "Analysis text...",
  "website_source": "https://www.company.com",
  "publication_date": "2024-01-01",
  "activity_level": "Active",
  "flags": ["[HIGH] sanctions_match: ..."],
  "sources": ["web_scraper", "company_registry", "sanctions_checker"],
  "is_red_flag": true,
  "confidence_score": "High",
  "data_collected_at": "2025-11-01T12:00:00",
  "data_freshness_score": "fresh",
  "last_verified_at": "2025-11-01T12:05:00",
  "created_at": "2025-11-01T12:00:00",
  "updated_at": "2025-11-01T12:05:00"
}
```

---

### PHASE 7: FRONTEND DISPLAY (if using web UI)

#### Step 7.1: Receive Response
**Process**:
- Frontend receives JSON response from API
- React Query handles response
- Updates UI state

#### Step 7.2: Display Results
**Process**:
- **Form**: Shows input values (company, country, role, product)
- **Loading State**: Shows spinner while processing
- **Results Display**:
  - **Activity Indicator**: Shows activity level (Active/Dormant/etc.) with color coding
  - **Flags Display**: Shows all flags with severity indicators (red/yellow/green)
  - **AI Response**: Shows LLM-generated analysis text
  - **Source Citations**: Lists all data sources used
  - **Timeline**: Shows data collection → AI analysis timeline
  - **Red Flag Alert**: Prominent display if `is_red_flag = true`

**UI Components**:
- `VerificationForm`: Input form
- `VerificationResults`: Results display
- `ActivityIndicator`: Activity level display
- `FlagDisplay`: Flags/alerts display
- `AIResponse`: AI analysis text
- `SourceCitation`: Source attribution
- `Timeline`: Process timeline
- `ConnectionStatus`: Backend connection status

---

## Complete Flow Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: USER INPUT                          │
├─────────────────────────────────────────────────────────────────┤
│  1. User enters: Company Name, Country, Role, Product          │
│  2. Frontend sends POST /api/v1/lob/verify                    │
│  3. API validates input (Pydantic schema)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 2: DATA COLLECTION                         │
├─────────────────────────────────────────────────────────────────┤
│  2.1 Initialize DataConnector                                   │
│  2.2 WebScraper:                                                 │
│      ├─ Auto-discover website (3 strategies)                    │
│      ├─ Scrape website content                                  │
│      └─ Extract publication dates                               │
│  2.3 CompanyRegistryFetcher:                                    │
│      ├─ Search SEC EDGAR (US)                                   │
│      ├─ Search Companies House (UK) - placeholder              │
│      └─ Search ASIC (AU) - placeholder                         │
│  2.4 SanctionsChecker:                                          │
│      ├─ Check OFAC SDN List (17,711 entities)                  │
│      ├─ Check EU Sanctions (5,579 entities)                     │
│      └─ Check UN Sanctions - placeholder                        │
│  2.5 Aggregate results from all sources                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 3: DATA VALIDATION & STORAGE                 │
├─────────────────────────────────────────────────────────────────┤
│  3.1 Validate collected data                                   │
│  3.2 Store initial record in database                           │
│      ├─ Store input data                                        │
│      ├─ Store collected data                                    │
│      ├─ Store sources                                           │
│      └─ Store timestamps                                         │
│      Returns: Verification ID                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 4: AI/ML ANALYSIS                       │
├─────────────────────────────────────────────────────────────────┤
│  4.1 Prepare AI input (evidence text)                         │
│  4.2 Text processing & feature extraction                       │
│  4.3 LLM Analysis (Ollama llama3.2):                            │
│      └─ Generate legitimacy assessment                          │
│  4.4 Activity Level Classification:                             │
│      └─ Classify: Active/Dormant/Inactive/Suspended/Unknown    │
│  4.5 Risk Assessment:                                            │
│      └─ Calculate risk score & level (High/Medium/Low)         │
│  4.6 Flag Generation:                                            │
│      └─ Generate compliance flags (sanctions, risk, data quality)│
│  4.7 Confidence Score Calculation:                              │
│      └─ Calculate confidence (High/Medium/Low)                 │
│  4.8 Red Flag Determination:                                      │
│      └─ Determine if red flag (True/False)                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 5: DATABASE UPDATE                       │
├─────────────────────────────────────────────────────────────────┤
│  5.1 Update verification record with AI results               │
│      ├─ ai_response                                             │
│      ├─ activity_level                                          │
│      ├─ flags                                                    │
│      ├─ confidence_score                                         │
│      ├─ is_red_flag                                              │
│      └─ last_verified_at                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 6: RESPONSE FORMATTING                        │
├─────────────────────────────────────────────────────────────────┤
│  6.1 Format output (LOBVerificationOutput schema)             │
│  6.2 Return JSON response with all UC1 outputs                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 7: FRONTEND DISPLAY (optional)                │
├─────────────────────────────────────────────────────────────────┤
│  7.1 Frontend receives response                                 │
│  7.2 Display results in UI:                                       │
│      ├─ Activity indicator                                      │
│      ├─ Flags display                                           │
│      ├─ AI response                                              │
│      ├─ Source citations                                         │
│      └─ Red flag alerts                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components & Their Roles

### 1. Data Collection Layer
- **WebScraper**: Finds and scrapes company websites
- **CompanyRegistryFetcher**: Checks official company registries
- **SanctionsChecker**: Checks sanctions/watchlists
- **DataConnector**: Orchestrates all data sources

### 2. AI/ML Layer
- **AIOrchestrator**: Coordinates all AI analysis
- **TextProcessor**: Processes text, extracts features
- **LLMClient**: Interfaces with Ollama (local LLM)
- **ActivityClassifier**: Classifies activity levels
- **RiskClassifier**: Assesses risk
- **FlagGenerator**: Generates compliance flags

### 3. Service Layer
- **AIService**: Integrates AI analysis with database
- **DataStorage**: Handles database operations

### 4. API Layer
- **FastAPI Routes**: REST API endpoints
- **Pydantic Schemas**: Input/output validation

### 5. Frontend Layer
- **React Components**: UI for user interaction
- **API Client**: Communicates with backend

---

## Data Flow

### Input Data Flow
```
User Input
    ↓
API Endpoint (/api/v1/lob/verify)
    ↓
Input Validation (Pydantic)
    ↓
DataConnector
    ↓
[WebScraper, CompanyRegistryFetcher, SanctionsChecker]
    ↓
Data Aggregation
    ↓
DataStorage (Initial Record)
    ↓
AIService
    ↓
AIOrchestrator
    ↓
[TextProcessor, LLMClient, ActivityClassifier, RiskClassifier, FlagGenerator]
    ↓
Database Update
    ↓
Response Formatting
    ↓
JSON Response
    ↓
Frontend Display (optional)
```

### Data Sources Flow
```
Company Name + Country
    ↓
┌─────────────────────────────────────────┐
│  WebScraper                              │
│  1. Auto-discover website (3 strategies) │
│  2. Scrape content                       │
│  3. Extract dates                        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  CompanyRegistryFetcher                 │
│  1. Search SEC EDGAR (US companies)     │
│  2. Search Companies House (UK) - TODO │
│  3. Search ASIC (AU) - TODO              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  SanctionsChecker                       │
│  1. Check OFAC SDN List (17,711)        │
│  2. Check EU Sanctions (5,579)          │
│  3. Check UN Sanctions - TODO           │
└─────────────────────────────────────────┘
    ↓
Aggregated Results
```

### AI Analysis Flow
```
Collected Data
    ↓
Text Extraction & Feature Extraction
    ↓
LLM Analysis (Ollama)
    ├─ Main Response Generation
    ├─ Activity Classification
    └─ Risk Assessment
    ↓
Flag Generation
    ↓
Confidence Calculation
    ↓
Red Flag Determination
    ↓
AI Results (All UC1 Outputs)
```

---

## Timing & Performance

### Typical Processing Times
- **Data Collection**: 5-15 seconds
  - Website discovery: 1-10 seconds (depending on strategy)
  - Website scraping: 2-5 seconds
  - Company registry: 1-2 seconds
  - Sanctions check: 1-3 seconds

- **AI Analysis**: 5-20 seconds
  - Text processing: <1 second
  - LLM calls: 3-15 seconds (depends on Ollama performance)
  - Classification: 2-5 seconds

- **Total**: 10-35 seconds per verification

### Optimization
- **Caching**: URLs can be cached (not implemented)
- **Parallel Processing**: Data sources can run in parallel (partially implemented)
- **Async**: API endpoints are async (implemented)

---

## Error Handling

### Data Collection Failures
- **Website Not Found**: System continues, sets `website_source = NULL`
- **Registry Not Found**: System continues, marks as "not found"
- **Sanctions Check Error**: System continues, marks as "error" in sources
- **Partial Failures**: System aggregates successful sources, continues

### AI Analysis Failures
- **LLM Error**: Returns partial results (data collected, no AI analysis)
- **Classification Error**: Sets `activity_level = "Unknown"`
- **Flag Generation Error**: Returns empty flags list

### Database Failures
- **Connection Error**: Returns HTTP 500 error
- **Transaction Error**: Rolls back, returns error

**All errors are logged** for debugging and monitoring.

---

## Source Attribution

Every result includes source attribution:
- **WebScraper**: Lists website URL
- **CompanyRegistryFetcher**: Lists registry source (SEC EDGAR, etc.)
- **SanctionsChecker**: Lists sanctions sources checked (OFAC, EU, etc.)

**Output Format**:
```json
{
  "sources": [
    "web_scraper",
    "company_registry",
    "sanctions_checker"
  ]
}
```

---

## UC1 Output Fields (Required)

All outputs required by UC1 specification:

1. **AI Response**: Text analysis of company legitimacy
2. **Website Source**: URL of company website (if found)
3. **Publication Date**: Date information was published (if extracted)
4. **Activity Level**: Active/Dormant/Inactive/Suspended/Unknown
5. **Flags**: List of alerts/warnings (compliance, risk, data quality)
6. **Sources**: List of data sources used
7. **Confidence Score**: High/Medium/Low
8. **Red Flag**: True/False (immediate attention needed)

---

## Summary

This POC workflow demonstrates:
- **Automated Data Collection** from multiple public sources
- **Intelligent Website Discovery** with fallback strategies
- **Real Sanctions Checking** against OFAC and EU lists
- **AI-Powered Analysis** using local LLM (Ollama)
- **Risk Assessment** with flag generation
- **Explainable Results** with source attribution
- **Complete UC1 Implementation** with all required outputs

**Status**: ✅ **Functional POC - Ready for Demonstration**

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-01

