# DRINKOO SKU Management System - Project Plan

## Project Overview
A comprehensive drink freight and inventory management platform for DRINKOO, a beverage company. The system tracks SKU distribution, customer data, and shipments across Indian states with real-time ETL capabilities.

---

## Core Requirements

### 1. Data Foundation

#### 1.1 Customer Data (1,000 Dummy Customers)
- **Geographic Coverage**: All 28 states + 8 union territories in India
- **Distribution Logic**: Customer count per region based on state population (statistically relevant)
- **Data Fields**:
  - Customer ID (unique identifier)
  - Customer Name
  - State (all 36 regions covered)
  - City/Capital
  - Region/District
  - Customer Contact Information
  - Registration Date
  - Customer Tier/Segment

#### 1.2 SKU Management (50 Total SKUs)

**Phase 1 - Soda Flavors (10 SKUs)**:
- Flavor Profile (e.g., Cola, Orange, Lemon, Mango, etc.)
- Size/Volume Options (1L, 1.5L, 2L)
- Manufacturing Cost
- Shipping Cost per Unit
- Price Point
- Status (Active/Inactive)

**Phase 2 - Additional SKUs (40)**:
- Other beverage categories (Juices, Energy Drinks, Water, Iced Tea, etc.)
- Same metadata structure as Phase 1

#### 1.3 SKU Distribution Logic
- **Per State Distribution**: Based on state customer density
- **Statistical Relevance**: 
  - High-population states → more diverse SKU distribution
  - Low-population states → focused SKU distribution (best sellers)
  - Ensure each state has minimum viable SKU variety
- **Distribution Table**: Maps states to their allocated SKUs with quantity weights

---

### 2. Backend - FastAPI

#### 2.1 Architecture
- **Framework**: FastAPI (Python)
- **Database**: SQLite
- **Real-time ETL**: Background tasks for near-real-time processing
- **Performance Optimization**:
  - Database indexing on frequently queried columns (state, SKU, timestamp)
  - Query optimization for aggregations
  - Caching layer for read-heavy operations
  - Connection pooling

#### 2.2 API Routes Structure

**Authentication Routes**:
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Token verification

**SKU Routes**:
- `GET /api/skus/` - List all SKUs
- `GET /api/skus/{sku_id}` - Get SKU details
- `POST /api/skus/` - Create new SKU (with authorization)
- `PUT /api/skus/{sku_id}` - Update SKU (with authorization)
- `GET /api/skus/by-state/{state}` - Get SKUs available in a state

**State & Distribution Routes**:
- `GET /api/states/` - List all states
- `GET /api/states/{state_name}/data` - Get state-wise sales data
- `GET /api/states/{state_name}/customers` - Get customers in state
- `GET /api/states/{state_name}/sku-distribution` - Get SKU availability in state

**Shipment & Tracking Routes**:
- `POST /api/shipments/` - Create new shipment
- `GET /api/shipments/` - List shipments
- `GET /api/shipments/{tracking_code}` - Track shipment status
- `PUT /api/shipments/{tracking_code}/status` - Update shipment status
- `GET /api/shipments/by-state/{state}` - Get shipments for state

**Sales & Analytics Routes**:
- `GET /api/analytics/sales-by-state` - Sales data aggregated by state
- `GET /api/analytics/top-skus` - Top performing SKUs
- `GET /api/analytics/sales-by-sku/{sku_id}` - Sales performance per SKU
- `GET /api/analytics/dashboard` - Overall metrics for dashboard

**File Upload Routes**:
- `POST /api/upload/sku-images/` - Upload SKU images
- `GET /api/upload/sku-images/{sku_id}` - Retrieve SKU images

**RAG Chatbot Routes**:
- `POST /api/chatbot/ask` - Query chatbot
- `GET /api/chatbot/context` - Get available knowledge base context

#### 2.3 Configuration Management
- Environment variables for database path, API keys
- Config file structure for easy deployment
- Support for different environments (dev, test, prod)

#### 2.4 Error Handling & Logging
- Centralized error handling
- Request/response logging
- Performance metrics logging

---

### 3. Database Design - SQLite

#### 3.1 Required Tables (Minimum 6+)

**1. users**
```
- user_id (PRIMARY KEY)
- username
- password_hash
- email
- role (admin, vendor, analyst)
- created_at
- updated_at
- is_active
```

**2. customers**
```
- customer_id (PRIMARY KEY)
- customer_name
- state
- city
- district
- contact_email
- contact_phone
- registration_date
- customer_tier
- created_at
```

**3. skus**
```
- sku_id (PRIMARY KEY)
- sku_code (unique)
- flavor_profile
- volume_size
- manufacturing_cost
- shipping_cost
- retail_price
- category
- status
- created_at
- updated_at
```

**4. sku_distribution**
```
- distribution_id (PRIMARY KEY)
- state
- sku_id (FOREIGN KEY)
- quantity_allocated
- distribution_percentage
- created_at
- updated_at
```

**5. shipments**
```
- shipment_id (PRIMARY KEY)
- tracking_code (unique)
- sku_id (FOREIGN KEY)
- state
- quantity
- shipment_date
- expected_delivery_date
- actual_delivery_date
- status (pending, in_transit, delivered, failed)
- manufacturer_cost
- shipping_cost
- created_at
- updated_at
```

**6. sales**
```
- sales_id (PRIMARY KEY)
- sku_id (FOREIGN KEY)
- state
- customer_id (FOREIGN KEY)
- quantity_sold
- sale_date
- revenue
- created_at
```

**7. sku_images**
```
- image_id (PRIMARY KEY)
- sku_id (FOREIGN KEY)
- image_path
- uploaded_by
- uploaded_at
```

#### 3.2 Database Optimization
- Indexes on: state, sku_id, tracking_code, created_at
- Foreign key constraints enabled
- Transaction support for data integrity

---

### 4. Frontend - HTML/CSS/JS

#### 4.1 Authentication Module
- Login page with username/password (Default: admin/password)
- Session management with JWT/session tokens
- Logout functionality
- Authorization checks on all protected pages

#### 4.2 Dashboard
- Overview metrics:
  - Total customers
  - Total SKUs active
  - Pending shipments
  - Revenue metrics
- State selector dropdown (all 36 regions)
- Date range filters

#### 4.3 State-Wide Data View
- Dropdown to select state
- Display metrics:
  - Number of customers in state
  - Available SKUs
  - Recent sales
  - Pending shipments
  - Top-selling SKUs in state

#### 4.4 SKU Management
- View all SKUs table
- Add New SKU form:
  - Flavor Profile
  - Volume Size
  - Manufacturing Cost
  - Shipping Cost per Unit
  - Retail Price
  - Upload product image
  - Quantity allocation per state
- Edit existing SKUs
- Soft delete SKUs (status update)

#### 4.5 Shipment Management
- Create new shipment:
  - Select SKU
  - Select destination state
  - Quantity
  - Expected delivery date
  - Auto-generated tracking code
- Track shipment:
  - Search by tracking code
  - Real-time status updates (Pending → In Transit → Delivered)
  - Timeline view

#### 4.6 Tracking System
- Pre-embedded tracking codes for each shipment
- Public tracking view (no login required)
- Shipment status history
- Visual status indicators

#### 4.7 Chat Interface
- RAG Chatbot integration
- Query box for asking questions about:
  - Sales data
  - SKU performance
  - Customer insights
  - Shipment status
- Chat history display

#### 4.8 File Upload Section
- SKU image upload
- Bulk customer data upload (CSV)
- Supported formats: JPG, PNG, CSV
- Upload status and validation messages

#### 4.9 Reports View
- Sales reports by state
- SKU performance reports
- Shipment reports
- Export to CSV functionality

---

### 5. RAG Chatbot

#### 5.1 Knowledge Base
- Indexed company dataset:
  - Customer data (anonymized)
  - SKU information
  - Historical sales data
  - State-wise metrics
- Real-time query updates

#### 5.2 Chatbot Capabilities
- Answer questions about:
  - "Which SKU performs best in Maharashtra?"
  - "How many customers are in Delhi?"
  - "What is the total revenue from soda flavors?"
  - "Which states have pending shipments?"
- Fallback responses for out-of-scope questions

#### 5.3 Implementation
- Integration with FastAPI backend
- Vector embeddings for semantic search
- Context grounding in company data

---

### 6. Security & Authorization

#### 6.1 Authentication
- JWT or session-based authentication
- Password hashing (bcrypt/argon2)
- Session timeout handling

#### 6.2 Authorization
- Role-based access control (RBAC):
  - **Admin**: Full system access
  - **Vendor**: View sales, track shipments, view reports (read-only mostly)
  - **Analyst**: View analytics, run reports (read-only)
- Route-level authorization checks
- Environment-based rules:
  - Dev/Test: Standard security
  - Prod/Production branches: Enhanced security, no hardcoded credentials

#### 6.3 Data Protection
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS protection on frontend
- CORS configuration

---

### 7. File Structure

```
drinkoo/
├── backend/
│   ├── config.py              # Configuration management
│   ├── requirements.txt        # Python dependencies
│   ├── main.py               # FastAPI application entry
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication routes
│   │   ├── skus.py           # SKU management routes
│   │   ├── states.py         # State and distribution routes
│   │   ├── shipments.py      # Shipment tracking routes
│   │   ├── analytics.py      # Analytics routes
│   │   ├── upload.py         # File upload routes
│   │   └── chatbot.py        # RAG chatbot routes
│   ├── database/
│   │   ├── db.py             # Database connection & setup
│   │   ├── schema.py         # SQLite schema definitions
│   │   └── models.py         # SQLAlchemy ORM models (if used)
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chatbot.py        # RAG chatbot logic
│   │   └── knowledge_base.py # Knowledge base management
│   ├── utils/
│   │   ├── auth.py           # Authentication utilities
│   │   ├── validators.py     # Data validation
│   │   └── helpers.py        # Helper functions
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_skus.py
│   │   ├── test_shipments.py
│   │   └── test_api.py
│   └── uploads/
│       └── sku_images/       # SKU image storage
├── frontend/
│   ├── index.html            # Login page
│   ├── dashboard.html        # Main dashboard
│   ├── sku-management.html   # SKU CRUD interface
│   ├── shipments.html        # Shipment tracking
│   ├── state-data.html       # State-wise data view
│   ├── chat.html             # Chatbot interface
│   ├── reports.html          # Reports view
│   ├── styles/
│   │   └── main.css          # Main stylesheet
│   └── js/
│       ├── main.js           # Main application logic
│       ├── auth.js           # Authentication handling
│       ├── api.js            # API client
│       └── charts.js         # Chart/visualization library
├── reports/                  # Generated reports storage
├── uploads/
│   └── sku_images/          # SKU images
├── data/                    # Dummy data generation scripts
│   ├── generate_customers.py
│   ├── generate_skus.py
│   └── generate_shipments.py
├── drinkoo.db              # SQLite database
└── README.md               # Project documentation
```

---

### 8. Implementation Phases

#### Phase 1: Foundation (Week 1-2)
- Database schema creation
- Dummy data generation (1,000 customers, 50 SKUs, distributions)
- Basic FastAPI setup with configuration
- Login/authentication routes

#### Phase 2: Core Features (Week 2-3)
- SKU management API routes
- State and distribution routes
- Basic frontend (login, dashboard, state selector)
- File upload functionality

#### Phase 3: Tracking & Shipping (Week 3-4)
- Shipment creation and tracking
- Tracking code generation
- Shipment status updates
- Real-time ETL for sales data

#### Phase 4: Advanced Features (Week 4-5)
- RAG chatbot integration
- Analytics and reporting
- Reports generation and export
- Performance optimization

#### Phase 5: Testing & Deployment (Week 5-6)
- Comprehensive test suite
- Security audit
- Production environment setup
- Documentation completion

---

### 9. Key Constraints & Rules

1. **Guardrails** (From project setup):
   - No file deletion without permission
   - No DML execution without permission
   - Second opinion for DELETE, ALTER, UPDATE on tables
   - SQLite-only for all database operations
   - Clear variable names for junior engineers
   - Complete documentation for non-technical users
   - No internet access for file editing (research only)

2. **Business Logic**:
   - SKU sizes: Only valid values like 1L, 1.5L, 2L (no arbitrary decimals like 1.25)
   - State distribution must be statistically relevant
   - Every state must have customer representation

3. **Environment**:
   - Dev/Test: Standard security with hardcoded admin/password
   - Prod/Production: Enhanced security, credential management

4. **Performance**:
   - Real-time ETL capabilities
   - Fast API response times
   - Optimized database queries

---

### 10. Success Criteria

- ✓ 1,000 dummy customers distributed across all Indian states
- ✓ 50 SKUs with statistically relevant distribution
- ✓ Fast API with <200ms response time for common queries
- ✓ Complete frontend with login, state selector, SKU management, tracking
- ✓ Shipment tracking system with pre-generated codes
- ✓ RAG chatbot answering company data questions
- ✓ Comprehensive test suite (>80% coverage)
- ✓ Production-ready code with security best practices
- ✓ Complete documentation for all users

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1 implementation (database & dummy data)
3. Iteratively develop through phases with regular checkpoints
4. Testing and optimization at each phase
5. Final deployment and documentation

---

**Last Updated**: June 15, 2026
**Project Name**: DRINKOO SKU Management System
**Status**: Planning
