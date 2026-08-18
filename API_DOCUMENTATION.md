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

1. Register using `/accounts/register/`. The account remains inactive until
   its email address is verified.
2. Open the email verification link. The frontend sends its `uid` and `token`
   to `/accounts/verify-email/`.
3. Send verified credentials to `/accounts/login/` to receive `access` and
   `refresh` tokens.
4. Store tokens securely on the client side.
5. Attach the `access` token to all protected API requests.
6. When the access token expires (`401 Unauthorized`), send the refresh token
   to `/accounts/refresh/` to obtain a new access token.

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
| `POST` | `/accounts/register/` | Public | Register an inactive account and send its verification email |
| `POST` | `/accounts/verify-email/` | Public | Verify the signed email token and activate the account |
| `POST` | `/accounts/resend-verification/` | Public | Resend verification without revealing whether an account exists |
| `POST` | `/accounts/login/` | Public | Authenticate and obtain JWT token pair |
| `POST` | `/accounts/refresh/` | Public | Obtain a new access token using refresh token |
| `POST` | `/accounts/logout/` | JWT | Logout and blacklist refresh token |
| `GET` | `/accounts/profile/` | JWT | Get current user's profile |
| `PUT` | `/accounts/profile/` | JWT | Update user profile |
| `PATCH` | `/accounts/profile/` | JWT | Partially update user profile |
| `POST` | `/accounts/change-password/` | JWT | Change authenticated user password |

Email verification rules:

- Registration does not return JWT tokens. Users must verify their email
  before they can log in.
- Verification links expire after the configured
  `EMAIL_VERIFICATION_TIMEOUT` period (24 hours by default).
- The frontend verification page reads `uid` and `token` from the email link
  and sends them as JSON to `/accounts/verify-email/`.
- Resend responses are intentionally identical for existing and unknown email
  addresses to prevent account enumeration.
- Registration, verification, and resend endpoints are rate limited.

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
| `POST` | `/tickets/{id}/status/` | JWT | Client may set `CLOSED` or reopen a closed ticket with `OPEN`; staff may set any valid status |
| `POST` | `/tickets/{ticket_id}/messages/` | JWT | Add a reply message to an existing ticket |

### 5.5 Billing & Financials

| Method | Endpoint | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `/billing/contracts/` | JWT | List contracts (Admin sees all, Client sees own) |
| `POST` | `/billing/contracts/` | Admin | Create a new contract |
| `GET` | `/billing/contracts/{id}/` | JWT | Get contract details |
| `PUT/PATCH/DELETE` | `/billing/contracts/{id}/` | Admin | Update or delete contract |
| `GET` | `/billing/contracts/{id}/download/` | JWT | Securely download a contract (owner or Admin) |
| `GET` | `/billing/invoices/` | JWT | List invoices (Admin sees all, Client sees own) |
| `POST` | `/billing/invoices/` | Admin | Create an invoice header; `total_amount` is calculated from its items |
| `GET` | `/billing/invoices/{id}/` | JWT | Get invoice details and line items |
| `PUT/PATCH/DELETE` | `/billing/invoices/{id}/` | Admin | Update or delete invoice |
| `GET/POST` | `/billing/invoice-items/` | Admin | List or create individual invoice items |
| `GET/PUT/PATCH/DELETE` | `/billing/invoice-items/{id}/` | Admin | Manage specific invoice item |
| `GET` | `/billing/transactions/` | JWT | List transactions / payment receipts |
| `POST` | `/billing/transactions/` | JWT | Upload payment receipt for an invoice |
| `GET` | `/billing/transactions/{id}/` | JWT | Get a payment receipt (Admin sees all; Client sees own) |
| `PUT/PATCH` | `/billing/transactions/{id}/` | Admin | Approve or reject a receipt by updating its `status` |
| `DELETE` | `/billing/transactions/{id}/` | Admin | Delete a payment receipt |
| `GET` | `/billing/transactions/{id}/receipt/` | JWT | Securely download a receipt (owner or Admin) |

Billing rules:

- `total_amount` is read-only and is recalculated after every invoice item
  create, update, or delete operation.
- Invoice items cannot be changed after a payment receipt is approved or when
  the invoice is canceled.
- Transaction requests use the integer invoice `id` in the writable `invoice`
  field. Responses also include the human-readable `invoice_number`.
- Financial amounts are returned as decimal strings with exactly two decimal
  places.
- Transaction amounts must be positive, cannot exceed the current remaining
  amount, and a reference code cannot be reused for the same invoice.
- Receipts cannot be submitted for canceled, fully paid, or zero-total
  invoices.
- Contract and receipt files are stored outside public `MEDIA_ROOT`. Their
  direct storage URLs are not included in API responses.
- File downloads require authentication and are limited to the file owner or
  an Admin/Staff user.

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
| **Invoice Status** | `UNPAID`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `CANCELED` | Billing invoice state |
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
  "total_amount": "250000000.00",
  "approved_amount": "0.00",
  "remaining_amount": "250000000.00",
  "status": "UNPAID",
  "status_display": "Unpaid",
  "due_date": "2026-09-01",
  "items": [
    {
      "id": 1,
      "invoice": 10,
      "description": "Frontend Development - Phase 1",
      "quantity": 1,
      "unit_price": "250000000.00",
      "total_price": "250000000.00"
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

Secure file download example:

```javascript
const response = await fetch(contract.download_url, {
  headers: {
    Authorization: `Bearer ${accessToken}`
  }
});

if (!response.ok) {
  throw new Error("File download failed");
}

const blob = await response.blob();
const objectUrl = URL.createObjectURL(blob);
const link = document.createElement("a");
link.href = objectUrl;
link.download = "contract.pdf";
link.click();
URL.revokeObjectURL(objectUrl);
```

After deploying a version that introduces private billing storage, run:

```bash
python manage.py migrate
python manage.py move_billing_files_to_private
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
