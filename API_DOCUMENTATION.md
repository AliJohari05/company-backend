Agency & Automation Platform API

API Version: 1.0.0OpenAPI: 3.0.3Purpose: REST API for the Agency platform covering accounts, services, projects, tickets, billing, blog, portfolio, and site content.

This document is the frontend integration guide for the Agency Backend API. The OpenAPI/Swagger specification is the source of truth for endpoint paths, request schemas, response schemas, authentication requirements, and enum values.

1. API Base URL

The supplied OpenAPI specification does not define a servers section, so the API host is environment-dependent.

Development

http://localhost:8000

Production

https://api.yourdomain.com

Replace the production URL with the actual production API domain before deployment.

All endpoints documented below already include the /api/v1/ prefix.

2. Interactive API Documentation

When the backend is running, the recommended development tools are:

Resource

URL

Swagger UI

http://localhost:8000/api/docs/

ReDoc

http://localhost:8000/api/redoc/

OpenAPI Schema

http://localhost:8000/api/schema/

Swagger UI should be used to inspect and test individual endpoints before implementing them in the frontend.

3. Authentication

The API uses JWT Bearer Authentication.

The OpenAPI security scheme is:

Scheme: Bearer
Format: JWT

Authenticated requests must include:

Authorization: Bearer <access_token>

Example:

GET /api/v1/accounts/profile/
Authorization: Bearer <access_token>

Token Flow

Send user credentials to the login endpoint.

Store the returned access and refresh tokens securely.

Send the access token with protected requests.

When the access token needs to be refreshed, send the refresh token to the refresh endpoint.

Use the newly returned access token for subsequent requests.

4. Account & Authentication Endpoints

4.1 Register

POST /api/v1/accounts/register/

Creates a new user account.

Authentication: Public endpoint.

Request

{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+123456789",
  "company_name": "Example Company",
  "password": "your-password",
  "password_confirm": "your-password"
}

Required Fields

email

password

password_confirm

Success

201 Created

4.2 Login

POST /api/v1/accounts/login/

Authenticates a user and returns an access/refresh JWT pair.

Authentication: Public endpoint.

Request

{
  "email": "user@example.com",
  "password": "your-password"
}

Response

{
  "access": "<access_token>",
  "refresh": "<refresh_token>"
}

Success

200 OK

4.3 Refresh Access Token

POST /api/v1/accounts/refresh/

Returns a new access token when the refresh token is valid.

Request

{
  "refresh": "<refresh_token>"
}

Response

{
  "access": "<new_access_token>",
  "refresh": "<refresh_token>"
}

Success

200 OK

4.4 Logout

POST /api/v1/accounts/logout/

Logs out the authenticated user.

Authentication: Required.

Success

200 OK

No response body is defined by the OpenAPI schema.

4.5 Get Profile

GET /api/v1/accounts/profile/

Returns the authenticated user's profile.

Authentication: Required.

Success

200 OK

4.6 Update Profile

PUT /api/v1/accounts/profile/

Updates the authenticated user's profile.

Authentication: Required.

Supported request formats:

application/json

application/x-www-form-urlencoded

multipart/form-data

Success

200 OK

4.7 Partially Update Profile

PATCH /api/v1/accounts/profile/

Partially updates the authenticated user's profile.

Authentication: Required.

Success

200 OK

4.8 Change Password

POST /api/v1/accounts/change-password/

Changes the authenticated user's password.

Authentication: Required.

Request

{
  "old_password": "old-password",
  "new_password": "new-password"
}

Required Fields

old_password

new_password

Success

200 OK

5. Services

5.1 List Active Services

GET /api/v1/services/

Returns all active services.

Authentication: Not required.

Success

200 OK

The response uses the ServiceList schema.

5.2 Get Service Details

GET /api/v1/services/{slug}/

Returns details of a specific service together with its pricing plans.

Authentication: Not required.

Path Parameter

Parameter

Type

Required

slug

string

Yes

Success

200 OK

The response uses the ServiceDetail schema.

5.3 List Service Categories

GET /api/v1/services/categories/

Returns active service categories together with their sub-services.

Authentication: Not required.

Success

200 OK

The response uses the ServiceCategory schema.

6. Projects

6.1 List / Create Project Requests

GET /api/v1/projects/
POST /api/v1/projects/

GET

Retrieves project requests for the current user.

Authentication: Required.

POST

Creates a new project request.

Authentication: Required.

Request Fields

The ProjectRequest schema defines the project request fields. Client-submitted fields include:

{
  "service": 1,
  "title": "New Website Project",
  "description": "Project requirements and details",
  "estimated_budget": "5000.00"
}

Success

GET  -> 200 OK
POST -> 201 Created

6.2 Get Project Request Details

GET /api/v1/projects/{id}/

Retrieves a specific project request owned by the user or accessible to staff.

Authentication: Required.

Path Parameter

Parameter

Type

Required

id

integer

Yes

Success

200 OK

6.3 Upload Project Attachment

POST /api/v1/projects/{project_id}/attachments/

Uploads an attachment for an existing project request.

Authentication: Required.

Path Parameter

Parameter

Type

Required

project_id

integer

Yes

Success

201 Created

The response uses the ProjectAttachment schema.

7. Tickets / Support

7.1 List / Create Tickets

GET /api/v1/tickets/
POST /api/v1/tickets/

Authentication: Required.

GET

Lists the user's tickets.

POST

Creates a new ticket together with its initial message.

The creation schema is TicketCreate.

Example:

{
  "title": "Website issue",
  "priority": "HIGH",
  "message": "I need help with my website."
}

Success

GET  -> 200 OK
POST -> 201 Created

7.2 Get Ticket Details

GET /api/v1/tickets/{id}/

Returns ticket details including nested messages.

Authentication: Required.

Path Parameter

Parameter

Type

Required

id

integer

Yes

Success

200 OK

7.3 Close / Reopen Ticket

POST /api/v1/tickets/{id}/close/

Changes a ticket status to CLOSED or REOPENED according to the backend action logic.

Authentication: Required.

Success

200 OK

The OpenAPI schema does not define a request body for this action. Use Swagger UI for the exact current behavior.

7.4 Add Ticket Message

POST /api/v1/tickets/{ticket_id}/messages/

Creates a new reply inside an existing ticket.

Authentication: Required.

Path Parameter

Parameter

Type

Required

ticket_id

integer

Yes

Success

201 Created

The response uses the TicketMessage schema.

8. Billing

Billing endpoints are protected by JWT authentication.

8.1 Contracts

List Contracts

GET /api/v1/billing/contracts/

Admin users can see all contracts.

Regular users can see their own contracts.

Optional query parameters:

?search=<term>
?ordering=<field>

Create Contract

POST /api/v1/billing/contracts/

Admin only.

Success

GET  -> 200 OK
POST -> 201 Created

8.2 Contract Details

GET    /api/v1/billing/contracts/{id}/
PUT    /api/v1/billing/contracts/{id}/
PATCH  /api/v1/billing/contracts/{id}/
DELETE /api/v1/billing/contracts/{id}/

Permissions

GET: Retrieve contract details.

PUT/PATCH/DELETE: Admin only.

Path Parameter

Parameter

Type

Required

id

integer

Yes

Success

GET    -> 200 OK
PUT    -> 200 OK
PATCH  -> 200 OK
DELETE -> 204 No Content

8.3 Invoices

List Invoices

GET /api/v1/billing/invoices/

Admin users can see all invoices.

Regular users can see only their own invoices.

Optional query parameters:

?search=<term>
?ordering=<field>

Create Invoice

POST /api/v1/billing/invoices/

Admin only.

Success

GET  -> 200 OK
POST -> 201 Created

8.4 Invoice Details

GET    /api/v1/billing/invoices/{id}/
PUT    /api/v1/billing/invoices/{id}/
PATCH  /api/v1/billing/invoices/{id}/
DELETE /api/v1/billing/invoices/{id}/

Permissions

GET: Retrieve invoice details.

PUT/PATCH/DELETE: Admin only.

Success

GET    -> 200 OK
PUT    -> 200 OK
PATCH  -> 200 OK
DELETE -> 204 No Content

8.5 Invoice Items

List / Create

GET  /api/v1/billing/invoice-items/
POST /api/v1/billing/invoice-items/

Admin only.

Optional filter:

?invoice=<invoice_id>

Individual Item

GET    /api/v1/billing/invoice-items/{id}/
PUT    /api/v1/billing/invoice-items/{id}/
PATCH  /api/v1/billing/invoice-items/{id}/
DELETE /api/v1/billing/invoice-items/{id}/

Admin only.

Success

GET    -> 200 OK
POST   -> 201 Created
PUT    -> 200 OK
PATCH  -> 200 OK
DELETE -> 204 No Content

8.6 Payment Transactions

List / Upload Payment Receipt

GET  /api/v1/billing/transactions/
POST /api/v1/billing/transactions/

GET

Admin users can see all payment receipts.

Regular users can see their own payment receipts.

Optional query parameters:

?search=<term>
?ordering=<field>

POST

Uploads a payment receipt for an invoice.

The transaction schema contains:

receipt_attachment

as the receipt file field.

For file uploads, use:

Content-Type: multipart/form-data

Example frontend request:

const formData = new FormData();

formData.append("invoice", invoiceId);
formData.append("amount", amount);
formData.append("reference_code", referenceCode);
formData.append("receipt_attachment", file);

fetch(`${API_BASE_URL}/api/v1/billing/transactions/`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
  body: formData,
});

When using FormData, do not manually set the Content-Type header. The browser creates the required multipart boundary automatically.

Success

GET  -> 200 OK
POST -> 201 Created

8.7 Transaction Details

GET    /api/v1/billing/transactions/{id}/
PUT    /api/v1/billing/transactions/{id}/
PATCH  /api/v1/billing/transactions/{id}/
DELETE /api/v1/billing/transactions/{id}/

Authentication: Required.

Success

GET    -> 200 OK
PUT    -> 200 OK
PATCH  -> 200 OK
DELETE -> 204 No Content

9. Blog

9.1 Categories

GET  /api/v1/blog/categories/
POST /api/v1/blog/categories/

The GET operation is public.

Category management supports:

GET    /api/v1/blog/categories/{id}/
PUT    /api/v1/blog/categories/{id}/
PATCH  /api/v1/blog/categories/{id}/
DELETE /api/v1/blog/categories/{id}/

Success

GET    -> 200 OK
POST   -> 201 Created
PUT    -> 200 OK
PATCH  -> 200 OK
DELETE -> 204 No Content

9.2 Posts

List Published Posts

GET /api/v1/blog/posts/

Returns published posts.

Authentication: Not required.

Success

200 OK

The response uses PostList.

Post Details

GET /api/v1/blog/posts/{slug}/

Returns a post by slug and increases its view count by 1.

Authentication: Not required.

Path Parameter

Parameter

Type

Required

slug

string

Yes

Success

200 OK

The OpenAPI specification also exposes PUT, PATCH, and DELETE for this path. Check the current Swagger permissions and schema before using those operations from the frontend.

9.3 Tags

List / Create

GET  /api/v1/blog/tags/
POST /api/v1/blog/tags/

The list operation is public.

Individual Tag

GET    /api/v1/blog/tags/{id}/
PUT    /api/v1/blog/tags/{id}/
PATCH  /api/v1/blog/tags/{id}/
DELETE /api/v1/blog/tags/{id}/

The individual tag management operations are documented as admin-only.

10. Portfolio

Portfolio endpoints are public according to the supplied OpenAPI specification.

10.1 Portfolio Categories

GET /api/v1/portfolio/categories/

Returns all portfolio categories.

Success

200 OK

10.2 Portfolio Items

GET /api/v1/portfolio/items/

Returns portfolio items.

The endpoint supports filtering by:

category

technology

featured status

Use Swagger UI to verify the exact query parameter names and accepted values exposed by the running API.

Success

200 OK

The list response uses PortfolioItemList.

10.3 Portfolio Item Details

GET /api/v1/portfolio/items/{slug}/

Returns the complete details of a portfolio project using its slug.

Success

200 OK

The response uses PortfolioItemDetail.

11. Core / Public Site Content

11.1 FAQs

GET /api/v1/core/faqs/

Returns all active frequently asked questions.

Authentication: Not required.

Success

200 OK

11.2 Site Settings

GET /api/v1/core/settings/

Returns site general settings, contact information, and social links in a single request.

Authentication: Not required.

Success

200 OK

The response uses SiteSetting.

11.3 Social Links

GET /api/v1/core/social-links/

Returns all active social media links.

Authentication: Not required.

Success

200 OK

12. Enum Values

Use the exact enum values returned by the API. Enum values are case-sensitive.

User Roles

ADMIN
STAFF
CLIENT

Value

Meaning

ADMIN

Administrator

STAFF

Staff

CLIENT

Client

Project Request Status

PENDING
APPROVED
IN_PROGRESS
COMPLETED
REJECTED

Value

Meaning

PENDING

Pending

APPROVED

Approved

IN_PROGRESS

In Progress

COMPLETED

Completed

REJECTED

Rejected

Ticket Priority

LOW
MEDIUM
HIGH

Value

Meaning

LOW

Low

MEDIUM

Medium

HIGH

High

Ticket Status

The OpenAPI schema defines:

OPEN
IN_PROGRESS
RESOLVED
CLOSED

Invoice Status

UNPAID
PAID
OVERDUE
CANCELED

Value

Meaning

UNPAID

Unpaid

PAID

Paid

OVERDUE

Overdue

CANCELED

Canceled

Transaction Status

PENDING
APPROVED
REJECTED

Value

Meaning

PENDING

Pending verification

APPROVED

Approved

REJECTED

Rejected

Contract Status

The API exposes a ContractStatusEnum. Use Swagger/OpenAPI as the source of truth for its currently defined values.

13. Main Data Models

UserProfile

id
email
first_name
last_name
phone_number
company_name
role
created_at

Read-only fields include:

id
email
role
created_at

ServiceList

id
category
category_name
category_slug
title
slug
short_description
icon
is_active

ServiceDetail

id
category
category_name
category_slug
title
slug
short_description
full_description
icon
is_active
plans

ServicePlan

id
title
price
features
is_popular

ProjectRequest

id
user
user_email
service
service_detail
title
description
estimated_budget
status
status_display
attachments
created_at
updated_at

Several fields are generated by the backend and are read-only, including:

id
user
user_email
service_detail
status
status_display
attachments
created_at
updated_at

ProjectAttachment

id
file
description
created_at

TicketList

id
user
user_email
title
priority
priority_display
status
status_display
created_at
updated_at

TicketDetail

id
user
user_email
title
priority
priority_display
status
status_display
created_at
updated_at
messages

TicketMessage

id
ticket
user
user_email
is_staff
message
attachment
created_at
updated_at

Invoice

id
invoice_number
user
user_email
project_request
service
total_amount
status
status_display
due_date
created_at
updated_at
items
transactions

InvoiceItem

id
invoice
description
quantity
unit_price
total_price

Transaction

id
invoice
user
user_email
amount
reference_code
receipt_attachment
status
status_display
created_at

Contract

id
user
user_email
title
file
status
status_display
start_date
end_date
created_at

Blog Post

PostList

id
title
slug
excerpt
featured_image
meta_description
author
category
tags
is_published
published_at
views_count
created_at

PostDetail

id
title
slug
content
featured_image
meta_description
author
category
tags
category_detail
tags_detail
is_published
published_at
views_count
created_at
updated_at

Portfolio Item

PortfolioItemList

id
title
slug
category
technologies
cover_image
summary
github_url
live_demo_url
is_featured

PortfolioItemDetail

id
title
slug
category
technologies
cover_image
summary
description
github_url
live_demo_url
client_name
is_featured
created_at
images

Portfolio Image

id
image
caption

Technology

id
name
icon

FAQ

id
question
answer
order

SocialLink

id
title
url
icon

SiteSetting

site_name
site_logo
about_us
email
phone_number
address
working_hours
social_links

14. Common HTTP Status Codes

The OpenAPI file explicitly defines the following success status codes across the API:

Status

Meaning

200

Successful request

201

Resource created

204

Successful request with no response body

For error responses, the exact status codes and response bodies should be checked in the running API/Swagger documentation because they are not uniformly defined for every endpoint in the supplied OpenAPI file.

15. Frontend Integration Checklist

Before implementing an endpoint, check:

Correct API base URL

Correct API version: /api/v1/

Correct HTTP method

Authentication requirement

Required headers

Path parameters

Query parameters

Request body schema

Required fields

Read-only fields

Enum values

File upload requirements

Response schema

Success status code

Error handling

16. Recommended Frontend API Configuration

Do not hard-code the backend URL throughout the frontend application.

For a Vite frontend, use an environment variable:

VITE_API_BASE_URL=http://localhost:8000

Production:

VITE_API_BASE_URL=https://api.yourdomain.com

Example:

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const response = await fetch(
  `${API_BASE_URL}/api/v1/services/`
);

const data = await response.json();

17. Recommended Authentication Configuration

A typical authenticated request should look like:

const response = await fetch(
  `${API_BASE_URL}/api/v1/accounts/profile/`,
  {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
  }
);

For FormData uploads:

const formData = new FormData();

formData.append("receipt_attachment", file);

const response = await fetch(
  `${API_BASE_URL}/api/v1/billing/transactions/`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: formData,
  }
);

Do not manually add:

Content-Type: multipart/form-data

when sending browser FormData.

18. Complete Endpoint Reference

Method

Endpoint

Authentication

Purpose

POST

/api/v1/accounts/register/

Public

Register

POST

/api/v1/accounts/login/

Public

Login

POST

/api/v1/accounts/refresh/

Public

Refresh JWT

POST

/api/v1/accounts/logout/

JWT

Logout

GET

/api/v1/accounts/profile/

JWT

Get profile

PUT/PATCH

/api/v1/accounts/profile/

JWT

Update profile

POST

/api/v1/accounts/change-password/

JWT

Change password

GET/POST

/api/v1/services/

Public

Services

GET

/api/v1/services/{slug}/

Public

Service details

GET

/api/v1/services/categories/

Public

Service categories

GET/POST

/api/v1/projects/

JWT

Project requests

GET

/api/v1/projects/{id}/

JWT

Project details

POST

/api/v1/projects/{project_id}/attachments/

JWT

Project attachment

GET/POST

/api/v1/tickets/

JWT

Tickets

GET

/api/v1/tickets/{id}/

JWT

Ticket details

POST

/api/v1/tickets/{id}/close/

JWT

Close/reopen ticket

POST

/api/v1/tickets/{ticket_id}/messages/

JWT

Ticket reply

GET/POST

/api/v1/billing/contracts/

JWT

Contracts

GET/PUT/PATCH/DELETE

/api/v1/billing/contracts/{id}/

JWT

Contract detail

GET/POST

/api/v1/billing/invoices/

JWT

Invoices

GET/PUT/PATCH/DELETE

/api/v1/billing/invoices/{id}/

JWT

Invoice detail

GET/POST

/api/v1/billing/invoice-items/

JWT

Invoice items

GET/PUT/PATCH/DELETE

/api/v1/billing/invoice-items/{id}/

JWT

Invoice item detail

GET/POST

/api/v1/billing/transactions/

JWT

Payment transactions

GET/PUT/PATCH/DELETE

/api/v1/billing/transactions/{id}/

JWT

Transaction detail

GET/POST

/api/v1/blog/categories/

Public*

Blog categories

GET/PUT/PATCH/DELETE

/api/v1/blog/categories/{id}/

Check Swagger

Category management

GET/POST

/api/v1/blog/posts/

Public*

Published posts

GET

/api/v1/blog/posts/{slug}/

Public

Post details

GET/PUT/PATCH/DELETE

/api/v1/blog/posts/{slug}/

Check Swagger

Post management

GET/POST

/api/v1/blog/tags/

Public*

Tags

GET/PUT/PATCH/DELETE

/api/v1/blog/tags/{id}/

Admin for management

Tag management

GET

/api/v1/core/faqs/

Public

FAQs

GET

/api/v1/core/settings/

Public

Site settings

GET

/api/v1/core/social-links/

Public

Social links

GET

/api/v1/portfolio/categories/

Public

Portfolio categories

GET

/api/v1/portfolio/items/

Public

Portfolio list

GET

/api/v1/portfolio/items/{slug}/

Public

Portfolio details

* For endpoints where the OpenAPI file exposes multiple operations with different security metadata, verify the specific operation in Swagger before implementation.

19. Source of Truth

This documentation is based on:

Agency & Automation Platform API
OpenAPI Version: 3.0.3
API Version: 1.0.0

The frontend team should always use the live OpenAPI/Swagger documentation as the final authority when an endpoint's behavior differs from this overview.

Swagger:
http://localhost:8000/api/docs/

ReDoc:
http://localhost:8000/api/redoc/

OpenAPI:
http://localhost:8000/api/schema/

Frontend Quick Start

1. Start the backend
       ↓
2. Open Swagger UI
       ↓
3. Authenticate if required
       ↓
4. Select the required endpoint
       ↓
5. Check request schema
       ↓
6. Test with "Try it out"
       ↓
7. Check the response
       ↓
8. Implement the API call in the frontend
       ↓
9. Handle loading, success and error states

Agency & Automation Platform API — Frontend Integration Documentation

Keep this document synchronized with the OpenAPI specification whenever API endpoints, permissions, schemas, or enum values change.