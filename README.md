# IssuePay

IssuePay is a Django REST API for managing customer issues and processing payments. It includes role-based access control, issue management, payment tracking, M-Pesa STK Push integration, and M-Pesa callback processing.

## 🚀 Live API

- **Production API:** [https://issuepay.onrender.com](https://issuepay.onrender.com)
- **GitHub:** [[https://github.com/otieno-backend/issuepay](https://github.com/otieno-backend/issuepay)](https://github.com/otieno-backend/issuepay)

## ✨ Features

- User registration and JWT authentication
- Custom user model with Customer, Staff, and Admin roles
- Role-based permissions
- Customer issue management
- Staff issue updates
- Payment creation and tracking
- Payment status management
- M-Pesa STK Push integration
- M-Pesa callback processing
- M-Pesa transaction receipt tracking
- Payment success and failure notifications
- PostgreSQL database
- Production deployment with Render
- Automated tests

## 🛠️ Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Simple JWT
- Django Filter
- M-Pesa Daraja API
- Gunicorn
- Render

## 📁 Project Structure

```text
issuepay/
├── accounts/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── issues/
│   ├── models.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── views.py
│   └── urls.py
├── payments/
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   └── urls.py
├── notifications/
│   └── services.py
├── issuepay/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── README.md
```

## User Roles

| Role | Access |
|---|---|
| Customer | Create and manage their own issues and payments |
| Staff | Manage issues and update issue information |
| Admin | Manage administrative functions |

New users are registered as Customers by default.

## Issue Management

IssuePay allows customers and staff to manage issues from creation to resolution.

Each issue includes:

- Title
- Description
- Amount
- Customer
- Assigned staff member
- Status
- Priority
- Created date
- Updated date

### Issue Status

- OPEN
- IN_PROGRESS
- RESOLVED
- CLOSED

### Priority

- LOW
- MEDIUM
- HIGH
- URGENT

## Payment Management

Payments are linked to customer issues.

The system tracks:

- Payment amount
- Payment method
- Payment status
- Transaction ID
- Payment date

### Payment Status

- PENDING
- SUCCESSFUL
- FAILED
- REFUNDED

### Payment Methods

- M-Pesa
- Card
- Bank Transfer

## M-Pesa Integration

IssuePay integrates with the Safaricom M-Pesa Daraja API to support STK Push payments.

### Payment Flow

Customer
    ↓
Creates a payment
    ↓
Requests an STK Push
    ↓
Receives an M-Pesa prompt
    ↓
Confirms or cancels the payment
    ↓
M-Pesa sends a callback
    ↓
IssuePay updates the payment status

### M-Pesa Endpoints

POST /api/payments/mpesa/stk-push/

POST /api/payments/mpesa/callback/

The system processes successful and failed M-Pesa callbacks and records the transaction receipt when a payment is successful.

## API Endpoints

### Authentication

POST /api/auth/token/

POST /api/auth/token/refresh/

GET /api/auth/me/

### Issues

GET /api/issues/

POST /api/issues/

GET /api/issues/<id>/

PUT /api/issues/<id>/

PATCH /api/issues/<id>/

### Payments

GET /api/payments/

POST /api/payments/

GET /api/payments/<id>/

### M-Pesa

POST /api/payments/mpesa/stk-push/

POST /api/payments/mpesa/callback/

Protected endpoints require JWT authentication.

Example:

Authorization: Bearer <access_token>

## Technology

IssuePay is built using:

- Python
- Django
- Django REST Framework
- PostgreSQL
- JWT Authentication
- M-Pesa Daraja API
- Gunicorn
- Render

## Local Development

### 1. Clone the project

git clone https://github.com/otieno-backend/issuepay.git

cd issuepay

### 2. Create a virtual environment

python -m venv venv

### 3. Activate the virtual environment

For Git Bash:

source venv/Scripts/activate

### 4. Install dependencies

pip install -r requirements.txt

### 5. Run database migrations

python manage.py migrate

### 6. Start the development server

python manage.py runserver

The API will be available at:

http://127.0.0.1:8000/

## Testing

Run the automated test suite:

python manage.py test

Current test result:

78 tests passed

The tests cover authentication, users, permissions, issues, payments, and M-Pesa integration.

## Production

IssuePay is deployed on Render.

Live API:

[https://issuepay.onrender.com](https://issuepay.onrender.com)

The production environment uses:

- Gunicorn
- Django REST Framework
- PostgreSQL

## Security

IssuePay uses:

- JWT authentication
- Role-based permissions
- Secure password hashing
- Environment variables for sensitive credentials
- Protected API endpoints
- Database transactions for payment callbacks

Never commit passwords, API keys, M-Pesa credentials, or .env files to GitHub.

## Developer

Brian Otieno

Backend Software Developer

GitHub:
[[https://github.com/otieno-backend](https://github.com/otieno-backend)](https://github.com/otieno-backend)

LinkedIn:
[https://www.linkedin.com/in/brian-ochieng-ba1817374](https://www.linkedin.com/in/brian-ochieng-ba1817374)

---

IssuePay — Issue management and payment processing through a secure REST API.