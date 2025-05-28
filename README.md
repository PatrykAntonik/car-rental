# 🚗 Car Rental API

**Car Rental API** is a Django REST Framework project for managing a car rental service. It features user roles, car
listings, rental bookings, payment tracking, and authentication (JWT + Google OAuth2).

## 🛠 Technologies Used

- Django & Django REST Framework
- Simple JWT (Token-based Authentication)
- Google OAuth2
- drf-spectacular (OpenAPI schema)
- PostgreSQL

---

## 🚀 Features

- Role-based access control (Customer & Owner)
- JWT authentication with access/refresh tokens
- Google OAuth2 login
- Car availability and conflict checks
- Rental creation with automatic payment creation
- Admin & customer rental views
- Customer profile management
- API documentation using Swagger UI

---

## 📦 Installation

1. **Clone the repository**

```bash
git clone https://github.com/PatrykAntonik/car-rental.git
cd car-rental-api
```

2. **Create environment variables**
   Create a `.env` file in the project root with the following variables:

```env
SECRET_KEY=your_secret_key
DEBUG=True
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

3. **Build the Docker container**

```bash
docker build --no-cache -t car_rental_test .
```

4. **Run the Docker container**

```bash
docker run -p 8000:8000 car_rental_test
```

# App Usage

#### You can use App locally on `http://localhost:8000/` or on already deployed version (Azure Container Apps) at

`car-rental-api.salmonground-875e3968.polandcentral.azurecontainerapps.io`

For both versions, you can use Swagger UI to explore and test the API endpoints. Another way is to to manually test
enpoints. Below are example user logins (only for deployed version).

#### Swagger UI instructions:

You can login using login endpoint
`/api/users/login/`. Once logged in, you can copy access token from the response and paste it into the "Authorize"
button in Swagger UI. This will allow you to test endpoints that require authentication and access
endpoints according to your user role.

#### Example user logins for deployed version:

- **Customer**:
    - Email: `customer@example.com`
    - Password: `trudneHaslo123`
- **Owner**:
    - Email: `owner@example.com`
    - Password: `trudneHaslo123`
- **Admin**:
    - Email: `admin@example.com`
    - Password: `trudneHaslo123`

Local version uses SQLite database, while deployed version uses PostgreSQL on Azure.

*For local development you need to create new user accounts.

# API Documentation

You can access the API documentation at site root: `http://localhost:8000/` or on deployed version at
`car-rental-api.salmonground-875e3968.polandcentral.azurecontainerapps.io`.