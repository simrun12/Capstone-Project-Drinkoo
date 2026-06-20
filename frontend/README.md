## DRINKOO Frontend

Simple HTML/CSS/JavaScript frontend for the DRINKOO beverage management platform.

### Features

- **Login Page** - Default credentials: `admin` / `password`
- **Dashboard** - High-level metrics and overview
- **State Data** - State-wise customer and SKU distribution
- **SKU Management** - View and create new SKUs
- **Shipment Management** - Create shipments and track with unique tracking codes
- **Chat** - Ask questions about DRINKOO company data
- **Reports** - Sales by state and top-performing SKUs

### File Structure

```
frontend/
├── index.html           # Login page
├── dashboard.html       # Main dashboard interface
├── styles/
│   └── main.css        # All styling
└── js/
    ├── auth.js         # Authentication and token handling
    ├── api.js          # API client utilities
    └── main.js         # Dashboard logic
```

### How to Run

#### Option 1: Using Python HTTP Server

From the project root:

```bash
python run_frontend.py
```

Or manually:

```bash
python -m http.server 3000 --directory frontend
```

Then visit: **http://localhost:3000**

#### Option 2: Using Node.js

If you have Node.js installed:

```bash
npx http-server frontend -p 3000
```

### Prerequisites

- **Backend API running** at `http://localhost:8000`
- **Modern browser** (Chrome, Firefox, Safari, Edge)
- **JavaScript enabled**

To start the backend API:

```bash
uvicorn backend.main:app --reload
```

### Login Instructions

1. Navigate to http://localhost:3000
2. Username: `admin`
3. Password: `password`
4. Click "Sign In"

### Using the Dashboard

#### Dashboard Tab
- View overall DRINKOO metrics
- Total customers, SKUs, shipments, and revenue

#### State Data Tab
- Select a state from the dropdown
- View state-specific metrics
- See available SKUs and their distribution

#### SKU Management Tab
- View all active SKUs in a table
- Add new SKUs using the form
- Only valid sizes: 1000ml or 1500ml

#### Shipments Tab
- Create new shipments (requires state, SKU, and quantity)
- Automatic tracking code generation
- Track shipments using their tracking code
- View shipment status (pending, in_transit, delivered, failed)

#### Chat Tab
- Ask questions about DRINKOO data
- Query examples:
  - "How many customers in Maharashtra?"
  - "Which SKU is performing best?"
  - "How many pending shipments?"
  - "List states covered by DRINKOO"

#### Reports Tab
- View sales by state
- View top-performing SKUs

### API Integration

The frontend communicates with the backend API at:
- **Base URL**: `http://localhost:8000/api/v1`

All requests require an `Authorization: Bearer <token>` header.

### Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Notes

- This is a **development demo** interface
- Default credentials are hardcoded for dev/test use only
- No persistent session - refresh page requires re-login
- All data is demo/dummy data from the SQLite database

### Troubleshooting

**"Cannot reach API" error?**
- Ensure backend is running: `uvicorn backend.main:app --reload`
- Check backend is at `http://localhost:8000`

**"Login failed" error?**
- Verify default credentials: admin / password
- Check browser console for detailed error

**"No states/SKUs showing"?**
- Ensure database is seeded: `python backend/scripts/seed_database.py`
- Restart frontend page

---

For more details, see [../plan.md](../plan.md)
