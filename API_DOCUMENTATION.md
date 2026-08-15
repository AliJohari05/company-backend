# Agency & Automation Platform API — Frontend Integration Guide

**API Version:** 1.0.0  
**OpenAPI Specification:** 3.0.3  
**Swagger UI:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)  
**ReDoc:** [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)  
**OpenAPI Schema:** [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)  

---

## 1. API Base URL Configuration

The API host is environment-dependent. Do not hard-code the Base URL in the frontend codebase. Use environment variables (e.g., Vite/React).

- **Development:** `http://localhost:8000/api/v1/`
- **Production:** `https://api.yourdomain.com/api/v1/`

Example configuration for Vite (`.env.local`):
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1

```

All documented endpoints in this guide include the `/api/v1/` prefix.

---

## 2. Interactive Documentation & Source of Truth

The live OpenAPI/Swagger documentation is the single source of truth for endpoint paths, request/response schemas, authentication parameters, and enum values.

**Frontend Quick Start Flow:**

1. Start the backend server.
2. Open Swagger UI (`/api/docs/`).
3. Authenticate using JWT if required.
4. Test endpoints with "Try it out".
5. Implement the verified schema in the frontend app.

---

## 3. Authentication & Authorization

The API uses **JWT (JSON Web Token)** Bearer Authentication.

* **Header Format:** `Authorization: Bearer <access_token>`
* **Security Scheme:** `Bearer` / `JWT`

### Token Flow

1. Send credentials to `/accounts/login/` to receive `access` and `refresh` tokens.
2. Store tokens securely on the client side.
3. Attach the `access` token to all protected API requests.
4. When the `access` token expires (`401 Unauthorized`), send the `refresh` token to `/accounts/refresh/` to obtain a new access token.

---

## 4. Response Structure, Pagination & Currency

### Paginated Responses (List Endpoints)

Endpoints that return lists (Blog Posts, Invoices, Projects, etc.) follow Django REST Framework's standard paginated format:

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/blog/posts/?page=2",
  "previous": null,
  "results": [ ... ]
}

```

*Note: Frontend clients can pass `?page=X` or `?page_size=Y` in query parameters where supported.*

### Currency & Financial Values

All monetary fields (`amount`, `unit_price`, `total_price`, `estimated_budget`) are returned as **raw numerical values in IRR (Rials)**. Formatting (such as adding thousand separators or converting/displaying "تومان") must be performed on the UI/Frontend layer.

### Common HTTP Status Codes

* `200 OK`: Request succeeded.
* `201 Created`: Resource successfully created.
* `204 No Content`: Request succeeded with no response body.
* `400 Bad Request`: Validation error in payload.
* `401 Unauthorized`: Missing or expired JWT token.
* `403 Forbidden`: Insufficient permissions.
* `404 Not Found`: Resource does not exist.

---

## 5. Complete Endpoint Reference

### 5.1 Accounts & Authentication

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/accounts/register/` | Public | Register a new user account |
| `POST` | `/accounts/login/` | Public | Authenticate and obtain JWT token pair |
| `POST` | `/accounts/refresh/` | Public | Obtain a new access token using refresh token |
| `POST` | `/accounts/logout/` | JWT | Logout and blacklist refresh token |
| `GET` | `/accounts/profile/` | JWT | Get current user's profile |
| `PUT` | `/accounts/profile/` | JWT | Update user profile |
| `PATCH` | `/accounts/profile/` | JWT | Partially update user profile |
| `POST` | `/accounts/change-password/` | JWT | Change authenticated user password |

### 5.2 Services

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/services/` | Public | List all active services |
| `GET` | `/services/{slug}/` | Public | Get service details and pricing plans |
| `GET` | `/services/categories/` | Public | List active service categories |

### 5.3 Projects

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/projects/` | JWT | List user's project requests |
| `POST` | `/projects/` | JWT | Create a new project request |
| `GET` | `/projects/{id}/` | JWT | Get project request details |
| `POST` | `/projects/{project_id}/attachments/` | JWT | Upload attachment for a project request |

### 5.4 Tickets & Support

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/tickets/` | JWT | List user's support tickets |
| `POST` | `/tickets/` | JWT | Create a new ticket with initial message |
| `GET` | `/tickets/{id}/` | JWT | Get ticket details and full message history |
| `POST` | `/tickets/{id}/status/` | JWT | Toggle ticket status (Close / Reopen) |
| `POST` | `/tickets/{ticket_id}/messages/` | JWT | Add a reply message to an existing ticket |

### 5.5 Billing & Financials

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/billing/contracts/` | JWT | List contracts (Admin sees all, Client sees own) |
| `POST` | `/billing/contracts/` | Admin | Create a new contract |
| `GET` | `/billing/contracts/{id}/` | JWT | Get contract details |
| `PUT/PATCH/DELETE` | `/billing/contracts/{id}/` | Admin | Update or delete contract |
| `GET` | `/billing/invoices/` | JWT | List invoices (Admin sees all, Client sees own) |
| `POST` | `/billing/invoices/` | Admin | Create a new invoice |
| `GET` | `/billing/invoices/{id}/` | JWT | Get invoice details and line items |
| `PUT/PATCH/DELETE` | `/billing/invoices/{id}/` | Admin | Update or delete invoice |
| `GET/POST` | `/billing/invoice-items/` | Admin | List or create individual invoice items |
| `GET/PUT/PATCH/DELETE` | `/billing/invoice-items/{id}/` | Admin | Manage specific invoice item |
| `GET` | `/billing/transactions/` | JWT | List transactions / payment receipts |
| `POST` | `/billing/transactions/` | JWT | Upload payment receipt for an invoice |
| `GET/PUT/PATCH/DELETE` | `/billing/transactions/{id}/` | JWT/Admin | Manage specific payment transaction |

### 5.6 Blog

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/blog/categories/` | Public | List blog categories |
| `POST/PUT/PATCH/DELETE` | `/blog/categories/{id}/` | Admin | Category management |
| `GET` | `/blog/posts/` | Public | List published blog posts |
| `GET` | `/blog/posts/{slug}/` | Public | Get post details (increments view count) |
| `PUT/PATCH/DELETE` | `/blog/posts/{slug}/` | Admin | Post management |
| `GET` | `/blog/tags/` | Public | List blog tags |
| `POST/PUT/PATCH/DELETE` | `/blog/tags/{id}/` | Admin | Tag management |

### 5.7 Portfolio

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/portfolio/categories/` | Public | List portfolio categories |
| `GET` | `/portfolio/items/` | Public | List portfolio items (supports filtering) |
| `GET` | `/portfolio/items/{slug}/` | Public | Get portfolio project details |

### 5.8 Core / Site Content

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/core/faqs/` | Public | List active Frequently Asked Questions |
| `GET` | `/core/settings/` | Public | Get site settings, contact info, working hours |
| `GET` | `/core/social-links/` | Public | List active social media links |

---

## 6. Enum Reference

Enum values are case-sensitive and must be sent/handled exactly as defined below:

| Enum Category | Allowed Values | Description |
| --- | --- | --- |
| **User Role** | `ADMIN`, `STAFF`, `CLIENT` | User permission access level |
| **Project Status** | `PENDING`, `APPROVED`, `IN_PROGRESS`, `COMPLETED`, `REJECTED` | Project request status |
| **Ticket Priority** | `LOW`, `MEDIUM`, `HIGH` | Support ticket priority level |
| **Ticket Status** | `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED` | Support ticket resolution state |
| **Invoice Status** | `UNPAID`, `PAID`, `OVERDUE`, `CANCELED` | Billing invoice state |
| **Transaction Status** | `PENDING`, `APPROVED`, `REJECTED` | Payment verification status |

---

## 7. Main Data Models & Schemas

### UserProfile

```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+989123456789",
  "company_name": "Example Corp",
  "role": "CLIENT",
  "created_at": "2026-08-12T10:00:00Z"
}

```

### Invoice & InvoiceItem

```json
{
  "id": 10,
  "invoice_number": "INV-2026-001",
  "user": 1,
  "user_email": "user@example.com",
  "total_amount": 250000000,
  "status": "UNPAID",
  "status_display": "Unpaid",
  "due_date": "2026-09-01",
  "items": [
    {
      "id": 1,
      "description": "Frontend Development - Phase 1",
      "quantity": 1,
      "unit_price": 250000000,
      "total_price": 250000000
    }
  ],
  "transactions": []
}

```

---

## 8. File Upload Handling (Multipart Requests)

When sending files (e.g., transaction payment receipts or project attachments), use `FormData`.

> **Important:** Do NOT manually set the `Content-Type` header when using `FormData`. The browser will automatically manage and attach the correct boundary string.

Example (Transaction Receipt Upload):

```javascript
const formData = new FormData();
formData.append("invoice", invoiceId);
formData.append("amount", amount);
formData.append("reference_code", referenceCode);
formData.append("receipt_attachment", fileInput.files[0]);

const response = await fetch(`${API_BASE_URL}/billing/transactions/`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`
    // Do NOT include Content-Type header here
  },
  body: formData
});

```

---

## 9. Recommended Frontend Integration Example

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Helper function for authenticated JSON requests
async function fetchAPI(endpoint, options = {}) {
  const token = localStorage.getItem("accessToken");
  
  const headers = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    // Handle Token Refresh or Redirect to Login
  }

  return response.json();
}

```
