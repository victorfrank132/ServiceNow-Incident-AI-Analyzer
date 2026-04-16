#!/usr/bin/env python
"""
Clean up existing incidents and create a fresh batch of API-related test incidents
with detailed error information, status codes, payloads, and headers.
"""

import sys
import os
from dotenv import load_dotenv

sys.path.insert(0, "/Users/apple/Desktop/Snow_TicketAssignment")

from src.servicenow_client import ServiceNowClient

# Load environment
load_dotenv("config/.env")

instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
username = os.getenv("SERVICENOW_USERNAME")
password = os.getenv("SERVICENOW_PASSWORD")

print("=" * 70)
print("ServiceNow Incident Cleanup & API Incidents Setup")
print("=" * 70)

# Initialize client
client = ServiceNowClient(instance_url, username, password)

# API-related incidents with detailed error information
api_incidents = [
    {
        "title": "API Rate Limiting - Payment Service",
        "description": """Endpoint: POST /api/v2/payments/process
Users are experiencing 429 Too Many Requests errors when calling payment processing API.
The service returns rate limit exceeded responses during peak hours (12-2PM EST).
Affects checkout flow for e-commerce platform.

Error Response:
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Limit: 1000 requests per minute",
  "retry_after": 60,
  "current_usage": 1200,
  "limit": 1000,
  "window": "60 seconds",
  "error_id": "ERR_RATE_LIMIT_001"
}

Request Headers:
Authorization: Bearer sk_live_abc123
Content-Type: application/json
X-Request-ID: req_12345abcde
User-Agent: PaymentClient/2.1.0

Request Body:
{
  "amount": 99.99,
  "currency": "USD",
  "customer_id": "cust_abc123",
  "description": "Order #12345"
}

Impact: 45% of payment transactions failing, estimated $15K/hour revenue loss.""",
        "category": "Application",
        "priority": "1",
        "urgency": "1",
        "impact": "1"
    },
    {
        "title": "REST API Authentication Failure",
        "description": """Endpoint: GET /api/v1/users/profile
API key validation failing for premium tier customers.
All requests from enterprise customers returning 401 Unauthorized even with valid credentials.

Error Response:
HTTP/1.1 401 Unauthorized
Content-Type: application/json
X-Error-Identifier: AUTH_ERR_002
{
  "status_code": 401,
  "error_type": "InvalidCredentials",
  "message": "API key validation failed: Key format invalid or expired",
  "timestamp": "2026-03-27T14:32:15.234Z",
  "error_code": "AUTH_001",
  "hint": "API key may have expired. Please regenerate from dashboard",
  "request_id": "req_78910fghij"
}

Request Headers:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-API-Version: 2.0
Accept: application/json
X-Request-ID: req_78910fghij

Status: 401 Unauthorized
Error ID: AUTH_ERR_002
Affected Customers: 12 enterprise accounts
Duration: 45+ minutes

Stack Trace:
ValidationError at /api/v1/auth/validate
File "auth_service.py", line 156, in validate_key()
  raise ValidationError("Key validation failed")""",
        "category": "Security",
        "priority": "1",
        "urgency": "1",
        "impact": "2"
    },
    {
        "title": "API Gateway Timeout",
        "description": """Endpoint: POST /api/v2/analytics/batch
API gateway timing out on requests to backend microservices.
Gateway configured with 30s timeout but backend services taking 45-120 seconds.

Error Response:
HTTP/1.1 504 Gateway Timeout
Content-Type: application/json
{
  "error": "gateway_timeout",
  "code": "GATEWAY_504",
  "message": "Backend service did not respond within 30000ms",
  "timestamp": "2026-03-27T14:45:32.567Z",
  "trace_id": "trace_9a8b7c6d",
  "affected_service": "analytics-processor",
  "timeout_ms": 30000,
  "service_response_time": 45000,
  "error_id": "GATEWAY_ERR_003"
}

Request:
POST /api/v2/analytics/batch HTTP/1.1
Host: api.example.com
Content-Type: application/json
Content-Length: 4521
X-Request-ID: req_analysis_batch_001

Request Body (4.2KB):
{
  "batch_id": "batch_2026_03_27_001",
  "events": [
    {
      "user_id": "user_12345",
      "action": "page_view",
      "timestamp": "2026-03-27T14:30:00Z",
      "metadata": {...}
    },
    ... 523 more events
  ]
}

Failure Rate: 67% of analytics API calls
Resolution: Increase gateway timeout or optimize backend services""",
        "category": "Infrastructure",
        "priority": "1",
        "urgency": "1",
        "impact": "1"
    },
    {
        "title": "GraphQL Query Performance Degradation",
        "description": """Endpoint: POST /graphql
Complex GraphQL queries showing severe performance degradation.
Queries that previously executed in 200ms now taking 5-10 seconds.

Error Response:
HTTP/1.1 200 OK
Content-Type: application/json
{
  "data": null,
  "errors": [
    {
      "message": "Query timeout: execution exceeded 10000ms",
      "extensions": {
        "code": "QUERY_TIMEOUT",
        "error_id": "GQL_PERF_004",
        "execution_time_ms": 10234,
        "max_allowed_ms": 10000,
        "timestamp": "2026-03-27T14:55:22.891Z"
      }
    }
  ]
}

GraphQL Query:
query GetUserData($userId: ID!) {
  user(id: $userId) {
    id
    name
    email
    orders(limit: 100) {
      id
      total
      items {
        name
        price
        quantity
        reviews {
          rating
          comment
        }
      }
    }
    analytics {
      pageViews
      clickthrough
      conversionRate
    }
  }
}

Variables:
{"userId": "user_enterprise_001"}

Database Metrics:
- Query execution: 5234ms (was 234ms)
- Resolver calls: 892 (database n+1 problem suspected)
- Memory usage: 1.2GB (was 120MB)
- CPU: 94% (was 12%)

Error ID: GQL_PERF_004
Root Cause: Possible cache invalidation or missing database indexes""",
        "category": "Database",
        "priority": "2",
        "urgency": "2",
        "impact": "2"
    },
    {
        "title": "API Webhook Delivery Failure",
        "description": """Webhook Endpoint: POST https://customer.example.com/webhooks/events
Webhooks not delivering to customer endpoints.
Event queue backing up with 10,000+ pending webhook events.

Error Response (from retry):
HTTP/1.1 500 Internal Server Error
Content-Type: application/json
{
  "error": "webhook_delivery_failed",
  "status_code": 500,
  "error_id": "WEBHOOK_ERR_005",
  "attempt": 5,
  "max_retries": 5,
  "timestamp": "2026-03-27T14:20:15.432Z",
  "reason": "Webhook endpoint returned 500 error for 5 consecutive attempts"
}

Sample Webhook Payload:
POST https://customer.example.com/webhooks/events HTTP/1.1
Content-Type: application/json
X-Webhook-Signature: sha256=abc123def456...
X-Webhook-Timestamp: 1711531215
X-Event-ID: evt_abc123def456
X-Delivery-Attempt: 3

{
  "event_type": "order.created",
  "timestamp": "2026-03-27T14:15:00Z",
  "event_id": "evt_abc123def456",
  "data": {
    "order_id": "ord_12345",
    "customer_id": "cust_67890",
    "total": 299.99,
    "items": [...]
  }
}

Queue Status:
- Pending events: 10,247
- Failed deliveries: 5,132
- Customer endpoints affected: 23
- Last successful delivery: 45 minutes ago
- Error ID: WEBHOOK_ERR_005

Impact: Real-time order synchronization broken for 23 customers""",
        "category": "Application",
        "priority": "1",
        "urgency": "1",
        "impact": "2"
    },
    {
        "title": "CORS Error - Cross-Origin Requests Blocked",
        "description": """Origin: https://customer-portal.example.com
Third-party integrations failing due to CORS policy violation.
Web applications cannot call API from their domains.

Browser Console Error:
Access to XMLHttpRequest at 'https://api.example.com/api/v2/data' 
from origin 'https://customer-portal.example.com' has been blocked 
by CORS policy: No 'Access-Control-Allow-Origin' header is present 
on the requested resource.

HTTP Response Headers (Missing):
Access-Control-Allow-Origin: https://customer-portal.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400

Actual Response Received:
HTTP/1.1 200 OK
Content-Type: application/json
(No CORS headers)

Request Details:
Method: POST
URL: https://api.example.com/api/v2/customers/search
Origin: https://customer-portal.example.com
Headers:
  Authorization: Bearer token123...
  Content-Type: application/json

Error ID: CORS_ERR_006
Affected Domains: 
  - customer-portal.example.com
  - dashboard.client.com
  - analytics.integrator.io

Browser Network Error:
XMLHttpRequest { readyState: 4, status: 0, statusText: "error" }
Type: 'error'""",
        "category": "Security",
        "priority": "2",
        "urgency": "2",
        "impact": "2"
    },
    {
        "title": "API Version Deprecation - Legacy Endpoints",
        "description": """Deprecated Endpoint: GET /api/v1/users
V1 API endpoints deprecated and scheduled for removal (March 31, 2026).
Customers still using old API endpoints experiencing errors and warnings.

Deprecation Warning Response:
HTTP/1.1 200 OK
Content-Type: application/json
Deprecation: true
Sunset: Sun, 31 Mar 2026 23:59:59 GMT
Warning: 299 – "API v1 is deprecated. Please migrate to API v2"

{
  "data": [...],
  "meta": {
    "deprecation_notice": "This API version will be removed on 2026-03-31",
    "migration_endpoint": "/api/v2/users",
    "documentation": "https://docs.example.com/migration-guide",
    "error_id": "DEPRECATION_ERR_007",
    "support_deadline": "2026-03-31T23:59:59Z"
  }
}

Still Active Requests to /api/v1/:
- /api/v1/users: 12,450 daily requests
- /api/v1/orders: 8,932 daily requests  
- /api/v1/products: 23,145 daily requests

Customer Migration Status:
- Migrated: 15 customers
- In Progress: 8 customers
- Not Started: 52 customers

Error ID: DEPRECATION_ERR_007
Timeline: 4 days until full shutdown
Impact: 78,527 API calls daily will fail""",
        "category": "Application",
        "priority": "2",
        "urgency": "2",
        "impact": "3"
    },
    {
        "title": "API Documentation Mismatch",
        "description": """The API response format has changed but documentation was not updated.
Customers integrating based on old documentation are experiencing failures.

Expected (per documentation):
{
  "user": {
    "id": "user_123",
    "name": "John Doe",
    "email": "john@example.com"
  }
}

Actual Response:
HTTP/1.1 200 OK
Content-Type: application/json
{
  "status": "success",
  "code": 200,
  "data": {
    "user": {
      "id": "user_123",
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2026-01-15T10:30:00Z",
      "metadata": {...}
    }
  },
  "timestamp": "2026-03-27T15:00:00Z"
}

Breaking Changes:
1. Response wrapper added: "data" and "status" fields
2. Timestamp field added
3. New metadata object included
4. Field "created_at" is now present

Error ID: DOC_MISMATCH_008

Customer Code Failing:
const user = response.user  // Fails - response now has "data.user"
const email = user.email    // Undefined

Affected Endpoints:
- GET /api/v2/users/{id}
- GET /api/v2/orders/{id}
- POST /api/v2/payments

Customers Affected: 34
Estimated Fix Time Per Customer: 4-6 hours""",
        "category": "Application",
        "priority": "2",
        "urgency": "2",
        "impact": "2"
    },
    {
        "title": "Database Connection Pool Exhaustion - API Backend",
        "description": """The API service is running out of database connections during peak traffic.
Connection pool maxed out, requests queuing and timing out.

Database Connection Pool Status:
{
  "error_id": "DB_POOL_ERR_009",
  "timestamp": "2026-03-27T15:15:33.212Z",
  "pool_size": 100,
  "active_connections": 100,
  "idle_connections": 0,
  "waiting_requests": 247,
  "average_wait_time_ms": 3450
}

Error Response:
HTTP/1.1 503 Service Unavailable
Content-Type: application/json
{
  "error": "service_unavailable",
  "message": "Connection pool exhausted. Please retry in 30 seconds.",
  "status_code": 503,
  "error_id": "DB_POOL_ERR_009",
  "retry_after": 30,
  "queued_requests": 247,
  "pool_capacity": 100,
  "wait_time_ms": 3450
}

Database Metrics:
- Active Connections: 100/100 (100%)
- Connection Wait Queue: 247 requests
- Average Wait Time: 3.45 seconds
- Max Wait Time: 12.34 seconds
- Connection Timeout: 30 seconds

Traffic Pattern:
- Normal QPS: 500 requests/second
- Current QPS: 1,200 requests/second
- Connection Per Request: 0.5
- Expected Pool Needed: 600 connections

Configuration:
min_pool_size: 10
max_pool_size: 100
connection_timeout: 5s
idle_timeout: 300s

Error ID: DB_POOL_ERR_009
Recommendation: Increase pool size to 250 or optimize query performance""",
        "category": "Database",
        "priority": "1",
        "urgency": "1",
        "impact": "1"
    },
    {
        "title": "API Request Validation Error",
        "description": """New request validation rules are too strict, rejecting valid API calls from legacy clients.
Customers using older client libraries experiencing unexpected validation failures.

Error Response:
HTTP/1.1 400 Bad Request
Content-Type: application/json
{
  "error": "validation_error",
  "status_code": 400,
  "error_id": "VALIDATION_ERR_010",
  "timestamp": "2026-03-27T15:30:45.678Z",
  "validation_errors": [
    {
      "field": "user_type",
      "message": "Invalid enum value 'freelancer'. Allowed values: individual, business, enterprise",
      "code": "INVALID_ENUM",
      "provided_value": "freelancer"
    },
    {
      "field": "metadata",
      "message": "Field is required but missing",
      "code": "REQUIRED_FIELD"
    }
  ],
  "request_id": "req_validation_001"
}

Request Attempted:
POST /api/v2/accounts HTTP/1.1
Content-Type: application/json
X-API-Version: 1.2
{
  "name": "Freelance Studio",
  "user_type": "freelancer",
  "email": "info@freelancestudio.com"
}

New Validation Schema Changes:
1. enum 'user_type': value 'freelancer' no longer accepted
2. field 'metadata': now required (was optional)
3. field 'country_code': must be 2-letter ISO code (was flexible)
4. field 'phone': now requires E.164 format (was any format)

Error ID: VALIDATION_ERR_010
Affected Legacy Clients:
- API v1.2: 8,234 calls/day failing
- Mobile App (v2.1): 3,451 calls/day failing
- Third-party integrations: 2,198 calls/day failing

Total Failures: 13,883 daily API calls
Since: 2026-03-25 (2 days ago)

Migration Required: Update client libraries and request validation""",
        "category": "Application",
        "priority": "2",
        "urgency": "2",
        "impact": "2"
    }
]

# Step 1: Delete existing incidents
print("\n[Step 1] Deleting existing incidents...")
print("-" * 70)

deleted = client.delete_all_incidents(state=["1", "2", "3"])
print(f"✓ Deleted {deleted} existing incidents\n")

# Step 2: Create new API-related incidents with rich data
# Note: Creating ALL incidents in "IT Support" group on purpose, so analyzer can test reassignment
print("[Step 2] Creating fresh batch of detailed API incidents...")
print("-" * 70)
print("ℹ️  All incidents created in 'IT Support' group for testing auto-reassignment\n")

created_incidents = []
for i, inc_data in enumerate(api_incidents, 1):
    print(f"({i}/{len(api_incidents)}) Creating: {inc_data['title']}")
    
    result = client.create_incident(
        title=inc_data["title"],
        description=inc_data["description"],
        category=inc_data["category"],
        priority=inc_data["priority"],
        urgency=inc_data["urgency"],
        impact=inc_data["impact"],
        assignment_group="IT Support"  # Wrong group - for testing reassignment
    )
    
    if result:
        inc_num = result.get("number")
        inc_id = result.get("sys_id")
        created_incidents.append({
            "number": inc_num,
            "title": inc_data["title"],
            "sys_id": inc_id,
            "category": inc_data["category"],
            "priority": inc_data["priority"],
            "assignment_group": "IT Support"
        })
        print(f"  ✓ Created: {inc_num} (assigned to: IT Support)\n")

# Step 3: Summary
print("=" * 70)
print("Setup Complete!")
print("=" * 70)

print(f"\n📊 Summary:")
print(f"  • Deleted: {deleted} incidents")
print(f"  • Created: {len(created_incidents)} detailed API incidents")
print(f"\n🧪 Testing Configuration:")
print(f"  • All incidents created in: 'IT Support' (WRONG GROUP)")
print(f"  • When analyzer runs, it will:")
print(f"    - Analyze incident content")
print(f"    - Determine correct assignment group:")
print(f"      - Database Team (for DB/performance issues)")
print(f"      - Infrastructure Team (for API gateway/network)")
print(f"      - Application Team (for API/webhook/validation issues)")
print(f"      - Security Team (for auth/CORS issues)")
print(f"    - Auto-reassign to correct group (confidence > 70%)")
print(f"  • This tests the re-assignment feature end-to-end")

if created_incidents:
    print(f"\n📋 Created Incidents (All in 'IT Support' group):")
    for inc in created_incidents:
        print(f"  • {inc['number']}: {inc['title']}")
        print(f"    Current: {inc['assignment_group']} | Will be reassigned to: {inc['category']} Team")

print("\n✅ Ready to test! Run 'python3 main.py' to start the analyzer")
print("   Watch it analyze incidents and auto-reassign them to correct groups.")
print("=" * 70)
